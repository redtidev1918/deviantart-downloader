"""Small, typed error hierarchy for the downloader.

Deliberately limited to the categories that actually change control flow
(skip vs. retry vs. fail) so callers never have to string-match error text.
"""

from __future__ import annotations


class DeviantArtError(Exception):
    """Base class for all downloader errors."""

    def __init__(self, message: str, *, code: str | None = None) -> None:
        super().__init__(message)
        self.code = code or type(self).__name__


class AuthenticationError(DeviantArtError):
    """Credentials are missing, expired, or lack permission (401/403)."""


class NetworkError(DeviantArtError):
    """A connection or timeout failure; may be transient."""


class RateLimitError(DeviantArtError):
    """The server rate-limited the request (429)."""


class ParseError(DeviantArtError):
    """A response could not be parsed into the expected shape."""


class MediaUnavailableError(DeviantArtError):
    """The media exists but cannot be downloaded (premium, restricted, …)."""


class DownloadError(DeviantArtError):
    """A file download failed or produced an invalid result."""


class FilesystemError(DeviantArtError):
    """A local file could not be read or written."""
