"""Async downloader implementation - simplified for testing"""

import logging
from pathlib import Path
from typing import Optional

from ..models.config import AppConfig
from ..models.deviation import Deviation
from ..models.download import DownloadTask, DownloadResult, DownloadStatus

logger = logging.getLogger(__name__)


class DeviantArtDownloader:
    """
    Async DeviantArt downloader.

    This is a simplified implementation for the v3.0 architecture demonstration.
    Full implementation will include:
    - Concurrent download queue
    - Progress tracking
    - Database integration
    - Resume capability
    """

    def __init__(self, config: AppConfig):
        self.config = config
        logger.info(f"DeviantArtDownloader initialized with config: {config}")

    async def __aenter__(self):
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()

    async def close(self):
        """Cleanup resources"""
        pass

    async def download_gallery(
        self, 
        username: str, 
        folder_id: Optional[str] = None
    ) -> list[DownloadResult]:
        """
        Download gallery (placeholder implementation).

        Args:
            username: DeviantArt username
            folder_id: Optional folder ID

        Returns:
            List of download results
        """
        logger.info(f"Downloading gallery for {username}, folder={folder_id}")
        return []

    async def download_search(
        self, 
        username: str, 
        query: str
    ) -> list[DownloadResult]:
        """
        Download search results (placeholder).

        Args:
            username: DeviantArt username or 'all'
            query: Search query

        Returns:
            List of download results
        """
        logger.info(f"Searching {username} for '{query}'")
        return []

    async def download_favorites(
        self, 
        username: str, 
        folder_id: str
    ) -> list[DownloadResult]:
        """
        Download favorites (placeholder).

        Args:
            username: DeviantArt username
            folder_id: Favorites folder ID

        Returns:
            List of download results
        """
        logger.info(f"Downloading favorites for {username}, folder={folder_id}")
        return []
