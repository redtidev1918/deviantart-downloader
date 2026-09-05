"""High-level Downloader facade and factory: parse → resolve → download.

This is the public library entry point: build a wired pipeline from plain
configuration values, then call ``download(url)`` with a URL or bare id.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import requests

from .api import DeviantArtAPI
from .archive import DownloadArchive
from .http import HttpDownloader
from .manager import DownloadManager, DownloadOutcome
from .oauth import OAuthSession
from .official_api import OfficialApiClient
from .path import PathFormatter
from .provider import DeviantArtProvider, OfficialProvider, WebProvider
from .targets import DownloadTarget, TargetParser

# User-facing quality names (new) and the legacy o/f/p shorthand.
_QUALITY = {
    "original": "o",
    "best": "f",
    "preview": "p",
    "o": "o",
    "f": "f",
    "p": "p",
}


def normalize_quality(value: str) -> str:
    quality = (value or "best").lower()
    if quality in _QUALITY:
        return _QUALITY[quality]
    raise ValueError(f"invalid quality {value!r} (use original/best/preview or o/f/p)")


class Downloader:
    """High-level entry point: parse a target, resolve items, download them."""

    def __init__(self, provider: DeviantArtProvider, manager: DownloadManager) -> None:
        self.provider = provider
        self.manager = manager

    def download(self, target: str | DownloadTarget) -> list[DownloadOutcome]:
        parsed = TargetParser.parse(target) if isinstance(target, str) else target
        return [self.manager.run(item) for item in self.provider.resolve(parsed)]


def build_downloader(
    *,
    destination: Path,
    cookies: str = "",
    archive: Optional[Path] = None,
    quality: str = "best",
    overwrite: bool = False,
    write_info_json: bool = False,
    directory: str = "{author}",
    filename: str = "{id}_{title}.{ext}",
    proxy: Optional[str] = None,
    timeout: float = 60.0,
    retries: int = 3,
    retry_delay: float = 3.0,
    limit: int = 24,
) -> Downloader:
    """Assemble a wired ``Downloader`` from plain configuration values.

    When an OAuth session exists it is preferred (official API); otherwise the
    cookie-based web provider is used as the fallback.
    """
    normalized_quality = normalize_quality(quality)
    proxies = {"http": proxy, "https": proxy} if proxy else {}

    oauth_session = OAuthSession.from_store()
    if oauth_session is not None:
        client = OfficialApiClient(oauth_session, timeout=timeout)
        provider: DeviantArtProvider = OfficialProvider(
            client, quality=normalized_quality, limit=limit
        )
        # Official media URLs are signed CDN links and need no cookies.
        http_session = requests.Session()
        if proxies:
            http_session.proxies.update(proxies)
    else:
        headers = {
            "accept": "application/json, text/plain, */*",
            "user-agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
            ),
        }
        if cookies:
            headers["cookie"] = cookies
        api = DeviantArtAPI(
            headers, proxies, retry_delay=int(retry_delay), max_retries=retries
        )
        provider = WebProvider(api, quality=normalized_quality, limit=limit)
        http_session = api.session

    http = HttpDownloader(
        session=http_session,
        max_retries=retries,
        retry_backoff=retry_delay,
        timeout=timeout,
    )
    formatter = PathFormatter(destination, directory=directory, filename=filename)
    archive_obj = DownloadArchive(archive) if archive else None
    manager = DownloadManager(
        downloader=http,
        formatter=formatter,
        archive=archive_obj,
        overwrite=overwrite,
        write_info_json=write_info_json,
    )
    return Downloader(provider, manager)


__all__ = ["Downloader", "build_downloader", "normalize_quality"]
