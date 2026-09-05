"""Tests for the WebProvider (target → DownloadItem)."""

from __future__ import annotations

import pytest

from da_downloader.api import ActionType
from da_downloader.errors import MediaUnavailableError
from da_downloader.models import Deviation
from da_downloader.provider import WebProvider
from da_downloader.targets import TargetParser


def make_deviation(identifier="123", title="Art", author="alice", mature=False) -> Deviation:
    return Deviation(
        deviation_id=identifier,
        title=title,
        url=f"https://www.deviantart.com/{author}/art/{title}-{identifier}",
        author=author,
        media={
            "baseUri": f"https://images.test/{identifier}.jpg",
            "prettyName": title.lower(),
            "token": ["token"],
            "types": [{"t": "fullview", "c": "/f/<prettyName>.jpg"}],
        },
        is_downloadable=False,
        is_mature=mature,
        deviation_type="image",
    )


class FakeAPI:
    def __init__(self, pages=None) -> None:
        self.pages = list(pages or [])
        self.fetch_calls: list[tuple] = []
        self.build_calls: list[tuple] = []
        self.media_urls: dict[str, str] = {}

    def get_csrf_token(self, username=""):
        return "csrf"

    def build_api_url(self, action, username, query=None, folder_id=None):
        self.build_calls.append((action, username, query, folder_id))
        return "URL?offset=<OFFSET>&limit=<LIMIT>"

    def fetch_deviations(self, url, offset=0, cursor=""):
        self.fetch_calls.append((offset, cursor))
        return self.pages.pop(0)

    def get_download_url(self, deviation, quality):
        return self.media_urls.get(deviation.deviation_id)


def make_provider(pages, media_urls=None, quality="f") -> WebProvider:
    api = FakeAPI(pages=pages)
    api.media_urls = media_urls or {}
    return WebProvider(api, quality=quality)


def test_gallery_yields_items_with_media_url_and_extension() -> None:
    dev = make_deviation()
    provider = make_provider(
        pages=[([dev], False, 1, "")],
        media_urls={"123": "https://images.test/123.png"},
    )

    items = list(provider.resolve(TargetParser.parse("https://www.deviantart.com/alice/gallery")))

    assert len(items) == 1
    assert items[0].artwork_id == "123"
    assert items[0].author == "alice"
    assert items[0].media_url == "https://images.test/123.png"
    assert items[0].extension == "png"


def test_pagination_across_two_pages() -> None:
    first = make_deviation("1")
    second = make_deviation("2")
    provider = make_provider(
        pages=[([first], True, 24, ""), ([second], False, 48, "")],
        media_urls={"1": "https://images.test/1.jpg", "2": "https://images.test/2.jpg"},
    )

    items = list(provider.resolve(TargetParser.parse("https://www.deviantart.com/alice/gallery")))

    assert [i.artwork_id for i in items] == ["1", "2"]
    assert len(provider.api.fetch_calls) == 2


def test_artwork_target_requires_official_api() -> None:
    provider = make_provider(pages=[])
    with pytest.raises(MediaUnavailableError):
        list(provider.resolve(TargetParser.parse("https://www.deviantart.com/a/art/x-123")))


def test_tag_target_requires_official_api() -> None:
    provider = make_provider(pages=[])
    with pytest.raises(MediaUnavailableError):
        list(provider.resolve(TargetParser.parse("https://www.deviantart.com/tag/landscape")))


def test_original_quality_falls_back_to_full() -> None:
    dev = make_deviation()

    class FallbackAPI(FakeAPI):
        def get_download_url(self, deviation, quality):
            return "https://images.test/123.jpg" if quality == "f" else None

    provider = WebProvider(FallbackAPI(pages=[([dev], False, 1, "")]), quality="o")

    items = list(provider.resolve(TargetParser.parse("https://www.deviantart.com/alice/gallery")))

    assert items[0].media_url == "https://images.test/123.jpg"


def test_search_target_builds_search_action() -> None:
    dev = make_deviation()
    provider = make_provider(
        pages=[([dev], False, 1, "")], media_urls={"123": "https://images.test/123.jpg"}
    )

    list(provider.resolve(TargetParser.parse("https://www.deviantart.com/search?q=digital+art")))

    action, username, query, folder = provider.api.build_calls[0]
    assert action == ActionType.SEARCH
    assert query == "digital art"
