"""
DeviantArt Downloader

Modern, async, fully-tested DeviantArt media downloader.

Features:
- Async downloads with httpx
- Pydantic data validation
- SQLite database for history
- Rich CLI interface
- Comprehensive test suite
- Type-safe with mypy

Requires Python 3.10+
"""

__version__ = "3.0.0"
__author__ = "DeviantArt Downloader Team"

from .core.downloader import DeviantArtDownloader
from .models.config import AppConfig
from .models.deviation import Deviation

__all__ = ["DeviantArtDownloader", "AppConfig", "Deviation"]
