import os
from pathlib import Path

import msal
import typer

SCOPES = ["Files.Read"]
AUTHORITY = "https://login.microsoftonline.com/consumers"


def get_cache_path() -> Path:
    path = Path.home() / ".config" / "backup-drive" / "token_cache.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def load_token_cache() -> msal.SerializableTokenCache:
    cache = msal.SerializableTokenCache()
    cache_path = get_cache_path()
    if cache_path.exists():
        cache.deserialize(cache_path.read_text())
    return cache


def save_token_cache(cache: msal.SerializableTokenCache) -> None:
    if cache.has_state_changed:
        cache_path = get_cache_path()
        cache_path.write_text(cache.serialize())
        cache_path.chmod(0o600)


def get_client_id() -> str:
    client_id = os.environ.get("BACKUP_DRIVE_CLIENT_ID")
    if not client_id:
        typer.echo("Error: BACKUP_DRIVE_CLIENT_ID environment variable is not set.")
        raise typer.Exit(code=1)
    return client_id


def login() -> None:
    client_id = get_client_id()
    cache = load_token_cache()

    msal_app = msal.PublicClientApplication(
        client_id, authority=AUTHORITY, token_cache=cache
    )

    accounts = msal_app.get_accounts()
    if accounts:
        result = msal_app.acquire_token_silent(SCOPES, account=accounts[0])
        if result and "access_token" in result:
            save_token_cache(cache)
            typer.echo("Already logged in. Token refreshed if needed.")
            return

    flow = msal_app.initiate_device_flow(scopes=SCOPES)
    if "user_code" not in flow:
        typer.echo(
            f"Error initiating device flow: {flow.get('error_description', 'unknown error')}"
        )
        raise typer.Exit(code=1)

    typer.echo(flow["message"])

    result = msal_app.acquire_token_by_device_flow(flow)

    if "access_token" in result:
        save_token_cache(cache)
        typer.echo("Login successful. Credentials stored.")
    else:
        typer.echo(
            f"Login failed: {result.get('error')}: {result.get('error_description')}"
        )
        raise typer.Exit(code=1)


def get_access_token() -> str:
    client_id = get_client_id()
    cache = load_token_cache()

    msal_app = msal.PublicClientApplication(
        client_id, authority=AUTHORITY, token_cache=cache
    )

    accounts = msal_app.get_accounts()
    if not accounts:
        typer.echo("Not logged in. Run `backup-drive login` first.")
        raise typer.Exit(code=1)

    result = msal_app.acquire_token_silent(SCOPES, account=accounts[0])
    if not result or "access_token" not in result:
        typer.echo("Session expired. Run `backup-drive login` first.")
        raise typer.Exit(code=1)

    save_token_cache(cache)
    return result["access_token"]
