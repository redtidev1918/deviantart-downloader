"""
DeviantArt Downloader (deprecated package).

This package was an early async prototype and is now deprecated in favour of the
canonical ``da_downloader`` package, which contains the maintained CLI, the
``Downloader`` facade, and the provider/downloader layers. Please import from
``da_downloader`` instead:

    from da_downloader import Downloader
    from da_downloader.download import build_downloader

This module is kept only as a compatibility shim and will be removed in a
future major release.
"""

__version__ = "3.4.0"
__author__ = "DeviantArt Downloader Team"

from .core.downloader import DeviantArtDownloader
from .models.config import AppConfig
from .models.deviation import Deviation

__all__ = ["DeviantArtDownloader", "AppConfig", "Deviation"]
