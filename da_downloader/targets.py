"""Parse a DeviantArt URL (or bare artwork id) into a typed ``DownloadTarget``.

This is the URL-first entry point: the CLI hands a URL or id here, and gets back
a target the provider can resolve — rather than every command parsing URLs for
itself.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from urllib.parse import parse_qs, urlparse

from .errors import ParseError

_UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)
_NUMERIC_RE = re.compile(r"^\d+$")
_SLUG_ID_RE = re.compile(r"-(\d+)$")


class TargetKind(str, Enum):
    ARTWORK = "artwork"
    GALLERY = "gallery"  # all folders
    GALLERY_FOLDER = "gallery_folder"
    FAVORITES = "favorites"  # all folders
    FAVORITES_FOLDER = "favorites_folder"
    TAG = "tag"
    USER = "user"  # all of an artist's works
    SEARCH = "search"


@dataclass(frozen=True)
class DownloadTarget:
    """A resolved download target; provider-specific ids are opaque strings."""

    kind: TargetKind
    username: str | None = None
    identifier: str | None = None  # artwork id / folder id / tag / fav.me code
    query: str | None = None  # search query


class TargetParser:
    """Parses DeviantArt URLs and bare artwork ids into ``DownloadTarget``."""

    @classmethod
    def parse(cls, value: str) -> DownloadTarget:
        text = value.strip()
        if not text:
            raise ParseError("empty target")

        if _UUID_RE.match(text) or _NUMERIC_RE.match(text):
            return DownloadTarget(TargetKind.ARTWORK, identifier=text)

        if "://" not in text:
            text = "https://" + text
        url = urlparse(text)
        host = (url.netloc or "").lower()
        segments = [s for s in url.path.rstrip("/").split("/") if s]

        if host == "fav.me":
            code = segments[0] if segments else ""
            if not code:
                raise ParseError("fav.me link is missing its code")
            return DownloadTarget(TargetKind.ARTWORK, identifier=code)

        if not segments:
            raise ParseError(f"unrecognized target: {value}")

        first = segments[0]
        if first == "tag":
            tag = segments[1] if len(segments) > 1 else ""
            if not tag:
                raise ParseError("tag URL is missing the tag name")
            return DownloadTarget(TargetKind.TAG, identifier=tag)
        if first == "search":
            query = parse_qs(url.query).get("q", [""])[0]
            return DownloadTarget(TargetKind.SEARCH, query=query)

        username = first
        rest = segments[1:]
        if not rest:
            return DownloadTarget(TargetKind.USER, username=username)

        section = rest[0]
        if section == "art":
            return DownloadTarget(
                TargetKind.ARTWORK,
                username=username,
                identifier=_extract_artwork_id(rest[-1], value),
            )
        if section == "gallery":
            folder = rest[1] if len(rest) > 1 else None
            if folder:
                return DownloadTarget(
                    TargetKind.GALLERY_FOLDER, username=username, identifier=folder
                )
            return DownloadTarget(TargetKind.GALLERY, username=username)
        if section in ("favourites", "favorites"):
            folder = rest[1] if len(rest) > 1 else None
            if folder:
                return DownloadTarget(
                    TargetKind.FAVORITES_FOLDER, username=username, identifier=folder
                )
            return DownloadTarget(TargetKind.FAVORITES, username=username)
        if section == "search":
            query = parse_qs(url.query).get("q", [""])[0]
            return DownloadTarget(TargetKind.SEARCH, query=query)
        if section == "posts":
            # Journals/status posts; treat as the artist's works for now.
            return DownloadTarget(TargetKind.USER, username=username)

        raise ParseError(f"unrecognized DeviantArt target: {value}")


def _extract_artwork_id(slug: str, original: str) -> str:
    if _NUMERIC_RE.match(slug):
        return slug
    if _UUID_RE.match(slug):
        return slug
    match = _SLUG_ID_RE.search(slug)
    if match:
        return match.group(1)
    raise ParseError(f"could not extract an artwork id from: {original}")


__all__ = ["DownloadTarget", "TargetKind", "TargetParser"]
