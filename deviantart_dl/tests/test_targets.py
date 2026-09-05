"""Tests for URL → DownloadTarget parsing."""

from __future__ import annotations

import pytest

from da_downloader.errors import ParseError
from da_downloader.models import DownloadItem
from da_downloader.targets import DownloadTarget, TargetKind, TargetParser


def parse(value: str) -> DownloadTarget:
    return TargetParser.parse(value)


def test_bare_numeric_id() -> None:
    target = parse("123456")
    assert target.kind == TargetKind.ARTWORK
    assert target.identifier == "123456"


def test_bare_uuid() -> None:
    uuid = "a0367442-a7cf-4b5e-9b2a-585e6d98ce8d"
    target = parse(uuid)
    assert target.kind == TargetKind.ARTWORK
    assert target.identifier == uuid


def test_artwork_url() -> None:
    target = parse("https://www.deviantart.com/alice/art/title-123456")
    assert target.kind == TargetKind.ARTWORK
    assert target.username == "alice"
    assert target.identifier == "123456"


def test_artwork_url_with_bare_id_slug() -> None:
    target = parse("https://www.deviantart.com/alice/art/123456")
    assert target.kind == TargetKind.ARTWORK
    assert target.identifier == "123456"


def test_gallery_url() -> None:
    target = parse("https://www.deviantart.com/alice/gallery")
    assert target.kind == TargetKind.GALLERY
    assert target.username == "alice"


def test_gallery_folder_url() -> None:
    target = parse("https://www.deviantart.com/alice/gallery/12345")
    assert target.kind == TargetKind.GALLERY_FOLDER
    assert target.username == "alice"
    assert target.identifier == "12345"


def test_favourites_url() -> None:
    assert parse("https://www.deviantart.com/alice/favourites").kind == TargetKind.FAVORITES
    assert parse("https://www.deviantart.com/alice/favorites").kind == TargetKind.FAVORITES


def test_favourites_folder_url() -> None:
    target = parse("https://www.deviantart.com/alice/favourites/12345")
    assert target.kind == TargetKind.FAVORITES_FOLDER
    assert target.identifier == "12345"


def test_tag_url() -> None:
    target = parse("https://www.deviantart.com/tag/landscape")
    assert target.kind == TargetKind.TAG
    assert target.identifier == "landscape"


def test_user_profile_url() -> None:
    target = parse("https://www.deviantart.com/alice")
    assert target.kind == TargetKind.USER
    assert target.username == "alice"


def test_favme_short_link() -> None:
    target = parse("https://fav.me/abc123")
    assert target.kind == TargetKind.ARTWORK
    assert target.identifier == "abc123"


def test_search_url() -> None:
    target = parse("https://www.deviantart.com/search?q=digital+art")
    assert target.kind == TargetKind.SEARCH
    assert target.query == "digital art"


def test_empty_target_raises() -> None:
    with pytest.raises(ParseError):
        parse("")


def test_unrecognized_target_raises() -> None:
    with pytest.raises(ParseError):
        parse("https://www.deviantart.com/alice/unknown-section")


def test_download_item_is_frozen_and_typed() -> None:
    item = DownloadItem(
        artwork_id="123",
        url="https://www.deviantart.com/a/art/x-123",
        title="X",
        author="a",
        media_url="https://images.test/x.jpg",
        extension="jpg",
        mature=True,
    )
    assert item.artwork_id == "123"
    assert item.extension == "jpg"
    assert item.mature is True
    assert item.metadata == {}
