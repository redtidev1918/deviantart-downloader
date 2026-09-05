"""Tests for the download manager orchestration."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from da_downloader.archive import DownloadArchive, artwork_key
from da_downloader.errors import DownloadError
from da_downloader.http import TransferResult
from da_downloader.manager import DownloadManager
from da_downloader.models import DownloadItem
from da_downloader.path import PathFormatter


class FakeDownloader:
    def __init__(self, result: TransferResult | None = None, error: Exception | None = None) -> None:
        self.result = result
        self.error = error
        self.calls: list[tuple] = []

    def download(self, url, destination, *, overwrite=False, headers=None, timeout=None) -> TransferResult:
        self.calls.append((url, destination, overwrite))
        if self.error:
            raise self.error
        if self.result:
            return self.result
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(b"data")
        return TransferResult(destination, 4)


def make_item(**overrides) -> DownloadItem:
    kwargs = dict(
        artwork_id="123",
        url="https://www.deviantart.com/a/art/x-123",
        title="Sunset",
        author="alice",
        media_url="https://images.test/sunset.jpg",
        extension="jpg",
        published_at=date(2025, 1, 15),
        mature=False,
    )
    kwargs.update(overrides)
    return DownloadItem(**kwargs)


def make_manager(tmp_path, *, downloader=None, archive=None, overwrite=False, write_info_json=False) -> DownloadManager:
    return DownloadManager(
        downloader=downloader or FakeDownloader(),
        formatter=PathFormatter(tmp_path),
        archive=archive,
        overwrite=overwrite,
        write_info_json=write_info_json,
    )


def test_downloads_and_adds_to_archive(tmp_path: Path) -> None:
    archive = DownloadArchive(tmp_path / "archive.sqlite")
    downloader = FakeDownloader()
    manager = make_manager(tmp_path, downloader=downloader, archive=archive)

    outcome = manager.run(make_item())

    assert outcome.status == "downloaded"
    assert outcome.path is not None and outcome.path.exists()
    assert archive.contains(artwork_key("123"))
    assert len(downloader.calls) == 1


def test_skips_when_archived(tmp_path: Path) -> None:
    archive = DownloadArchive(tmp_path / "archive.sqlite")
    archive.add(artwork_key("123"))
    downloader = FakeDownloader()
    manager = make_manager(tmp_path, downloader=downloader, archive=archive)

    outcome = manager.run(make_item())

    assert outcome.status == "skipped"
    assert outcome.reason == "archived"
    assert downloader.calls == []  # never touched the network


def test_skips_when_file_exists(tmp_path: Path) -> None:
    # Pre-create the file the formatter would produce.
    (tmp_path / "alice").mkdir()
    (tmp_path / "alice" / "123_Sunset.jpg").write_bytes(b"existing")
    downloader = FakeDownloader()
    manager = make_manager(tmp_path, downloader=downloader)

    outcome = manager.run(make_item())

    assert outcome.status == "skipped"
    assert outcome.reason == "exists"
    assert downloader.calls == []


def test_overwrite_re_downloads(tmp_path: Path) -> None:
    (tmp_path / "alice").mkdir()
    (tmp_path / "alice" / "123_Sunset.jpg").write_bytes(b"old")
    downloader = FakeDownloader()
    manager = make_manager(tmp_path, downloader=downloader, overwrite=True)

    outcome = manager.run(make_item())

    assert outcome.status == "downloaded"
    assert downloader.calls[0][2] is True  # overwrite flag forwarded


def test_failure_does_not_add_to_archive(tmp_path: Path) -> None:
    archive = DownloadArchive(tmp_path / "archive.sqlite")
    downloader = FakeDownloader(error=DownloadError("boom"))
    manager = make_manager(tmp_path, downloader=downloader, archive=archive)

    outcome = manager.run(make_item())

    assert outcome.status == "failed"
    assert outcome.reason == "boom"
    assert not archive.contains(artwork_key("123"))


def test_writes_info_json_sidecar(tmp_path: Path) -> None:
    downloader = FakeDownloader()
    manager = make_manager(tmp_path, downloader=downloader, write_info_json=True)

    outcome = manager.run(make_item(metadata={"tags": ["landscape"]}))

    assert outcome.path is not None
    sidecar = outcome.path.with_name(outcome.path.name + ".json")
    assert sidecar.exists()
    data = json.loads(sidecar.read_text(encoding="utf-8"))
    assert data["id"] == "123"
    assert data["author"] == "alice"
    assert data["tags"] == ["landscape"]


def test_path_stays_inside_root_for_evil_title(tmp_path: Path) -> None:
    downloader = FakeDownloader()
    manager = make_manager(tmp_path, downloader=downloader)

    outcome = manager.run(make_item(title="../../../../etc/passwd"))

    assert outcome.status == "downloaded"
    assert outcome.path is not None and outcome.path.is_relative_to(tmp_path)
