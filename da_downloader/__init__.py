"""DeviantArt Downloader — a reliable, focused downloader and archival CLI."""

__version__ = "3.4.0"
__author__ = "DeviantArt Downloader Team"

from .download import Downloader, build_downloader, normalize_quality
from .errors import DeviantArtError
from .models import DownloadItem

__all__ = [
    "Downloader",
    "build_downloader",
    "normalize_quality",
    "DownloadItem",
    "DeviantArtError",
]
