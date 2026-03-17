from collections import deque
from pathlib import Path

import typer
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)

from backup_drive import onedrive


def download_file(
    token: str,
    item: onedrive.DriveItem,
    target_dir: Path,
    force: bool,
    quiet: bool = False,
) -> None:
    target_dir.mkdir(parents=True, exist_ok=True)
    dest = target_dir / item.name

    if dest.exists():
        if quiet or (not force and not typer.confirm(f"'{dest}' already exists. Overwrite?")):
            typer.echo(f"Skipped '{item.name}'.")
            return

    with Progress(
        TextColumn("[bold blue]{task.fields[filename]}", justify="right"),
        BarColumn(),
        DownloadColumn(),
        TransferSpeedColumn(),
        TimeRemainingColumn(),
    ) as progress:
        task = progress.add_task("download", filename=item.name, total=item.size)
        if item.download_url is None:
            raise ValueError(f"Item '{item.name}' has no download URL")
        onedrive.download_file(
            item.download_url, dest, lambda n: progress.advance(task, n)
        )


def download_folder(
    token: str,
    root_item: onedrive.DriveItem,
    target: Path,
    force: bool,
    quiet: bool = False,
) -> None:
    queue = deque([(root_item, target / root_item.name)])
    while queue:
        folder, local_dir = queue.popleft()
        children = onedrive.list_children(token, folder.id)
        for child in children:
            if child.is_folder:
                queue.append((child, local_dir / child.name))
            else:
                download_file(token, child, local_dir, force, quiet)
