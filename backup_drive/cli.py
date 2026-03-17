from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from backup_drive import onedrive
from backup_drive.auth import get_access_token
from backup_drive.auth import login as auth_login
from backup_drive.download import download_file, download_folder

app = typer.Typer(
    help="Backup files from OneDrive to local storage.", no_args_is_help=True
)


def _format_size(size: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


@app.callback()
def callback():
    pass


@app.command()
def ls(
    path: str = typer.Argument(None, help="Path on OneDrive to list (default: root)"),
):
    """List files and directories on OneDrive."""
    token = get_access_token()

    try:
        if path:
            item = onedrive.get_item(token, path)
            if not item.is_folder:
                typer.echo(f"Error: '{path}' is not a directory.")
                raise typer.Exit(1)
        else:
            item = onedrive.get_root(token)
    except onedrive.ItemNotFoundError:
        typer.echo(f"Error: '{path}' not found.")
        raise typer.Exit(1)
    except onedrive.AuthError:
        typer.echo("Auth failed. Run login first.")
        raise typer.Exit(1)
    except onedrive.OneDriveError as e:
        typer.echo(f"Error: {e}")
        raise typer.Exit(1)

    children = onedrive.list_children(token, item.id)

    table = Table(show_header=True, box=None, pad_edge=False)
    table.add_column("", width=2)
    table.add_column("Name")
    table.add_column("Size", justify="right")

    for child in children:
        if child.is_folder:
            table.add_row("[blue]\uf07b[/blue]", child.name, "-")
        else:
            table.add_row("[green]\uf15b[/green]", child.name, _format_size(child.size))

    Console().print(table)


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
    quiet: bool = typer.Option(
        False, "--quiet", "-q", help="Skip files that already exist locally"
    ),
):
    """Download a file or directory from OneDrive to a local path."""
    if force and quiet:
        typer.echo("Error: --force and --quiet are mutually exclusive.")
        raise typer.Exit(1)

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
        download_folder(token, item, target, force, quiet)
    else:
        download_file(token, item, target, force, quiet)
