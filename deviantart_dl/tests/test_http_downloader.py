"""Tests for the reliable HTTP downloader (streaming, Range resume, validation)."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import pytest
from requests.exceptions import RequestException

from da_downloader.errors import AuthenticationError, DownloadError, NetworkError, RateLimitError
from da_downloader.http import HttpDownloader


class FakeResponse:
    def __init__(
        self,
        status_code: int,
        content: bytes = b"",
        headers: Optional[dict] = None,
    ) -> None:
        self.status_code = status_code
        self._content = content
        self.headers = headers or {}
        self._closed = False

    def iter_content(self, chunk_size: int):
        for i in range(0, len(self._content), chunk_size):
            yield self._content[i : i + chunk_size]

    def close(self) -> None:
        self._closed = True

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *args) -> bool:
        self.close()
        return False


class FakeSession:
    def __init__(self, responses=None, errors=None) -> None:
        self.responses = list(responses or [])
        self.errors = list(errors or [])
        self.calls = []

    def get(self, url, stream=True, headers=None, timeout=None):
        self.calls.append({"url": url, "headers": headers or {}, "timeout": timeout})
        if self.errors:
            raise self.errors.pop(0)
        return self.responses.pop(0)


def make_downloader(session: FakeSession, **kwargs) -> HttpDownloader:
    kwargs.setdefault("retry_backoff", 0.0)
    kwargs.setdefault("max_backoff", 0.0)
    return HttpDownloader(session=session, **kwargs)


def test_downloads_full_content(tmp_path: Path) -> None:
    session = FakeSession(responses=[FakeResponse(200, b"abcdef")])
    downloader = make_downloader(session)
    target = tmp_path / "art.jpg"

    result = downloader.download("https://example.test/art.jpg", target)

    assert result.path == target
    assert result.size == 6
    assert result.resumed is False
    assert target.read_bytes() == b"abcdef"
    assert not (tmp_path / "art.jpg.part").exists()


def test_skips_existing_file_without_overwrite(tmp_path: Path) -> None:
    session = FakeSession()
    target = tmp_path / "art.jpg"
    target.write_bytes(b"existing")
    downloader = make_downloader(session)

    result = downloader.download("https://example.test/art.jpg", target)

    assert result.size == len(b"existing")
    assert session.calls == []  # no HTTP request made


def test_resumes_partial_download(tmp_path: Path) -> None:
    target = tmp_path / "art.jpg"
    (tmp_path / "art.jpg.part").write_bytes(b"abc")
    session = FakeSession(
        responses=[FakeResponse(206, b"def", {"Content-Range": "bytes 3-5/6"})]
    )
    downloader = make_downloader(session)

    result = downloader.download("https://example.test/art.jpg", target)

    assert result.resumed is True
    assert target.read_bytes() == b"abcdef"
    assert session.calls[0]["headers"]["Range"] == "bytes=3-"


def test_416_finalizes_complete_part(tmp_path: Path) -> None:
    target = tmp_path / "art.jpg"
    (tmp_path / "art.jpg.part").write_bytes(b"abcdef")
    session = FakeSession(responses=[FakeResponse(416)])
    downloader = make_downloader(session)

    result = downloader.download("https://example.test/art.jpg", target)

    assert result.resumed is True
    assert target.read_bytes() == b"abcdef"


def test_connection_error_retries_then_succeeds(tmp_path: Path) -> None:
    target = tmp_path / "art.jpg"
    session = FakeSession(
        responses=[FakeResponse(200, b"ok")], errors=[RequestException("offline")]
    )
    downloader = make_downloader(session)

    result = downloader.download("https://example.test/art.jpg", target)

    assert result.size == 2
    assert len(session.calls) == 2


def test_connection_error_exhausts_retries(tmp_path: Path) -> None:
    session = FakeSession(errors=[RequestException("offline")] * 2)
    downloader = make_downloader(session, max_retries=1)

    with pytest.raises(NetworkError):
        downloader.download("https://example.test/art.jpg", tmp_path / "art.jpg")
    assert len(session.calls) == 2  # initial + one retry


def test_429_retry_after_then_succeeds(tmp_path: Path) -> None:
    session = FakeSession(
        responses=[
            FakeResponse(429, headers={"Retry-After": "0"}),
            FakeResponse(200, b"ok"),
        ]
    )
    downloader = make_downloader(session, max_retries=2)

    result = downloader.download("https://example.test/art.jpg", tmp_path / "art.jpg")

    assert result.size == 2
    assert [c["url"] for c in session.calls].count("https://example.test/art.jpg") == 2


def test_429_exhausts_retries_raises_rate_limit(tmp_path: Path) -> None:
    session = FakeSession(responses=[FakeResponse(429)] * 2)
    downloader = make_downloader(session, max_retries=1)

    with pytest.raises(RateLimitError):
        downloader.download("https://example.test/art.jpg", tmp_path / "art.jpg")


def test_5xx_retries_then_succeeds(tmp_path: Path) -> None:
    session = FakeSession(
        responses=[FakeResponse(500), FakeResponse(200, b"ok")]
    )
    downloader = make_downloader(session)

    result = downloader.download("https://example.test/art.jpg", tmp_path / "art.jpg")
    assert result.size == 2


def test_404_is_permanent(tmp_path: Path) -> None:
    session = FakeSession(responses=[FakeResponse(404)])
    downloader = make_downloader(session)

    with pytest.raises(DownloadError, match="404"):
        downloader.download("https://example.test/art.jpg", tmp_path / "art.jpg")
    assert len(session.calls) == 1  # no retry on permanent failure


def test_401_raises_authentication_error(tmp_path: Path) -> None:
    session = FakeSession(responses=[FakeResponse(401)])
    downloader = make_downloader(session)

    with pytest.raises(AuthenticationError):
        downloader.download("https://example.test/art.jpg", tmp_path / "art.jpg")


def test_html_response_is_rejected(tmp_path: Path) -> None:
    session = FakeSession(
        responses=[FakeResponse(200, b"<html>login</html>", {"Content-Type": "text/html"})]
    )
    downloader = make_downloader(session)

    with pytest.raises(DownloadError, match="HTML"):
        downloader.download("https://example.test/art.jpg", tmp_path / "art.jpg")
    assert not (tmp_path / "art.jpg").exists()


def test_empty_response_is_rejected(tmp_path: Path) -> None:
    session = FakeSession(responses=[FakeResponse(200, b"", {"Content-Length": "0"})])
    downloader = make_downloader(session)

    with pytest.raises(DownloadError, match="empty"):
        downloader.download("https://example.test/art.jpg", tmp_path / "art.jpg")


def test_incomplete_content_length_is_rejected(tmp_path: Path) -> None:
    session = FakeSession(
        responses=[FakeResponse(200, b"abc", {"Content-Length": "10"})]
    )
    downloader = make_downloader(session)

    with pytest.raises(DownloadError, match="incomplete"):
        downloader.download("https://example.test/art.jpg", tmp_path / "art.jpg")
    # The partial file is retained for a later resume.
    assert (tmp_path / "art.jpg.part").exists()


def test_server_ignoring_range_restarts(tmp_path: Path) -> None:
    target = tmp_path / "art.jpg"
    (tmp_path / "art.jpg.part").write_bytes(b"stale")
    session = FakeSession(responses=[FakeResponse(200, b"abcdef")])
    downloader = make_downloader(session)

    result = downloader.download("https://example.test/art.jpg", target)

    assert result.resumed is False
    assert target.read_bytes() == b"abcdef"  # truncated and rewritten from scratch


def test_backoff_caps_at_maximum() -> None:
    downloader = HttpDownloader(session=FakeSession(), retry_backoff=1.0, max_backoff=8.0)
    assert downloader._backoff(1) == 1.0
    assert downloader._backoff(2) == 2.0
    assert downloader._backoff(3) == 4.0
    assert downloader._backoff(10) == 8.0
