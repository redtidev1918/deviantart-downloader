"""Thin download orchestration.

For each ``DownloadItem`` the manager performs, in order: archive check,
path formatting, download (the ``HttpDownloader`` handles ``.part``/Range
resume/atomic rename), then archive commit and optional metadata sidecar. It
knows nothing about DeviantArt endpoints — only the ``DownloadItem`` contract.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .archive import DownloadArchive, artwork_key
from .errors import DeviantArtError
from .http import HttpDownloader, TransferResult
from .models import DownloadItem
from .path import PathFormatter


@dataclass(frozen=True)
class DownloadOutcome:
    """Result of processing one item through the manager."""

    item_id: str
    status: str  # "downloaded" | "skipped" | "failed"
    path: Optional[Path] = None
    reason: Optional[str] = None
    size: int = 0
    resumed: bool = False


class DownloadManager:
    """Orchestrates archive → path → download → archive commit."""

    def __init__(
        self,
        *,
        downloader: HttpDownloader,
        formatter: PathFormatter,
        archive: Optional[DownloadArchive] = None,
        overwrite: bool = False,
        write_info_json: bool = False,
    ) -> None:
        self.downloader = downloader
        self.formatter = formatter
        self.archive = archive
        self.overwrite = overwrite
        self.write_info_json = write_info_json

    def run(self, item: DownloadItem) -> DownloadOutcome:
        key = artwork_key(item.artwork_id)
        if self.archive is not None and self.archive.contains(key):
            return DownloadOutcome(item.artwork_id, "skipped", reason="archived")

        path = self.formatter.resolve(
            id=item.artwork_id,
            title=item.title,
            author=item.author,
            published=item.published_at,
            ext=item.extension,
        )

        if path.exists() and not self.overwrite:
            return DownloadOutcome(item.artwork_id, "skipped", path=path, reason="exists")

        try:
            result: TransferResult = self.downloader.download(
                item.media_url, path, overwrite=self.overwrite
            )
        except DeviantArtError as exc:
            return DownloadOutcome(item.artwork_id, "failed", path=path, reason=str(exc))

        if self.archive is not None:
            self.archive.add(key)
        if self.write_info_json:
            self._write_info_json(item, path)
        return DownloadOutcome(
            item.artwork_id,
            "downloaded",
            path=path,
            size=result.size,
            resumed=result.resumed,
        )

    def _write_info_json(self, item: DownloadItem, path: Path) -> None:
        data: dict = dict(item.metadata)
        data.update(
            {
                "id": item.artwork_id,
                "title": item.title,
                "author": item.author,
                "url": item.url,
                "published_at": item.published_at.isoformat() if item.published_at else None,
                "mature": item.mature,
                "media_url": item.media_url,
                "downloaded_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        sidecar = path.with_name(path.name + ".json")
        sidecar.write_text(
            json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
        )


__all__ = ["DownloadManager", "DownloadOutcome"]
