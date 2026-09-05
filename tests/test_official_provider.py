"""Tests for the OfficialProvider (official API → DownloadItem)."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

import da_downloader.provider as provider_mod
from da_downloader.errors import MediaUnavailableError
from da_downloader.official_api import (
    OriginalDownload,
    _extract_numeric_id,
    _resolve_short_id,
)
from da_downloader.provider import OfficialProvider
from da_downloader.targets import TargetParser


def make_deviation(
    uuid="uuid-1",
    title="Art",
    author="alice",
    content_src="https://images.test/full.jpg",
    is_downloadable=True,
    mature=False,
):
    return {
        "deviationid": uuid,
        "title": title,
        "author": {"username": author},
        "url": f"https://www.deviantart.com/{author}/art/{title}",
        "content": {"src": content_src},
        "preview": {"src": "https://images.test/preview.jpg"},
        "is_downloadable": is_downloadable,
        "is_mature": mature,
        "published_time": 1427750464,
    }


class FakeClient:
    def __init__(self) -> None:
        self.deviations: dict = {}
        self.originals: dict = {}
        self.pages: dict = {}

    def deviation(self, uuid):
        return self.deviations[uuid]

    def original_download(self, uuid):
        return self.originals[uuid]

    def gallery_all(self, username, offset=0, limit=24):
        return self.pages[("gallery_all", username, offset)]

    def browse_tags(self, tag, offset=0, limit=24):
        return self.pages[("browse_tags", tag, offset)]


def test_artwork_original(monkeypatch) -> None:
    monkeypatch.setattr(provider_mod, "deviation_init", lambda identifier, username=None, **_: {"deviation": {"extended": {"deviationUuid": "uuid-1", "additionalMedia": []}}})
    client = FakeClient()
    client.deviations["uuid-1"] = make_deviation()
    client.originals["uuid-1"] = OriginalDownload(
        "https://download.test/original.jpg", "original.jpg"
    )
    provider = OfficialProvider(client, quality="o")

    items = list(provider.resolve(TargetParser.parse("https://www.deviantart.com/alice/art/x-123456")))

    assert len(items) == 1
    assert items[0].media_url == "https://download.test/original.jpg"
    assert items[0].extension == "jpg"
    assert items[0].author == "alice"
    assert items[0].title == "Art"
    assert items[0].mature is False
    assert items[0].published_at == datetime(2015, 3, 30, 21, 21, 4, tzinfo=timezone.utc)


def test_artwork_multimedia_yields_every_file(monkeypatch) -> None:
    init = {
        "deviation": {
            "extended": {
                "deviationUuid": "uuid-1",
                "additionalMedia": [
                    {"fileId": 2, "media": {"baseUri": "https://media.test/p2.jpg", "token": ["t2"]}},
                    {"fileId": 3, "media": {"baseUri": "https://media.test/p3.png", "token": ["t3"]}},
                ],
            }
        }
    }
    monkeypatch.setattr(provider_mod, "deviation_init", lambda identifier, username=None, **_: init)
    client = FakeClient()
    client.deviations["uuid-1"] = make_deviation()
    provider = OfficialProvider(client, quality="f")

    items = list(provider.resolve(TargetParser.parse("https://www.deviantart.com/alice/art/x-123456")))

    assert len(items) == 3  # 主图 + 两张附加
    assert items[0].media_url == "https://images.test/full.jpg"
    assert items[1].media_url == "https://media.test/p2.jpg?token=t2"
    assert items[1].artwork_id == "uuid-1-1"
    assert items[2].media_url == "https://media.test/p3.png?token=t3"
    assert items[2].extension == "png"


def test_artwork_best_uses_content(monkeypatch) -> None:
    monkeypatch.setattr(provider_mod, "deviation_init", lambda identifier, username=None, **_: {"deviation": {"extended": {"deviationUuid": "uuid-1", "additionalMedia": []}}})
    client = FakeClient()
    client.deviations["uuid-1"] = make_deviation()
    provider = OfficialProvider(client, quality="f")

    items = list(provider.resolve(TargetParser.parse("123456")))

    assert items[0].media_url == "https://images.test/full.jpg"
    assert client.originals == {}  # never called the download endpoint


def test_gallery_paginates(monkeypatch) -> None:
    client = FakeClient()
    client.pages[("gallery_all", "alice", 0)] = {
        "results": [make_deviation("uuid-1"), make_deviation("uuid-2", title="B")],
        "has_more": True,
        "next_offset": 24,
    }
    client.pages[("gallery_all", "alice", 24)] = {
        "results": [make_deviation("uuid-3", title="C")],
        "has_more": False,
    }
    client.originals["uuid-1"] = OriginalDownload("https://d.test/1.jpg", "1.jpg")
    client.originals["uuid-2"] = OriginalDownload("https://d.test/2.jpg", "2.jpg")
    client.originals["uuid-3"] = OriginalDownload("https://d.test/3.jpg", "3.jpg")
    provider = OfficialProvider(client, quality="o")

    items = list(provider.resolve(TargetParser.parse("https://www.deviantart.com/alice/gallery")))

    assert [i.artwork_id for i in items] == ["uuid-1", "uuid-2", "uuid-3"]


def test_no_media_raises(monkeypatch) -> None:
    monkeypatch.setattr(provider_mod, "deviation_init", lambda identifier, username=None, **_: {"deviation": {"extended": {"deviationUuid": "uuid-1", "additionalMedia": []}}})
    client = FakeClient()
    client.deviations["uuid-1"] = {
        "deviationid": "uuid-1",
        "title": "No Media",
        "author": {"username": "alice"},
        "is_downloadable": False,
    }
    provider = OfficialProvider(client, quality="f")

    with pytest.raises(MediaUnavailableError):
        list(provider.resolve(TargetParser.parse("123456")))


def test_tag_target() -> None:
    client = FakeClient()
    client.pages[("browse_tags", "landscape", 0)] = {
        "results": [make_deviation("uuid-1")],
        "has_more": False,
    }
    provider = OfficialProvider(client, quality="f")

    items = list(provider.resolve(TargetParser.parse("https://www.deviantart.com/tag/landscape")))

    assert [i.artwork_id for i in items] == ["uuid-1"]
    assert items[0].media_url == "https://images.test/full.jpg"


def test_extract_numeric_id() -> None:
    assert _extract_numeric_id("https://www.deviantart.com/u/art/title-123456") == "123456"
    assert _extract_numeric_id("https://www.deviantart.com/u/art/123456") == "123456"
    assert _extract_numeric_id("https://www.deviantart.com/u/gallery") is None


def test_resolve_short_id_follows_redirect() -> None:
    class FakeResponse:
        url = "https://www.deviantart.com/alice/art/title-123456"

        def close(self) -> None:
            pass

    class FakeHttp:
        def get(self, url, allow_redirects=True, timeout=30, stream=True):
            return FakeResponse()

    assert _resolve_short_id("abc123", FakeHttp(), 30) == "123456"
