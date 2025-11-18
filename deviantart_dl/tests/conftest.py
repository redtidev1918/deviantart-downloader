"""Pytest configuration and fixtures"""

import asyncio
from pathlib import Path
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import AsyncClient

from ..models.config import AppConfig, DownloadQuality
from ..models.deviation import Deviation, DeviationType, MediaInfo


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_dir(tmp_path: Path) -> Path:
    """Create temporary directory for tests"""
    test_dir = tmp_path / "test_downloads"
    test_dir.mkdir(exist_ok=True)
    return test_dir


@pytest.fixture
def mock_config(temp_dir: Path) -> AppConfig:
    """Create mock configuration for tests"""
    return AppConfig(
        destination=temp_dir,
        cookies_file=temp_dir / "cookies.txt",
        database_path=temp_dir / "test.db",
        quality=DownloadQuality.FULL,
        ask_before_download=False,
        replace_existing=True,
        concurrent_downloads=2,
        timeout=10,
        max_retries=1,
        rate_limit_delay=0,  # No delay in tests
        dry_run=False,
    )


@pytest.fixture
def mock_deviation() -> Deviation:
    """Create mock deviation for tests"""
    return Deviation(
        deviation_id="123456",
        title="Test Artwork",
        url="https://www.deviantart.com/test/art/test-123456",
        author="testuser",
        media=MediaInfo(
            base_uri="https://images-wixmp-test.com/test.jpg",
            pretty_name="test_artwork",
            token=["test_token"],
            types=[
                {"t": "fullview", "c": "/intermediary/f/<prettyName>.jpg"},
                {"t": "preview", "c": "/preview/<prettyName>.jpg"},
            ],
        ),
        deviation_type=DeviationType.IMAGE,
        is_downloadable=True,
        is_mature=False,
    )


@pytest.fixture
def mock_api_response() -> dict:
    """Create mock API response"""
    return {
        "results": [
            {
                "deviationId": "123",
                "title": "Artwork 1",
                "url": "https://www.deviantart.com/user/art/artwork-1-123",
                "author": {"username": "testuser"},
                "media": {
                    "baseUri": "https://images-test.com/art1.jpg",
                    "prettyName": "artwork_1",
                    "token": ["token1"],
                    "types": [{"t": "preview", "c": "/<prettyName>.jpg"}],
                },
                "type": "image",
                "isDownloadable": True,
                "isMature": False,
            },
            {
                "deviationId": "456",
                "title": "Artwork 2",
                "url": "https://www.deviantart.com/user/art/artwork-2-456",
                "author": {"username": "testuser"},
                "media": {
                    "baseUri": "https://images-test.com/art2.jpg",
                    "prettyName": "artwork_2",
                    "token": [],
                    "types": [{"t": "fullview", "c": "/f/<prettyName>.jpg"}],
                },
                "type": "image",
                "isDownloadable": False,
                "isMature": True,
            },
        ],
        "hasMore": False,
        "nextOffset": 2,
    }


@pytest.fixture
def mock_cookies() -> str:
    """Create mock cookies string"""
    return "auth=test_auth; auth_secure=test_secure; userinfo=test_user"


@pytest_asyncio.fixture
async def mock_http_client() -> AsyncGenerator[AsyncClient, None]:
    """Create mock HTTP client"""
    async with AsyncClient() as client:
        yield client
