"""Reliable HTTP file download: streaming, ``.part`` files, Range resume, and
response validation.

This module knows nothing about DeviantArt, gallery pagination, OAuth, or CSRF.
Its only job is to move bytes from a URL to a file without corrupting them:
stream to a ``.part`` file, resume partial transfers via HTTP Range, retry
transient failures, and refuse to save HTML/empty responses as media.
"""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Optional

import requests
from requests.exceptions import RequestException

from .errors import (
    AuthenticationError,
    DeviantArtError,
    DownloadError,
    NetworkError,
    RateLimitError,
)

logger = logging.getLogger(__name__)

DEFAULT_CHUNK_SIZE = 64 * 1024  # 64 KiB
_HTML_CONTENT_TYPES = ("text/html", "application/xhtml+xml")
_RETRYABLE_STATUS = frozenset({429, 500, 502, 503, 504})


@dataclass(frozen=True)
class TransferResult:
    """Outcome of a successful download."""

    path: Path
    size: int
    resumed: bool = False


class HttpDownloader:
    """Downloads a single URL to a file with resume and validation."""

    def __init__(
        self,
        session: Optional[requests.Session] = None,
        *,
        max_retries: int = 3,
        retry_backoff: float = 1.0,
        max_backoff: float = 8.0,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        timeout: float = 60.0,
    ) -> None:
        self.session = session or requests.Session()
        self.max_retries = max_retries
        self.retry_backoff = retry_backoff
        self.max_backoff = max_backoff
        self.chunk_size = chunk_size
        self.timeout = timeout

    def download(
        self,
        url: str,
        destination: Path,
        *,
        overwrite: bool = False,
        headers: Optional[Mapping[str, str]] = None,
        timeout: Optional[float] = None,
    ) -> TransferResult:
        """Download ``url`` to ``destination``, returning the saved file info.

        Raises ``AuthenticationError``/``DownloadError``/``NetworkError``/
        ``RateLimitError`` on failure. A failed attempt keeps the ``.part``
        file so a later call can resume instead of starting over.
        """
        target = Path(destination)
        if target.exists() and not overwrite:
            return TransferResult(target, target.stat().st_size)

        target.parent.mkdir(parents=True, exist_ok=True)
        part = target.with_name(target.name + ".part")
        request_headers = dict(headers or {})
        request_headers.setdefault("Accept", "*/*")
        timeout = timeout if timeout is not None else self.timeout

        attempt = 0
        while True:
            part_size = part.stat().st_size if part.exists() else 0
            headers = dict(request_headers)
            if part_size:
                headers["Range"] = f"bytes={part_size}-"

            try:
                response = self.session.get(
                    url, stream=True, headers=headers, timeout=timeout
                )
            except RequestException as exc:
                if attempt >= self.max_retries:
                    raise NetworkError(
                        f"request failed after {attempt + 1} attempts: {exc}"
                    ) from exc
                attempt += 1
                delay = self._backoff(attempt)
                logger.warning(
                    "request failed (%s), retry %d/%d in %.1fs",
                    type(exc).__name__, attempt, self.max_retries, delay,
                )
                time.sleep(delay)
                continue

            with response:
                status = response.status_code
                if status in (200, 206):
                    self._validate_content_type(response, target)
                    self._stream(response, part, mode="ab" if status == 206 else "wb")
                    if part.stat().st_size == 0:
                        raise DownloadError("server returned an empty file")
                    os.replace(part, target)
                    return TransferResult(
                        target, target.stat().st_size, resumed=(status == 206)
                    )
                if status == 416 and part_size:
                    # Range not satisfiable: the partial file is already complete.
                    os.replace(part, target)
                    return TransferResult(target, target.stat().st_size, resumed=True)
                if status in _RETRYABLE_STATUS and attempt < self.max_retries:
                    attempt += 1
                    retry_after = self._retry_after(response)
                    delay = self._backoff(attempt) if retry_after is None else retry_after
                    logger.warning(
                        "HTTP %d (%s), retry %d/%d in %.1fs",
                        status, url, attempt, self.max_retries, delay,
                    )
                    time.sleep(delay)
                    continue
                raise self._error_for(status, url)

    def _validate_content_type(self, response: requests.Response, target: Path) -> None:
        content_type = (response.headers.get("Content-Type") or "").lower()
        if content_type.startswith(_HTML_CONTENT_TYPES) and target.suffix.lower() not in (".html", ".htm"):
            raise DownloadError("server returned an HTML page instead of a media file")

    def _stream(self, response: requests.Response, part: Path, mode: str) -> None:
        expected = self._expected_total(response)
        try:
            with part.open(mode) as output:
                for chunk in response.iter_content(self.chunk_size):
                    if not chunk:
                        continue
                    output.write(chunk)
        except RequestException as exc:
            raise NetworkError(f"download interrupted: {exc}") from exc
        actual = part.stat().st_size
        if expected is not None and actual != expected:
            raise DownloadError(f"incomplete download: got {actual} of {expected} bytes")

    def _expected_total(self, response: requests.Response) -> Optional[int]:
        # 206 Partial Content reports the full size in Content-Range.
        content_range = response.headers.get("Content-Range") or ""
        if content_range:
            total = content_range.rpartition("/")[2]
            if total.isdigit():
                return int(total)
        content_length = response.headers.get("Content-Length") or ""
        return int(content_length) if content_length.isdigit() else None

    def _retry_after(self, response: requests.Response) -> Optional[float]:
        value = response.headers.get("Retry-After")
        if not value:
            return None
        try:
            return float(value)
        except ValueError:
            # An HTTP-date; fall back to exponential backoff.
            return None

    def _backoff(self, attempt: int) -> float:
        return min(self.retry_backoff * (2.0 ** (attempt - 1)), self.max_backoff)

    def _error_for(self, status: int, url: str) -> DeviantArtError:
        if status == 401:
            return AuthenticationError(f"HTTP 401 unauthorized: {url}")
        if status == 403:
            return AuthenticationError(f"HTTP 403 forbidden: {url}")
        if status == 404:
            return DownloadError(f"HTTP 404 not found: {url}")
        if status == 429:
            return RateLimitError(f"HTTP 429 rate limited: {url}")
        return DownloadError(f"HTTP {status} for {url}")


__all__ = ["TransferResult", "HttpDownloader"]
