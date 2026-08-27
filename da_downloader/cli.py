"""Installed command-line entry point for devart-dl."""

from __future__ import annotations

import subprocess
import sys
from importlib.metadata import PackageNotFoundError, version
from typing import Sequence


_HELP = """DeviantArt Downloader

Usage:
  devart-dl url URL [options]
  devart-dl artist USERNAME_OR_URL [options]
  devart-dl gallery USERNAME [GALLERY_ID] [options]
  devart-dl search USERNAME_OR_ALL QUERY [options]
  devart-dl fav USERNAME FOLDER_ID [options]
  devart-dl login [interactive|browser|validate|clear]
  devart-dl anti-ban
  devart-dl version

Run `devart-dl help COMMAND` for command-specific help.
"""


def _version() -> str:
    try:
        return version("devart-dl")
    except PackageNotFoundError:
        return "3.3.1"


def _run_module(module: str, arguments: Sequence[str]) -> int:
    """Run a packaged command module with the active Python interpreter."""
    return subprocess.run(
        [sys.executable, "-m", module, *arguments],
        check=False,
    ).returncode


def _command_help(command: str) -> int:
    modules = {
        "url": "tools.download_url",
        "artist": "tools.download_artist",
        "gallery": "legacy.main",
        "search": "legacy.main",
        "fav": "legacy.main",
        "login": "tools.auth_manager",
        "anti-ban": "tools.anti_ban_config",
    }
    module = modules.get(command)
    if module is None:
        print(f"Unknown command: {command}", file=sys.stderr)
        return 64
    args = ["help"] if module == "legacy.main" else ["--help"]
    return _run_module(module, args)


def main(argv: Sequence[str] | None = None) -> int:
    """Dispatch the public CLI without relying on source-tree-relative files."""
    arguments = list(sys.argv[1:] if argv is None else argv)
    if not arguments or arguments[0] in {"-h", "--help"}:
        print(_HELP)
        return 0
    if arguments[0] in {"-V", "--version", "version"}:
        print(f"devart-dl {_version()}")
        return 0

    command, *rest = arguments
    if command == "help":
        if not rest:
            print(_HELP)
            return 0
        return _command_help(rest[0])
    if command == "url":
        return _run_module("tools.download_url", rest or ["--help"])
    if command == "artist":
        return _run_module("tools.download_artist", rest or ["--help"])
    if command in {"gallery", "search", "fav"}:
        return _run_module("legacy.main", [command, *rest])
    if command == "login":
        if not rest or rest[0] in {"-h", "--help", "help"}:
            return _run_module("tools.auth_manager", ["--help"])
        login_command, *login_args = rest
        if login_command == "clear":
            return _run_module("tools.auth_manager", ["--clear-session"])
        if login_command == "interactive":
            return _run_module("tools.auth_manager", ["--method=input", *login_args])
        if login_command == "browser":
            return _run_module("tools.browser_login", login_args)
        if login_command in {"validate", "verify", "check", "test"}:
            return _run_module("tools.validate_cookies", login_args)
        return _run_module("tools.auth_manager", rest)
    if command == "anti-ban":
        return _run_module("tools.anti_ban_config", rest)
    if command == "test":
        if not rest:
            print("Usage: devart-dl test USERNAME", file=sys.stderr)
            return 64
        return _run_module(
            "legacy.main", ["gallery", rest[0], "--limit=1", "--ask=1"]
        )

    print(f"Unknown command: {command}\n\n{_HELP}", file=sys.stderr)
    return 64


if __name__ == "__main__":
    raise SystemExit(main())
