"""DeviantArt Downloader — a reliable, focused downloader and archival CLI."""

__version__ = "4.0.1"
__author__ = "DeviantArt Downloader Team"

from .download import Downloader, build_downloader, normalize_quality
from .errors import DeviantArtError
from .models import DownloadItem, MediaAsset, ResolvedDeviation

__all__ = [
    "Downloader",
    "build_downloader",
    "normalize_quality",
    "DownloadItem",
    "MediaAsset",
    "ResolvedDeviation",
    "DeviantArtError",
]
