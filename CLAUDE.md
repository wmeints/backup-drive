# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Purpose

A command-line utility to download directories from a OneDrive account to a local target location. Built with Python 3.13 and [Typer](https://typer.tiangolo.com/) for the CLI interface.

## Commands

This project uses [uv](https://docs.astral.sh/uv/) for dependency management.

```bash
# Install dependencies
uv sync

# Run the CLI
uv run backup-drive

# Add a dependency
uv add <package>

# Run tests
uv run pytest

# Run a single test
uv run pytest tests/test_foo.py::test_bar
```

## Architecture

- `backup_drive/cli/__init__.py` — Typer app and CLI commands
- `backup_drive/auth.py` — MSAL authentication logic, token cache I/O, and `get_access_token()` helper
- `pyproject.toml` — project metadata and dependencies (managed by uv)

The CLI is built with Typer. OneDrive access uses the Microsoft Graph API via `msal` for authentication and `httpx` or `requests` for API calls.

### Environment variables

| Variable | Required | Description |
|---|---|---|
| `BACKUP_DRIVE_CLIENT_ID` | Yes | Azure AD app registration client ID with `Files.Read` and `offline_access` delegated permissions and public client (device code) flow enabled |

### Token cache

Tokens are persisted to `~/.config/backup-drive/token_cache.json` (mode `0600`). Future commands import `from auth import get_access_token` and use the token as a `Bearer` header against the Graph API.
