"""Domain models: the web-API action types, the raw deviation, and the
DownloadItem contract that crosses the provider/downloader boundary."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Mapping, Optional


class ActionType(Enum):
    """Web-API action type."""

    GALLERY = "gallery"
    SEARCH = "search"
    FAVORITE = "fav"


@dataclass
class Deviation:
    """A raw deviation parsed from a web API response."""

    deviation_id: str
    title: str
    url: str
    author: str
    media: Dict[str, Any]
    is_downloadable: bool
    is_mature: bool
    deviation_type: str

    @classmethod
    def from_api_response(cls, data: Dict[str, Any]) -> "Deviation":
        if "deviation" in data:
            data = data["deviation"]

        deviation_id = data.get("deviationId", data.get("deviationid"))
        if deviation_id in (None, ""):
            raise ValueError("deviation ID is missing")

        author = data.get("author") or {}
        if not isinstance(author, dict):
            author = {}
        media = data.get("media") or {}
        if not isinstance(media, dict):
            media = {}

        deviation_type = data.get("type", "unknown")
        if data.get("isVideo"):
            deviation_type = "video"
        elif data.get("isJournal"):
            deviation_type = "literature"

        return cls(
            deviation_id=str(deviation_id),
            title=str(data.get("title") or "Untitled"),
            url=str(data.get("url") or ""),
            author=str(author.get("username") or "Unknown"),
            media=media,
            is_downloadable=bool(
                data.get("isDownloadable", data.get("is_downloadable", False))
            ),
            is_mature=bool(data.get("isMature", data.get("is_mature", False))),
            deviation_type=str(deviation_type),
        )

    def _extract_extension_from_media(self, media: Dict[str, Any]) -> str:
        if "types" in media:
            types = media["types"]
            if isinstance(types, list):
                for item in types:
                    if isinstance(item, dict) and item.get("t") == "video":
                        return ".mp4"
        base_uri = media.get("baseUri", "")
        if base_uri:
            return self._extract_extension(base_uri)
        return ".mp4" if self.deviation_type in ("video", "film") else ".jpg"

    def _extract_extension(self, uri: str) -> str:
        parts = uri.split(".")
        if len(parts) > 1:
            ext = parts[-1].split("?")[0]
            return f".{ext}"
        return ".jpg"

    def is_downloadable_type(self) -> bool:
        return self.deviation_type not in ("literature",)

    def __str__(self) -> str:
        flags = []
        if self.is_mature:
            flags.append("MATURE")
        if self.is_downloadable:
            flags.append("DOWNLOADABLE")
        flag_str = f" [{', '.join(flags)}]" if flags else ""
        return f"{self.title} by {self.author}{flag_str}"


@dataclass(frozen=True)
class DownloadItem:
    """A single resolved media file, produced by a provider and consumed by the
    downloader. This is the boundary between "understand DeviantArt" and
    "write bytes to disk": the downloader never sees API DTOs, CSRF, or
    ``_puppy`` endpoints — only this contract."""

    artwork_id: str
    url: str  # deviation page URL (for metadata / archive identity)
    title: str
    author: str
    media_url: str  # the actual file to download
    extension: Optional[str] = None  # without leading dot, e.g. "jpg"
    published_at: Optional[datetime] = None
    mature: bool = False
    metadata: Mapping[str, Any] = field(default_factory=dict)
