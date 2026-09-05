"""Installed command-line entry point for devart-dl."""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Sequence

from .auth import AuthManager
from .download import build_downloader
from .errors import DeviantArtError
from .oauth import (
    OAuthConfig,
    OAuthError,
    OAuthSession,
    OAuthTokenClient,
    OAuthTokenStore,
    login as oauth_login,
)
from .official_api import OfficialApiClient

_HELP = """DeviantArt Downloader

Usage:
  devart-dl URL [options]             # URL-first: artwork/gallery/favourites/tag
  devart-dl url URL [options]
  devart-dl artist USERNAME_OR_URL [options]
  devart-dl gallery USERNAME [GALLERY_ID] [options]
  devart-dl search USERNAME_OR_ALL QUERY [options]
  devart-dl fav USERNAME FOLDER_ID [options]
  devart-dl login [interactive|browser|validate|clear]
  devart-dl anti-ban
  devart-dl version

URL-first options:
  -d, --dest DIR          download root (default ./Downloads)
  --directory TEMPLATE    directory template (default "{author}")
  --filename TEMPLATE     filename template (default "{id}_{title}.{ext}")
  --quality NAME          original|best|preview (default best)
  --archive PATH          SQLite archive for skip-already-downloaded
  --cookies PATH          cookies file (falls back to saved session)
  --write-info-json       write a metadata .json next to each file
  --overwrite             replace existing files

Run `devart-dl help COMMAND` for command-specific help.
"""

_KNOWN_COMMANDS = frozenset(
    {
        "help",
        "url",
        "artist",
        "gallery",
        "search",
        "fav",
        "login",
        "anti-ban",
        "test",
        "whoami",
        "logout",
    }
)
_UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)


def _version() -> str:
    try:
        return version("devart-dl")
    except PackageNotFoundError:
        return "3.4.0"


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


def _looks_like_target(value: str) -> bool:
    return (
        "://" in value
        or "deviantart.com" in value
        or "fav.me" in value
        or "sta.sh" in value
        or bool(_UUID_RE.match(value))
        or value.isdigit()
    )


def _load_cookies(cookies_path: str | None) -> str:
    if cookies_path:
        path = Path(cookies_path)
        if path.is_file():
            return path.read_text(encoding="utf-8").strip()
        print(f"warning: cookies file not found: {cookies_path}", file=sys.stderr)
        return ""
    return str(AuthManager().load_cookies() or "")


def _run_download(arguments: Sequence[str]) -> int:
    parser = argparse.ArgumentParser(prog="devart-dl", description="Download a DeviantArt URL")
    parser.add_argument("target", help="DeviantArt URL or artwork id")
    parser.add_argument("-d", "--dest", "--destination", default="./Downloads")
    parser.add_argument("--directory", default="{author}")
    parser.add_argument("--filename", default="{id}_{title}.{ext}")
    parser.add_argument("--quality", default="best")
    parser.add_argument("--archive", default=None)
    parser.add_argument("--cookies", default=None)
    parser.add_argument("--proxy", default=None)
    parser.add_argument("--timeout", type=float, default=60.0)
    parser.add_argument("--retries", type=int, default=3)
    parser.add_argument("--limit", type=int, default=24)
    parser.add_argument("--write-info-json", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument("-q", "--quiet", action="store_true")
    args = parser.parse_args(list(arguments))

    try:
        downloader = build_downloader(
            destination=Path(args.dest),
            cookies=_load_cookies(args.cookies),
            archive=Path(args.archive) if args.archive else None,
            quality=args.quality,
            overwrite=args.overwrite,
            write_info_json=args.write_info_json,
            directory=args.directory,
            filename=args.filename,
            proxy=args.proxy,
            timeout=args.timeout,
            retries=args.retries,
            limit=args.limit,
        )
        outcomes = downloader.download(args.target)
    except (ValueError, DeviantArtError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    downloaded = sum(1 for o in outcomes if o.status == "downloaded")
    skipped = sum(1 for o in outcomes if o.status == "skipped")
    failed = sum(1 for o in outcomes if o.status == "failed")
    if not args.quiet:
        print(f"downloaded: {downloaded}, skipped: {skipped}, failed: {failed}")
        for outcome in outcomes:
            if outcome.status == "downloaded" and outcome.path:
                print(f"  {outcome.path}")
            elif outcome.status == "skipped" and args.verbose:
                print(f"  - {outcome.item_id} ({outcome.reason})")
            elif outcome.status == "failed":
                print(f"  ! {outcome.item_id}: {outcome.reason}", file=sys.stderr)
    return 0 if failed == 0 else 1


def _oauth_login(arguments: Sequence[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="devart-dl login oauth", description="Log in via the official API (OAuth + PKCE)"
    )
    parser.add_argument(
        "--client-id",
        default=os.environ.get("DEVIANTART_CLIENT_ID") or os.environ.get("DA_CLIENT_ID"),
    )
    parser.add_argument("--no-open", action="store_true")
    parser.add_argument("--manual", action="store_true")
    args = parser.parse_args(list(arguments))
    if not args.client_id:
        print(
            "error: --client-id is required (register a Public OAuth app at "
            "deviantart.com/developers, or set DEVIANTART_CLIENT_ID)",
            file=sys.stderr,
        )
        return 64
    try:
        oauth_login(OAuthConfig(args.client_id), no_open=args.no_open, manual=args.manual)
    except OAuthError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print("logged in via OAuth")
    return 0


def _oauth_whoami(arguments: Sequence[str]) -> int:
    session = OAuthSession.from_store()
    if session is None:
        print(
            "not logged in via OAuth — run `devart-dl login oauth --client-id ID`",
            file=sys.stderr,
        )
        return 1
    try:
        data = OfficialApiClient(session).whoami()
    except (OAuthError, DeviantArtError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"username: {data.get('username')}")
    return 0


def _oauth_logout(arguments: Sequence[str]) -> int:
    local_only = "--local" in arguments
    store = OAuthTokenStore()
    session = OAuthSession.from_store()
    if session is not None and not local_only:
        try:
            OAuthTokenClient().revoke(session.config, session.tokens)
        except OAuthError as exc:
            print(f"warning: could not revoke remote token: {exc}", file=sys.stderr)
    store.clear()
    print("logged out")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Dispatch the public CLI without relying on source-tree-relative files."""
    arguments = list(sys.argv[1:] if argv is None else argv)
    if not arguments or arguments[0] in {"-h", "--help"}:
        print(_HELP)
        return 0
    if arguments[0] in {"-V", "--version", "version"}:
        print(f"devart-dl {_version()}")
        return 0

    # URL-first: anything that isn't a known command but looks like a URL/id.
    if arguments[0] not in _KNOWN_COMMANDS and _looks_like_target(arguments[0]):
        return _run_download(arguments)

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
        if login_command == "oauth":
            return _oauth_login(login_args)
        if login_command == "clear":
            return _run_module("tools.auth_manager", ["--clear-session"])
        if login_command == "interactive":
            return _run_module("tools.auth_manager", ["--method=input", *login_args])
        if login_command == "browser":
            return _run_module("tools.browser_login", login_args)
        if login_command in {"validate", "verify", "check", "test"}:
            return _run_module("tools.validate_cookies", login_args)
        return _run_module("tools.auth_manager", rest)
    if command == "whoami":
        return _oauth_whoami(rest)
    if command == "logout":
        return _oauth_logout(rest)
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
