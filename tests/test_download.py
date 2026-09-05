"""Tests for the Downloader facade and quality normalization."""

from __future__ import annotations

from pathlib import Path

import pytest

from da_downloader.archive import DownloadArchive, artwork_key
from da_downloader.download import Downloader, normalize_quality
from da_downloader.http import TransferResult
from da_downloader.manager import DownloadManager
from da_downloader.models import DownloadItem
from da_downloader.path import PathFormatter


class FakeProvider:
    def __init__(self, items) -> None:
        self.items = list(items)
        self.targets = []

    def resolve(self, target):
        self.targets.append(target)
        yield from self.items


class FakeDownloader:
    def download(self, url, destination, *, overwrite=False, headers=None, timeout=None):
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(b"data")
        return TransferResult(destination, 4)


def make_item() -> DownloadItem:
    return DownloadItem(
        artwork_id="1",
        url="https://www.deviantart.com/alice/art/x-1",
        title="Art",
        author="alice",
        media_url="https://images.test/1.jpg",
        extension="jpg",
    )


def test_normalize_quality() -> None:
    assert normalize_quality("original") == "o"
    assert normalize_quality("best") == "f"
    assert normalize_quality("preview") == "p"
    assert normalize_quality("o") == "o"
    assert normalize_quality("f") == "f"
    assert normalize_quality("p") == "p"
    assert normalize_quality("") == "f"  # default
    assert normalize_quality("ORIGINAL") == "o"


def test_normalize_quality_rejects_unknown() -> None:
    with pytest.raises(ValueError):
        normalize_quality("huge")


def test_downloader_end_to_end(tmp_path: Path) -> None:
    archive = DownloadArchive(tmp_path / "archive.sqlite")
    manager = DownloadManager(
        downloader=FakeDownloader(),
        formatter=PathFormatter(tmp_path),
        archive=archive,
        write_info_json=True,
    )
    downloader = Downloader(FakeProvider([make_item()]), manager)

    outcomes = downloader.download("https://www.deviantart.com/alice/gallery")

    assert len(outcomes) == 1
    assert outcomes[0].status == "downloaded"
    assert outcomes[0].path is not None and outcomes[0].path.exists()
    assert archive.contains(artwork_key("1"))
    # metadata sidecar written next to the file
    assert outcomes[0].path.with_name(outcomes[0].path.name + ".json").exists()


def test_downloader_parses_target(tmp_path: Path) -> None:
    provider = FakeProvider([make_item()])
    manager = DownloadManager(
        downloader=FakeDownloader(), formatter=PathFormatter(tmp_path)
    )
    downloader = Downloader(provider, manager)

    downloader.download("https://www.deviantart.com/alice/gallery")

    from da_downloader.targets import TargetKind

    assert provider.targets[0].kind == TargetKind.GALLERY
    assert provider.targets[0].username == "alice"
