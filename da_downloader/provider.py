"""Provider layer: turn a ``DownloadTarget`` into a stream of ``DownloadItem``.

The provider is the only place that understands DeviantArt endpoints, CSRF,
pagination, and media-URL resolution. Everything downstream (DownloadManager,
HttpDownloader) works only with the ``DownloadItem`` contract.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Callable, Iterator, Optional, Protocol

from .api import ActionType, DeviantArtAPI
from .errors import MediaUnavailableError, ParseError
from .models import Deviation, DownloadItem
from .official_api import (
    OfficialApiClient,
    additional_media_urls,
    deviation_init,
    deviation_uuid,
)
from .targets import DownloadTarget, TargetKind

logger = logging.getLogger(__name__)


class DeviantArtProvider(Protocol):
    """Resolves a DownloadTarget into the DownloadItems to fetch."""

    def resolve(self, target: DownloadTarget) -> Iterator[DownloadItem]:
        ...


class WebProvider:
    """Cookie-based provider for list targets (gallery/search/favorites).

    Uses the website's private ``_puppy`` endpoints via the existing
    ``DeviantArtAPI``. Single-artwork and tag targets are the official API's
    job and are not handled here.
    """

    def __init__(
        self, api: DeviantArtAPI, quality: str = "f", limit: int = 24
    ) -> None:
        self.api = api
        self.quality = quality
        self.limit = limit

    def resolve(self, target: DownloadTarget) -> Iterator[DownloadItem]:
        kind = target.kind
        if kind == TargetKind.ARTWORK:
            raise MediaUnavailableError(
                "single-artwork download requires the official API; "
                "run `devart-dl login oauth` to enable it"
            )
        if kind == TargetKind.TAG:
            raise MediaUnavailableError(
                "tag browsing requires the official API; "
                "run `devart-dl login oauth` to enable it"
            )

        username = target.username or ""
        if kind in (TargetKind.USER, TargetKind.GALLERY):
            action, query, folder = ActionType.GALLERY, None, None
        elif kind == TargetKind.GALLERY_FOLDER:
            action, query, folder = ActionType.GALLERY, None, target.identifier
        elif kind == TargetKind.FAVORITES:
            action, query, folder = ActionType.FAVORITE, None, None
        elif kind == TargetKind.FAVORITES_FOLDER:
            action, query, folder = ActionType.FAVORITE, None, target.identifier
        elif kind == TargetKind.SEARCH:
            action, query, folder = ActionType.SEARCH, target.query or "", None
            username = username or "all"  # empty → global search
        else:
            raise MediaUnavailableError(f"unsupported target kind: {kind}")

        yield from self._resolve_list(action, username, query, folder)

    def _resolve_list(
        self,
        action: ActionType,
        username: str,
        query: Optional[str],
        folder: Optional[str],
    ) -> Iterator[DownloadItem]:
        csrf_username = "" if (action == ActionType.SEARCH and username == "all") else username
        if not self.api.get_csrf_token(csrf_username):
            raise ParseError(f"could not obtain a CSRF token for '{csrf_username}'")

        url = self.api.build_api_url(action, username, query=query, folder_id=folder)
        url = url.replace("<LIMIT>", str(self.limit))

        offset = 0
        cursor = ""
        seen_pages: set[tuple[int, str]] = set()
        while True:
            page_key = (offset, cursor)
            if page_key in seen_pages:
                raise ParseError(
                    f"pagination did not advance (offset={offset}, cursor={cursor!r})"
                )
            seen_pages.add(page_key)

            deviations, has_more, offset, cursor = self.api.fetch_deviations(
                url, offset, cursor
            )
            for deviation in deviations:
                item = self._to_item(deviation)
                if item is not None:
                    yield item
            if not has_more:
                break

    def _to_item(self, deviation: Deviation) -> Optional[DownloadItem]:
        media_url = self.api.get_download_url(deviation, self.quality)
        if media_url is None and self.quality == "o":
            media_url = self.api.get_download_url(deviation, "f")
        if media_url is None:
            logger.warning("no media URL for %r; skipping", deviation.title)
            return None
        return DownloadItem(
            artwork_id=deviation.deviation_id,
            url=deviation.url,
            title=deviation.title,
            author=deviation.author,
            media_url=media_url,
            extension=_extension(deviation, media_url),
            mature=deviation.is_mature,
            metadata={"quality": self.quality},
        )


def _extension(deviation: Deviation, media_url: str) -> Optional[str]:
    """Best-effort file extension from the download URL or deviation media."""
    path = media_url.split("?")[0]
    leaf = path.rstrip("/").rsplit("/", 1)[-1]
    if "." in leaf:
        ext = leaf.rsplit(".", 1)[-1].lower()
        if ext.isalnum() and 1 < len(ext) <= 10:
            return ext
    media = deviation.media or {}
    if media:
        return deviation._extract_extension_from_media(media).lstrip(".") or None
    return None


class OfficialProvider:
    """Official-API provider (OAuth). Handles every target kind except SEARCH.

    Original quality uses ``deviation/download/{uuid}`` (never preview URLs);
    ``best``/``preview`` fall back to the deviation's ``content``/``preview``
    images already present in the list response.
    """

    def __init__(
        self, client: OfficialApiClient, quality: str = "o", limit: int = 24
    ) -> None:
        self.client = client
        self.quality = quality
        self.limit = limit

    def resolve(self, target: DownloadTarget) -> Iterator[DownloadItem]:
        kind = target.kind
        if kind == TargetKind.ARTWORK:
            yield from self._artwork_items(target)
            return
        if kind == TargetKind.SEARCH:
            raise MediaUnavailableError(
                "the official API no longer has a search endpoint; use a web/cookie session"
            )

        username = target.username or ""
        if kind in (TargetKind.GALLERY, TargetKind.USER):
            fetch: Callable[[int], dict] = lambda offset: self.client.gallery_all(
                username, offset, self.limit
            )
        elif kind == TargetKind.GALLERY_FOLDER:
            fetch = lambda offset: self.client.gallery(
                username, target.identifier or "", offset, self.limit
            )
        elif kind == TargetKind.FAVORITES:
            fetch = lambda offset: self.client.collections_all(
                username, offset, self.limit
            )
        elif kind == TargetKind.FAVORITES_FOLDER:
            fetch = lambda offset: self.client.collections(
                username, target.identifier or "", offset, self.limit
            )
        elif kind == TargetKind.TAG:
            fetch = lambda offset: self.client.browse_tags(
                target.identifier or "", offset, self.limit
            )
        else:
            raise MediaUnavailableError(f"unsupported target kind: {kind}")
        yield from self._paginate(fetch)

    def _artwork(self, target: DownloadTarget) -> DownloadItem:
        # 兼容旧的单返回值调用（resolve 里已改用 _artwork_items）
        return next(self._artwork_items(target))

    def _artwork_items(self, target: DownloadTarget) -> Iterator[DownloadItem]:
        """单作品下载。多文件作品的附加画面来自网页 init 响应
        （deviation.extended.additionalMedia，官方 API 不再返回），逐个产出下载项；
        没有附加画面时只下主图（行为与以前一致）。"""
        identifier = target.identifier or ""
        init_data = deviation_init(identifier, target.username)
        uuid = deviation_uuid(init_data)
        main = self._item(self.client.deviation(uuid))
        yield main
        for index, url in enumerate(additional_media_urls(init_data), start=1):
            item = DownloadItem(
                artwork_id=f"{main.artwork_id}-{index}",
                url=main.url,
                title=main.title,
                author=main.author,
                media_url=url,
                extension=_ext_from_url(url),
                published_at=main.published_at,
                mature=main.mature,
                metadata={**main.metadata, "index": index},
            )
            yield item

    def _paginate(self, fetch: Callable[[int], dict]) -> Iterator[DownloadItem]:
        offset = 0
        seen: set[int] = set()
        while True:
            if offset in seen:
                raise ParseError("pagination did not advance")
            seen.add(offset)
            data = fetch(offset)
            results = data.get("results") or []
            for deviation in results:
                if isinstance(deviation, dict):
                    yield self._item(deviation)
            if not data.get("has_more"):
                break
            offset = data.get("next_offset") or (offset + len(results))

    def _item(self, deviation: dict) -> DownloadItem:
        uuid = str(deviation.get("deviationid") or deviation.get("deviationId") or "")
        if not uuid:
            raise ParseError("a deviation is missing its id")
        author = deviation.get("author") or {}
        media_url, ext = self._media(deviation, uuid)
        return DownloadItem(
            artwork_id=uuid,
            url=str(deviation.get("url") or ""),
            title=str(deviation.get("title") or "Untitled"),
            author=str(author.get("username") or "unknown"),
            media_url=media_url,
            extension=ext,
            published_at=_parse_published(deviation.get("published_time")),
            mature=bool(deviation.get("is_mature", False)),
            metadata={"quality": self.quality},
        )

    def _media(self, deviation: dict, uuid: str) -> tuple[str, Optional[str]]:
        if self.quality == "o" and deviation.get("is_downloadable"):
            original = self.client.original_download(uuid)
            ext = _ext_from_url(original.filename)
            return original.url, ext
        content = deviation.get("content") or {}
        if content.get("src"):
            return str(content["src"]), _ext_from_url(str(content["src"]))
        preview = deviation.get("preview") or {}
        if preview.get("src"):
            return str(preview["src"]), _ext_from_url(str(preview["src"]))
        thumbs = deviation.get("thumbs") or []
        if thumbs and isinstance(thumbs[0], dict) and thumbs[0].get("src"):
            return str(thumbs[0]["src"]), _ext_from_url(str(thumbs[0]["src"]))
        raise MediaUnavailableError(f"no media available for deviation {uuid}")


def _ext_from_url(url: str) -> Optional[str]:
    path = url.split("?")[0]
    leaf = path.rstrip("/").rsplit("/", 1)[-1]
    if "." in leaf:
        ext = leaf.rsplit(".", 1)[-1].lower()
        if ext.isalnum() and 1 < len(ext) <= 10:
            return ext
    return None


def _parse_published(value: Any) -> Optional[datetime]:
    if value is None:
        return None
    try:
        timestamp = int(value)
    except (TypeError, ValueError):
        return None
    if timestamp <= 0:
        return None
    if timestamp > 100_000_000_000:  # milliseconds
        timestamp //= 1000
    return datetime.fromtimestamp(timestamp, tz=timezone.utc)


__all__ = ["DeviantArtProvider", "OfficialProvider", "WebProvider"]
