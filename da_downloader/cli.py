"""Installed command-line entry point for devart-dl.

URL-first is the primary entry: ``devart-dl URL``. The legacy subcommands
(``url``/``artist``/``gallery``/``search``/``fav``) are kept for compatibility
and now route through the same pipeline (no subprocess dispatch).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Optional, Sequence

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
from .targets import DownloadTarget, TargetKind

_HELP = """DeviantArt Downloader

Usage:
  devart-dl URL [options]             # URL-first: artwork/gallery/favourites/tag
  devart-dl url URL [options]
  devart-dl artist USERNAME [options]
  devart-dl gallery USERNAME [GALLERY_ID] [options]
  devart-dl search USERNAME_OR_ALL QUERY [options]
  devart-dl fav USERNAME [FOLDER_ID] [options]
  devart-dl login oauth|interactive
  devart-dl whoami | logout
  devart-dl version

Options (URL-first and subcommands):
  -d, --dest DIR          download root (default ./Downloads)
  --directory TEMPLATE    directory template (default "{author}")
  --filename TEMPLATE     filename template (default "{id}_{title}.{ext}")
  --quality NAME          original|best|preview (default best)
  --archive PATH          SQLite archive to skip already-downloaded
  --cookies PATH          cookie file (otherwise env/session/cookies.txt)
  --write-info-json       write a metadata .json next to each file
  --overwrite             replace existing files
  --proxy URL --timeout S --retries N --limit N

Run `devart-dl login oauth --help` for OAuth details.
"""

_KNOWN_COMMANDS = frozenset(
    {"help", "url", "artist", "gallery", "search", "fav", "login", "whoami", "logout"}
)
_REMOVED_COMMANDS = frozenset({"anti-ban", "test"})
_UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)


def _version() -> str:
    try:
        return version("devart-dl")
    except PackageNotFoundError:
        return "4.0.1"


def _looks_like_target(value: str) -> bool:
    return (
        "://" in value
        or "deviantart.com" in value
        or "fav.me" in value
        or "sta.sh" in value
        or bool(_UUID_RE.match(value))
        or value.isdigit()
    )


def _load_cookies(cookies_path: Optional[str]) -> str:
    if cookies_path:
        path = Path(cookies_path)
        if path.is_file():
            return path.read_text(encoding="utf-8").strip()
        print(f"warning: cookies file not found: {cookies_path}", file=sys.stderr)
        return ""
    return os.environ.get("DEVIANTART_COOKIES", "").strip() or str(
        AuthManager().load_cookies() or ""
    )


def _execute(
    target: str | DownloadTarget,
    *,
    destination: str,
    cookies: str = "",
    archive: Optional[str] = None,
    quality: str = "best",
    overwrite: bool = False,
    write_info_json: bool = False,
    directory: str = "{author}",
    filename: str = "{id}_{title}.{ext}",
    proxy: Optional[str] = None,
    timeout: float = 60.0,
    retries: int = 3,
    limit: int = 24,
    quiet: bool = False,
    verbose: bool = False,
) -> int:
    try:
        downloader = build_downloader(
            destination=Path(destination),
            cookies=cookies,
            archive=Path(archive) if archive else None,
            quality=quality,
            overwrite=overwrite,
            write_info_json=write_info_json,
            directory=directory,
            filename=filename,
            proxy=proxy,
            timeout=timeout,
            retries=retries,
            limit=limit,
        )
        outcomes = downloader.download(target)
    except (ValueError, DeviantArtError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    downloaded = sum(1 for o in outcomes if o.status == "downloaded")
    skipped = sum(1 for o in outcomes if o.status == "skipped")
    failed = sum(1 for o in outcomes if o.status == "failed")
    if not quiet:
        print(f"downloaded: {downloaded}, skipped: {skipped}, failed: {failed}")
        for outcome in outcomes:
            if outcome.status == "downloaded" and outcome.path:
                print(f"  {outcome.path}")
            elif outcome.status == "skipped" and verbose:
                print(f"  - {outcome.item_id} ({outcome.reason})")
            elif outcome.status == "failed":
                print(f"  ! {outcome.item_id}: {outcome.reason}", file=sys.stderr)
    return 0 if failed == 0 else 1


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
    return _execute(
        args.target,
        destination=args.dest,
        cookies=_load_cookies(args.cookies),
        archive=args.archive,
        quality=args.quality,
        overwrite=args.overwrite,
        write_info_json=args.write_info_json,
        directory=args.directory,
        filename=args.filename,
        proxy=args.proxy,
        timeout=args.timeout,
        retries=args.retries,
        limit=args.limit,
        quiet=args.quiet,
        verbose=args.verbose,
    )


def _run_subcommand(command: str, rest: Sequence[str]) -> int:
    positionals: list[str] = []
    options: dict[str, str] = {}
    for arg in rest:
        if arg.startswith("--"):
            if "=" in arg:
                key, value = arg.split("=", 1)
                options[key] = value
            else:
                options[arg] = "1"
        else:
            positionals.append(arg)

    if command == "url":
        if not positionals:
            print("Usage: devart-dl url URL", file=sys.stderr)
            return 64
        target: str | DownloadTarget = positionals[0]
    else:
        if not positionals:
            print(f"Usage: devart-dl {command} ...", file=sys.stderr)
            return 64
        username = positionals[0]
        if command == "artist":
            target = DownloadTarget(TargetKind.USER, username=username)
        elif command == "gallery":
            folder = positionals[1] if len(positionals) > 1 else None
            kind = TargetKind.GALLERY_FOLDER if folder else TargetKind.GALLERY
            target = DownloadTarget(kind, username=username, identifier=folder)
        elif command == "search":
            query = positionals[1] if len(positionals) > 1 else ""
            target = DownloadTarget(TargetKind.SEARCH, username=username, query=query)
        elif command == "fav":
            folder = positionals[1] if len(positionals) > 1 else None
            kind = TargetKind.FAVORITES_FOLDER if folder else TargetKind.FAVORITES
            target = DownloadTarget(kind, username=username, identifier=folder)
        else:
            print(f"Unknown command: {command}", file=sys.stderr)
            return 64

    separate = options.get("--separate", "1") not in ("0", "false", "no")
    overwrite = options.get("--replace") in ("1", "true", "yes")
    try:
        return _execute(
            target,
            destination=options.get("--dest", "./Downloads"),
            cookies=_load_cookies(options.get("--cookies")),
            archive=options.get("--archive"),
            quality=options.get("--quality", "best"),
            overwrite=overwrite,
            write_info_json=options.get("--write-info-json") == "1",
            directory="{author}" if separate else "",
            filename=options.get("--filename", "{id}_{title}.{ext}"),
            proxy=options.get("--proxy"),
            timeout=float(options.get("--timeout", "60")),
            retries=int(options.get("--retries", "3")),
            limit=int(options.get("--limit", "24")),
            quiet=options.get("--quiet") == "1",
            verbose=options.get("--verbose") == "1",
        )
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 64


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
            "deviantart.com/developers, or set DEVIANTART_CLIENT_ID). "
            "See docs/LOGIN.md for step-by-step instructions.",
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


def _login_interactive(arguments: Sequence[str]) -> int:
    print("Paste your DeviantArt cookie (F12 → Application → Cookies → copy auth & auth_secure):")
    cookies = input().strip()
    if not cookies:
        print("error: empty cookie", file=sys.stderr)
        return 1
    path = Path.home() / ".deviantart_dl" / "session.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {"cookies": cookies, "saved_at": datetime.now().isoformat(), "method": "input"},
            indent=2,
        ),
        encoding="utf-8",
    )
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass
    print(f"saved session to {path}")
    return 0


def _oauth_whoami(arguments: Sequence[str]) -> int:
    session = OAuthSession.from_store()
    if session is None:
        print(
            "not logged in via OAuth — run `devart-dl login oauth --client-id ID` "
            "(see docs/LOGIN.md)",
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


def _login_clear(arguments: Sequence[str]) -> int:
    OAuthTokenStore().clear()
    session = Path.home() / ".deviantart_dl" / "session.json"
    try:
        session.unlink(missing_ok=True)
    except OSError:
        pass
    print("cleared saved login sessions")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
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
        print(_HELP)
        return 0
    if command in {"url", "artist", "gallery", "search", "fav"}:
        return _run_subcommand(command, rest)
    if command == "login":
        if not rest or rest[0] in {"-h", "--help", "help"}:
            print("Usage: devart-dl login oauth|interactive|clear")
            print("  oauth        log in via the official API (recommended)")
            print("  interactive  paste a cookie (fallback)")
            print("  clear        clear saved login sessions")
            return 0
        login_command, *login_args = rest
        if login_command == "oauth":
            return _oauth_login(login_args)
        if login_command == "interactive":
            return _login_interactive(login_args)
        if login_command == "clear":
            return _login_clear(login_args)
        print(f"Unknown login method: {login_command}", file=sys.stderr)
        return 64
    if command == "whoami":
        return _oauth_whoami(rest)
    if command == "logout":
        return _oauth_logout(rest)
    if command in _REMOVED_COMMANDS:
        print(
            f"`devart-dl {command}` was removed in v4.0.0 — use `devart-dl URL` instead.",
            file=sys.stderr,
        )
        return 64

    print(f"Unknown command: {command}\n\n{_HELP}", file=sys.stderr)
    return 64


if __name__ == "__main__":
    raise SystemExit(main())
