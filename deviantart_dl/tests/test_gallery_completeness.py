"""Regression tests for gallery completeness (issue #2).

The gallery endpoint only returns the Featured folder unless the request
carries all_folder=true. These tests pin that behavior in the URL builder,
plus an opt-in live check.
"""

from __future__ import annotations

from urllib.parse import parse_qs, urlparse

import pytest

from da_downloader.api import DeviantArtAPI
from da_downloader.models import ActionType

HEADERS = {"user-agent": "test-agent"}
PROXIES: dict[str, str] = {}


def make_api() -> DeviantArtAPI:
    api = DeviantArtAPI(headers=HEADERS, proxies=PROXIES)
    api.csrf_token = "test-csrf"
    return api


def build_query(api: DeviantArtAPI, **kwargs) -> dict[str, list[str]]:
    url = api.build_api_url(ActionType.GALLERY, "someone", **kwargs)
    return parse_qs(urlparse(url).query)


class TestGalleryAllFolders:
    def test_gallery_without_folder_requests_all_folders(self):
        # Without this flag the endpoint returns only the Featured folder,
        # silently skipping works in other gallery folders (issue #2).
        params = build_query(make_api())
        assert params.get("all_folder") == ["true"]

    def test_specific_folder_omits_all_folder_flag(self):
        params = build_query(make_api(), folder_id="12345")
        assert "all_folder" not in params
        assert params.get("folderid") == ["12345"]

    def test_gallery_request_contains_username_and_type(self):
        params = build_query(make_api())
        assert params.get("username") == ["someone"]
        assert params.get("type") == ["gallery"]
        assert params.get("csrf_token") == ["test-csrf"]


@pytest.mark.integration
class TestLiveGalleryEndpoint:
    # Hits the real DeviantArt API. Run explicitly with: pytest -m integration

    LIVE_USER = "Aenea-Jones"

    def test_all_folder_requests_are_accepted_and_differ_from_featured(self):
        import re

        import requests

        session = requests.Session()
        session.headers.update(HEADERS)
        page = session.get(
            f"https://www.deviantart.com/{self.LIVE_USER}", timeout=30
        )
        match = re.search(r"window\.__CSRF_TOKEN__ = '([^']+)'", page.text)
        assert match, "CSRF token not found on profile page"

        def first_page_ids(extra: str) -> set[str]:
            url = (
                "https://www.deviantart.com/_puppy/dashared/gallection/contents"
                f"?csrf_token={match.group(1)}&username={self.LIVE_USER}"
                f"&type=gallery&offset=0&limit=24{extra}"
            )
            response = session.get(url, timeout=30)
            assert response.status_code == 200, response.text[:200]
            payload = response.json()
            assert "errorCode" not in payload, payload
            return {item["deviationId"] for item in payload["results"]}

        featured = first_page_ids("")
        everything = first_page_ids("&all_folder=true")
        # Featured-only must not see works that all_folder reveals.
        assert everything - featured, (
            "all_folder=true returned no works outside Featured"
        )
