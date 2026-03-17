from pathlib import Path

import typer

from backup_drive import onedrive
from backup_drive.auth import get_access_token
from backup_drive.auth import login as auth_login
from backup_drive.download import download_file, download_folder

app = typer.Typer(
    help="Backup files from OneDrive to local storage.", no_args_is_help=True
)


@app.callback()
def callback():
    pass


@app.command()
def login():
    """Authenticate to Microsoft OneDrive via device code flow."""
    auth_login()


@app.command()
def download(
    source: str = typer.Argument(..., help="Path on OneDrive (file or directory)"),
    target: Path = typer.Argument(..., help="Local directory to download into"),
    force: bool = typer.Option(
        False, "--force", "-f", help="Overwrite without prompting"
    ),
):
    """Download a file or directory from OneDrive to a local path."""
    token = get_access_token()

    try:
        item = onedrive.get_item(token, source)
    except onedrive.ItemNotFoundError:
        typer.echo(f"Error: '{source}' not found.")
        raise typer.Exit(1)
    except onedrive.AuthError:
        typer.echo("Auth failed. Run login first.")
        raise typer.Exit(1)
    except onedrive.OneDriveError as e:
        typer.echo(f"Error: {e}")
        raise typer.Exit(1)

    if item.is_folder:
        download_folder(token, item, target, force)
    else:
        download_file(token, item, target, force)
