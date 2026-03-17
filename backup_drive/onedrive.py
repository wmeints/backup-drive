from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional
from urllib.parse import quote

import requests

GRAPH_BASE = "https://graph.microsoft.com/v1.0"
CHUNK_SIZE = 1024 * 1024  # 1 MB


class OneDriveError(Exception):
    pass


class ItemNotFoundError(OneDriveError):
    pass


class AuthError(OneDriveError):
    pass


@dataclass
class DriveItem:
    id: str
    name: str
    size: int
    is_folder: bool
    download_url: Optional[str]


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def get_root(token: str) -> DriveItem:
    url = f"{GRAPH_BASE}/me/drive/root"
    resp = requests.get(url, headers=_auth_headers(token))
    if resp.status_code == 401:
        raise AuthError("Authentication failed")
    if not resp.ok:
        raise OneDriveError(f"Graph API error {resp.status_code}: {resp.text}")
    data = resp.json()
    return DriveItem(
        id=data["id"],
        name=data["name"],
        size=data.get("size", 0),
        is_folder=True,
        download_url=None,
    )


def get_item(token: str, path: str) -> DriveItem:
    encoded = quote(path, safe="/")
    url = f"{GRAPH_BASE}/me/drive/root:/{encoded}"
    resp = requests.get(url, headers=_auth_headers(token))
    if resp.status_code == 404:
        raise ItemNotFoundError(f"'{path}' not found on OneDrive")
    if resp.status_code == 401:
        raise AuthError("Authentication failed")
    if not resp.ok:
        raise OneDriveError(f"Graph API error {resp.status_code}: {resp.text}")
    data = resp.json()
    return DriveItem(
        id=data["id"],
        name=data["name"],
        size=data.get("size", 0),
        is_folder="folder" in data,
        download_url=data.get("@microsoft.graph.downloadUrl"),
    )


def list_children(token: str, folder_id: str) -> list[DriveItem]:
    url = f"{GRAPH_BASE}/me/drive/items/{folder_id}/children"
    items = []
    while url:
        resp = requests.get(url, headers=_auth_headers(token))
        if resp.status_code == 401:
            raise AuthError("Authentication failed")
        if not resp.ok:
            raise OneDriveError(f"Graph API error {resp.status_code}: {resp.text}")
        data = resp.json()
        for item in data.get("value", []):
            items.append(DriveItem(
                id=item["id"],
                name=item["name"],
                size=item.get("size", 0),
                is_folder="folder" in item,
                download_url=item.get("@microsoft.graph.downloadUrl"),
            ))
        url = data.get("@odata.nextLink")
    return items


def get_item_by_id(token: str, item_id: str) -> DriveItem:
    url = f"{GRAPH_BASE}/me/drive/items/{item_id}"
    resp = requests.get(url, headers=_auth_headers(token))
    if resp.status_code == 404:
        raise ItemNotFoundError(f"Item '{item_id}' not found on OneDrive")
    if resp.status_code == 401:
        raise AuthError("Authentication failed")
    if not resp.ok:
        raise OneDriveError(f"Graph API error {resp.status_code}: {resp.text}")
    data = resp.json()
    return DriveItem(
        id=data["id"],
        name=data["name"],
        size=data.get("size", 0),
        is_folder="folder" in data,
        download_url=data.get("@microsoft.graph.downloadUrl"),
    )


def download_file(
    download_url: str,
    dest_path,
    progress_callback: Callable[[int], None],
) -> None:
    dest_path = Path(dest_path)
    tmp_path = dest_path.with_suffix(dest_path.suffix + ".tmp")
    try:
        with requests.get(download_url, stream=True) as resp:
            if resp.status_code == 401:
                raise AuthError("Authentication failed")
            resp.raise_for_status()
            with open(tmp_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=CHUNK_SIZE):
                    if chunk:
                        f.write(chunk)
                        progress_callback(len(chunk))
        tmp_path.replace(dest_path)
    except:
        tmp_path.unlink(missing_ok=True)
        raise
