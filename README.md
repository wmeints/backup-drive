# backup-drive

A command-line utility to download files and directories from OneDrive to local storage. Uses the Microsoft Graph API with device code authentication — no browser required on headless machines.

## Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) package manager
- An Azure app registration (see below)

---

## Setting up an Azure app registration

The tool authenticates as a registered application in Azure AD using the device code flow. You only need a personal Microsoft account (the same one you use for OneDrive).

1. Go to the [Azure portal](https://portal.azure.com) and sign in with your Microsoft account.

2. Navigate to **Azure Active Directory** → **App registrations** → **New registration**.

3. Fill in the form:
   - **Name**: anything descriptive, e.g. `backup-drive`
   - **Supported account types**: select **Personal Microsoft accounts only**
   - **Redirect URI**: leave blank

4. Click **Register**. Copy the **Application (client) ID** — you will need it later.

5. In the app's left sidebar, go to **Authentication**:
   - Under **Advanced settings**, set **Allow public client flows** to **Yes**.
   - Click **Save**.

6. Go to **API permissions** → **Add a permission** → **Microsoft Graph** → **Delegated permissions**.
   Add the following permissions:
   - `Files.Read`
   - `offline_access`

7. Click **Add permissions**. No admin consent is required for these delegated permissions on personal accounts.

---

## Installation

Clone the repository and install dependencies with uv:

```bash
git clone <repo-url>
cd backup-drive
uv sync
```

Set the client ID from your app registration as an environment variable. Add this to your shell profile (e.g. `~/.bashrc` or `~/.zshrc`) to make it permanent:

```bash
export BACKUP_DRIVE_CLIENT_ID="your-client-id-here"
```

---

## Usage

### Log in

Authenticate to OneDrive before downloading anything. The tool uses device code flow — it will print a URL and a code you enter in a browser:

```bash
uv run backup-drive login
```

Follow the on-screen instructions. Once authenticated, credentials are cached at `~/.config/backup-drive/token_cache.json` and reused automatically on subsequent runs. You only need to log in again if the session expires.

### Download a file

```bash
uv run backup-drive download "Documents/report.pdf" ~/Downloads
```

This downloads `report.pdf` into `~/Downloads/report.pdf`. If the file already exists locally, you will be prompted to confirm overwriting it.

To overwrite without prompting, use `--force`:

```bash
uv run backup-drive download "Documents/report.pdf" ~/Downloads --force
```

### Download a directory

Provide a folder path on OneDrive and the tool will recursively download all its contents:

```bash
uv run backup-drive download "Documents/Projects" ~/Backup
```

The folder is created under the target directory, so the above example produces `~/Backup/Projects/`.

### Get help

```bash
uv run backup-drive --help
uv run backup-drive download --help
```

---

## Development

### Install dependencies

```bash
uv sync
```

### Project layout

```
backup_drive/
  auth.py          # MSAL authentication, token cache
  onedrive.py      # Microsoft Graph API calls
  cli/
    __init__.py    # Typer app and CLI commands
pyproject.toml
```

### Running tests

```bash
uv run pytest
```

Run a single test:

```bash
uv run pytest tests/test_foo.py::test_bar
```

### Adding dependencies

```bash
uv add <package>
```

### Environment variables

| Variable | Required | Description |
|---|---|---|
| `BACKUP_DRIVE_CLIENT_ID` | Yes | Azure AD app registration client ID |

### Token cache

Tokens are persisted to `~/.config/backup-drive/token_cache.json` with mode `0600` (owner read/write only). Delete this file to force a fresh login.
