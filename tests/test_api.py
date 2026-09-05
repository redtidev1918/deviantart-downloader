"""Tests for the web API client (DeviantArtAPI) used by WebProvider."""

from __future__ import annotations

from unittest.mock import Mock
from urllib.parse import parse_qs, urlparse

import pytest
from requests import RequestException

from da_downloader.api import APIError, DeviantArtAPI
from da_downloader.models import ActionType, Deviation


def api_client(max_retries: int = 1) -> DeviantArtAPI:
    return DeviantArtAPI({}, {}, retry_delay=0, max_retries=max_retries)


def deviation_payload(identifier: int = 123) -> dict:
    return {
        "deviationId": identifier,
        "type": "image",
        "url": f"https://www.deviantart.com/example/art/work-{identifier}",
        "title": "Work",
        "author": {"username": "example"},
        "isDownloadable": False,
        "isMature": False,
        "media": {
            "baseUri": "https://images.example.test/work.png",
            "prettyName": f"work_{identifier}",
            "token": ["token"],
            "types": [{"t": "fullview", "r": 1}],
        },
    }


def response_with_json(payload: dict) -> Mock:
    response = Mock()
    response.json.return_value = payload
    response.raise_for_status.return_value = None
    return response


def test_gallery_without_folder_requests_all_works() -> None:
    api = api_client()
    api.csrf_token = "csrf value"

    url = api.build_api_url(ActionType.GALLERY, "sample-user")
    folder_url = api.build_api_url(ActionType.GALLERY, "sample-user", folder_id="42")

    assert "all_folder=true" in url
    assert "csrf_token=csrf+value" in url
    assert "all_folder" not in folder_url
    assert "folderid=42" in folder_url


def test_gallery_all_folder_flag_is_pinned() -> None:
    api = api_client()
    api.csrf_token = "test-csrf"

    all_params = parse_qs(urlparse(api.build_api_url(ActionType.GALLERY, "someone")).query)
    folder_params = parse_qs(
        urlparse(api.build_api_url(ActionType.GALLERY, "someone", folder_id="12345")).query
    )

    # Without this flag the endpoint returns only the Featured folder (issue #2).
    assert all_params.get("all_folder") == ["true"]
    assert folder_params.get("folderid") == ["12345"]
    assert "all_folder" not in folder_params


def test_page_parser_accepts_snake_case_continuation() -> None:
    api = api_client()
    api.session.get = Mock(
        return_value=response_with_json(
            {"results": [deviation_payload()], "has_more": True, "next_offset": 24}
        )
    )

    items, has_more, next_offset, next_cursor = api.fetch_deviations(
        "https://example.test?offset=<OFFSET>", offset=0
    )

    assert [item.deviation_id for item in items] == ["123"]
    assert has_more is True
    assert next_offset == 24
    assert next_cursor == ""


def test_invalid_result_is_not_silently_omitted() -> None:
    api = api_client()
    api.session.get = Mock(
        return_value=response_with_json({"results": [{"title": "missing id"}], "hasMore": False})
    )

    with pytest.raises(APIError, match="offset 0"):
        api.fetch_deviations("https://example.test?offset=<OFFSET>")


def test_empty_intermediate_page_does_not_become_end_of_list() -> None:
    api = api_client()
    api.session.get = Mock(
        return_value=response_with_json({"results": [], "hasMore": True, "nextOffset": 24})
    )

    items, has_more, next_offset, _ = api.fetch_deviations(
        "https://example.test?offset=<OFFSET>", offset=0
    )

    assert items == []
    assert has_more is True
    assert next_offset == 24


def test_final_page_accepts_null_continuation() -> None:
    api = api_client()
    api.session.get = Mock(
        return_value=response_with_json(
            {"results": [deviation_payload()], "hasMore": False, "nextOffset": None}
        )
    )

    items, has_more, next_offset, _ = api.fetch_deviations(
        "https://example.test?offset=<OFFSET>", offset=60
    )

    assert len(items) == 1
    assert has_more is False
    assert next_offset == 61


def test_request_failure_is_not_reported_as_normal_completion() -> None:
    api = api_client()
    api.session.get = Mock(side_effect=RequestException("offline"))

    with pytest.raises(APIError, match="Request failed"):
        api.fetch_deviations("https://example.test?offset=<OFFSET>")


def test_model_accepts_official_api_field_names() -> None:
    payload = deviation_payload()
    payload["deviationid"] = payload.pop("deviationId")
    payload["is_downloadable"] = payload.pop("isDownloadable")
    payload["is_mature"] = payload.pop("isMature")

    deviation = Deviation.from_api_response(payload)

    assert deviation.deviation_id == "123"
    assert deviation.is_downloadable is False
