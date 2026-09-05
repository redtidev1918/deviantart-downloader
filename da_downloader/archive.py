"""SQLite-backed download archive.

A tiny, dependency-free record of already-downloaded entries (one row per
key). It is the single source of truth for "already downloaded", independent
of any particular session, unlike the per-session JSON progress files.

Callers must only call :meth:`DownloadArchive.add` *after* a file has been
successfully finalized — never for a failed or incomplete download.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path


class DownloadArchive:
    """A persistent set of downloaded entry keys backed by SQLite."""

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.path))
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS archive (entry TEXT PRIMARY KEY)"
        )
        self._conn.commit()

    def contains(self, key: str) -> bool:
        row = self._conn.execute(
            "SELECT 1 FROM archive WHERE entry = ?", (key,)
        ).fetchone()
        return row is not None

    def add(self, key: str) -> None:
        self._conn.execute(
            "INSERT OR IGNORE INTO archive (entry) VALUES (?)", (key,)
        )
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> "DownloadArchive":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()


def artwork_key(artwork_id: str, media_index: int | None = None) -> str:
    """Build an archive key for an artwork (optionally a specific media file)."""
    if media_index is None:
        return f"deviantart:{artwork_id}"
    return f"deviantart:{artwork_id}:{media_index}"


__all__ = ["DownloadArchive", "artwork_key"]
