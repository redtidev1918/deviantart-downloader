"""Real captured CDN 403 regression; provenance is beside the fixture."""

import base64
import copy
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from da_downloader.api import DeviantArtAPI
from da_downloader.models import Deviation, DownloadItem, make_media_asset
from da_downloader.official_api import _descriptor_media_url, additional_media_urls
from da_downloader.provider import OfficialProvider, WebProvider
from da_downloader.targets import TargetParser
from da_downloader.wix_media import append_media_token, bounded_fullview_url


def test_existing_query_and_signature_are_preserved():
    assert append_media_token("https://example.test/a.jpg?download=1", "fresh") == "https://example.test/a.jpg?download=1&token=fresh"
    signed = "https://example.test/a.jpg?download=1&token=existing"
    assert append_media_token(signed, "fresh") == signed

SAMPLES = json.loads((Path(__file__).parent / "fixtures/deviantart-bounded-media.json").read_text(encoding="utf-8-sig"))["samples"]
DESCRIPTORS = [m for d in SAMPLES for m in [d["media"], *[e["media"] for e in d["extended"]["additionalMedia"]]]]


@pytest.mark.parametrize("media", DESCRIPTORS)
def test_captured_bounded_media_selects_fullview_in_both_paths(media, caplog):
    full = next(t for t in media["types"] if t["t"] == "fullview")
    expected = media["baseUri"] + full["c"].replace("<prettyName>", media["prettyName"]) + "?token=" + media["token"][0]
    api = DeviantArtAPI({}, {})
    assert api._get_full_view_url(media, media["baseUri"], media["token"][0], media["prettyName"]) == expected
    assert _descriptor_media_url(media) == expected
    assert "not the uploaded original" in caplog.text


def test_extra_page_is_not_lost_or_replaced_by_small_preview():
    result = additional_media_urls({"deviation": SAMPLES[0]})
    assert len(result) == 1
    assert "-fullview.jpg?token=" in result[0]
    assert "-pre.jpg" not in result[0]


@pytest.mark.parametrize("token", [None, [], "opaque", "a.bad.c"])
def test_unknown_token_preserves_original_selection(token):
    media = {**SAMPLES[1]["media"], "token": token}
    assert bounded_fullview_url(media) is None


def test_unbounded_original_gif_and_video_stay_unchanged():
    media = copy.deepcopy(SAMPLES[1]["media"])
    payload = media["token"][0].split(".")[1]
    claims = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
    claims["obj"][0][0].pop("width")
    claims["obj"][0][0].pop("height")
    payload = base64.urlsafe_b64encode(json.dumps(claims).encode()).decode().rstrip("=")
    media["token"] = [f"test.{payload}.REDACTED"]
    assert bounded_fullview_url(media) is None
    assert _descriptor_media_url(media).startswith(media["baseUri"] + "?token=")
    gif = {**media, "baseUri": media["baseUri"].replace(".jpg", ".gif")}
    assert _descriptor_media_url(gif).startswith(gif["baseUri"] + "?token=")
    video = {**SAMPLES[1]["media"], "types": [{"t": "video", "b": "https://example.test/movie.mp4", "q": "1080p"}]}
    assert _descriptor_media_url(video).startswith("https://example.test/movie.mp4")


def test_no_fullview_does_not_substitute_preview():
    media = copy.deepcopy(SAMPLES[1]["media"])
    media["types"] = [t for t in media["types"] if t["t"] != "fullview"]
    assert bounded_fullview_url(media) is None
    assert _descriptor_media_url(media).startswith(media["baseUri"] + "?token=")


def test_original_endpoint_still_wins_and_fullview_metadata_is_explicit(monkeypatch):
    media = SAMPLES[1]["media"]
    deviation = Deviation(deviation_id="1403090181", title="Untitled", author="lol1729", url="https://www.deviantart.com/lol1729/art/Untitled-1403090181", media=media, is_downloadable=True, is_mature=False, deviation_type="image")
    api = DeviantArtAPI({}, {})
    monkeypatch.setattr(api, "_get_original_download_url", lambda _: "https://example.test/original.jpg")
    assert api.get_download_url(deviation, "o") == "https://example.test/original.jpg"
    item = WebProvider(api, quality="f")._to_item(deviation)
    assert item.metadata["representation"] == "fullview"
    assert item.metadata["original_available"] is False
    assert item.extension == "jpg"
    asset = make_media_asset(item.artwork_id, 0, item.media_url, extension=item.extension, representation=item.metadata["representation"])
    assert asset.to_dict()["representation"] == "fullview"


def test_additional_page_metadata_does_not_claim_the_main_original_quality(monkeypatch):
    import da_downloader.provider as provider_mod

    sample = SAMPLES[0]
    uuid = sample["extended"]["deviationUuid"]
    monkeypatch.setattr(provider_mod, "deviation_init", lambda *a, **kw: {"deviation": sample})
    provider = OfficialProvider(SimpleNamespace(deviation=lambda _: {}), quality="o")
    main = DownloadItem(artwork_id=uuid, url="https://example.test/art", title="Work", author="Artist", media_url="https://example.test/original.png", extension="png", metadata={"quality": "o"})
    monkeypatch.setattr(provider, "_item", lambda _: main)
    items = list(provider.resolve(TargetParser.parse("1402511705")))
    assert len(items) == 2
    assert items[0] is main
    assert "representation" not in main.metadata
    assert items[1].artwork_id == uuid + "-1"
    assert items[1].metadata["representation"] == "fullview"
    assert items[1].metadata["original_available"] is False
    assert items[1].extension == "jpg"
