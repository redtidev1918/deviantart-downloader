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


def test_build_downloader_wires_capability_router_with_oauth_and_cookies(
    tmp_path: Path, monkeypatch
) -> None:
    from da_downloader.download import build_downloader
    from da_downloader.provider import CompositeProvider, OfficialProvider, WebProvider

    class FakeSession:
        def authorization_header(self, force=False):
            return "Bearer x"

    monkeypatch.setattr(
        "da_downloader.download.OAuthSession.from_store", classmethod(lambda cls: FakeSession())
    )

    downloader = build_downloader(
        destination=tmp_path, cookies="auth=token; auth_secure=secret"
    )

    router = downloader.provider
    assert isinstance(router, CompositeProvider)
    assert router.official is not None and isinstance(router.official, OfficialProvider)
    assert router.web is not None and isinstance(router.web, WebProvider)


def test_build_downloader_without_oauth_uses_composite_web_only(
    tmp_path: Path, monkeypatch
) -> None:
    from da_downloader.download import build_downloader
    from da_downloader.provider import CompositeProvider, WebProvider

    monkeypatch.setattr(
        "da_downloader.download.OAuthSession.from_store", classmethod(lambda cls: None)
    )

    downloader = build_downloader(destination=tmp_path)

    router = downloader.provider
    assert isinstance(router, CompositeProvider)
    assert router.official is None
    assert isinstance(router.web, WebProvider)


def test_resolve_groups_additional_media_into_one_work() -> None:
    main = DownloadItem(
        artwork_id="uuid-1",
        url="https://www.deviantart.com/alice/art/x-1",
        title="Art",
        author="alice",
        media_url="https://images.test/1.jpg",
        extension="jpg",
        mature=True,
    )
    extra = DownloadItem(
        artwork_id="uuid-1-1",
        url=main.url,
        title=main.title,
        author=main.author,
        media_url="https://images.test/2.png",
        extension="png",
        metadata={"index": 1},
    )
    downloader = Downloader(FakeProvider([main, extra]), manager=None)

    works = downloader.resolve("https://www.deviantart.com/alice/art/x-123")

    assert len(works) == 1
    work = works[0]
    assert work.id == "uuid-1"
    assert work.mature is True
    assert [a.id for a in work.media] == ["deviantart:uuid-1:p0", "deviantart:uuid-1:p1"]
    data = work.to_dict()
    assert data["work"]["title"] == "Art"
    assert data["media"][1]["sourceUrl"] == "https://images.test/2.png"
    assert data["media"][1]["mimeType"] == "image/png"
