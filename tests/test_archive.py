"""Tests for the SQLite download archive."""

from __future__ import annotations

from pathlib import Path

from da_downloader.archive import DownloadArchive, artwork_key


def test_contains_returns_false_before_add(tmp_path: Path) -> None:
    archive = DownloadArchive(tmp_path / "archive.sqlite")
    try:
        assert archive.contains("deviantart:123") is False
    finally:
        archive.close()


def test_add_then_contains(tmp_path: Path) -> None:
    archive = DownloadArchive(tmp_path / "archive.sqlite")
    try:
        archive.add("deviantart:123")
        assert archive.contains("deviantart:123") is True
        assert archive.contains("deviantart:456") is False
    finally:
        archive.close()


def test_add_is_idempotent(tmp_path: Path) -> None:
    archive = DownloadArchive(tmp_path / "archive.sqlite")
    try:
        archive.add("deviantart:123")
        archive.add("deviantart:123")
        count = archive._conn.execute("SELECT COUNT(*) FROM archive").fetchone()[0]
        assert count == 1
    finally:
        archive.close()


def test_persists_across_reopen(tmp_path: Path) -> None:
    path = tmp_path / "archive.sqlite"
    with DownloadArchive(path) as archive:
        archive.add("deviantart:123")

    with DownloadArchive(path) as reopened:
        assert reopened.contains("deviantart:123") is True


def test_artwork_key_format() -> None:
    assert artwork_key("abc") == "deviantart:abc"
    assert artwork_key("abc", 2) == "deviantart:abc:2"
