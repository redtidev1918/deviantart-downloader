"""Regression tests for the installed CLI and stable batch downloader."""

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from requests import RequestException

from da_downloader.api import APIError, DeviantArtAPI
from da_downloader.cli import main as cli_main
from da_downloader.downloader import DeviantArtDownloader
from da_downloader.models import (
    ActionType,
    Deviation,
    DownloadResult,
)
from da_downloader.progress import ProgressManager


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


def test_page_parser_accepts_snake_case_continuation() -> None:
    api = api_client()
    api.session.get = Mock(
        return_value=response_with_json(
            {
                "results": [deviation_payload()],
                "has_more": True,
                "next_offset": 24,
            }
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
        return_value=response_with_json(
            {"results": [{"title": "missing id"}], "hasMore": False}
        )
    )

    with pytest.raises(APIError, match="offset 0"):
        api.fetch_deviations("https://example.test?offset=<OFFSET>")


def test_empty_intermediate_page_does_not_become_end_of_list() -> None:
    api = api_client()
    api.session.get = Mock(
        return_value=response_with_json(
            {"results": [], "hasMore": True, "nextOffset": 24}
        )
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


def test_progress_requires_the_recorded_file_to_exist(tmp_path: Path) -> None:
    progress = ProgressManager("gallery_user_all", progress_dir=tmp_path)
    missing = tmp_path / "deleted.jpg"
    progress.mark_downloaded("123", str(missing))
    assert progress.is_downloaded("123") is False

    missing.write_bytes(b"image")
    assert progress.is_downloaded("123") is True


def test_corrupt_progress_file_recovers_without_recursion(tmp_path: Path) -> None:
    progress_file = tmp_path / "gallery_user_all.json"
    progress_file.write_text("{not-json", encoding="utf-8")

    progress = ProgressManager("gallery_user_all", progress_dir=tmp_path)

    assert progress.get_stats() == {
        "downloaded": 0,
        "failed": 0,
        "skipped": 0,
        "total": 0,
    }


def test_downloader_continues_after_an_empty_intermediate_page(tmp_path: Path) -> None:
    deviation = Deviation.from_api_response(deviation_payload())
    downloader = DeviantArtDownloader.__new__(DeviantArtDownloader)
    downloader.config = SimpleNamespace(
        offset=0,
        lazy_load_limit=24,
        replace_existing=False,
        quality="f",
        delay_seconds=0,
        ask_before_download=False,
    )
    downloader.api = Mock()
    downloader.api.fetch_deviations.side_effect = [
        ([], True, 24, ""),
        ([deviation], False, 25, ""),
    ]
    downloader.progress = ProgressManager("gallery_user_all", progress_dir=tmp_path)
    downloader.download_all = False
    downloader.total_downloaded = 0
    downloader.total_failed = 0
    downloader.total_skipped = 0
    downloader._get_destination_folder = Mock(return_value=str(tmp_path))
    downloader._download_single = Mock(
        side_effect=lambda task: DownloadResult(
            task=task,
            success=False,
            error="temporary failure",
        )
    )

    downloader._download_from_url(
        "https://example.test?offset=<OFFSET>&limit=<LIMIT>", "user"
    )

    assert downloader.api.fetch_deviations.call_count == 2
    assert downloader._download_single.call_count == 1
    assert downloader.progress.is_failed("123") is True
    assert downloader.progress.progress_file.exists()


def test_cli_version_is_importable(capsys: pytest.CaptureFixture[str]) -> None:
    assert cli_main(["--version"]) == 0
    assert "devart-dl 3.4.0" in capsys.readouterr().out


def test_model_accepts_official_api_field_names() -> None:
    payload = deviation_payload()
    payload["deviationid"] = payload.pop("deviationId")
    payload["is_downloadable"] = payload.pop("isDownloadable")
    payload["is_mature"] = payload.pop("isMature")

    deviation = Deviation.from_api_response(payload)

    assert deviation.deviation_id == "123"
    assert deviation.is_downloadable is False
