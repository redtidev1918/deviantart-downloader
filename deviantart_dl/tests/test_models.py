"""Tests for Pydantic models"""

import pytest
from pydantic import ValidationError

from ..models.config import AppConfig, DownloadQuality
from ..models.deviation import Deviation, DeviationType, MediaInfo
from ..models.download import DownloadTask, DownloadResult, DownloadStatus


class TestAppConfig:
    """Test AppConfig model"""

    def test_default_config(self):
        """Test default configuration"""
        config = AppConfig()

        assert config.quality == DownloadQuality.ORIGINAL
        assert config.ask_before_download is False
        assert config.concurrent_downloads == 3
        assert config.timeout == 30
        assert config.max_retries == 3

    def test_config_validation(self):
        """Test configuration validation"""
        # Valid config
        config = AppConfig(timeout=60, max_retries=5)
        assert config.timeout == 60
        assert config.max_retries == 5

        # Invalid timeout (out of range)
        with pytest.raises(ValidationError):
            AppConfig(timeout=500)  # > 300

        # Invalid retries (out of range)
        with pytest.raises(ValidationError):
            AppConfig(max_retries=20)  # > 10

    def test_proxy_validation(self):
        """Test proxy URL validation"""
        # Valid proxies
        config = AppConfig(proxy="http://127.0.0.1:8080")
        assert config.proxy == "http://127.0.0.1:8080"

        config = AppConfig(proxy="https://proxy.example.com:3128")
        assert config.proxy == "https://proxy.example.com:3128"

        # Invalid proxy (no protocol)
        with pytest.raises(ValidationError):
            AppConfig(proxy="127.0.0.1:8080")

    def test_path_resolution(self, tmp_path):
        """Test path resolution and expansion"""
        config = AppConfig(
            destination=tmp_path / "downloads",
            cookies_file=tmp_path / "cookies.txt",
        )

        assert config.destination.is_absolute()
        assert config.cookies_file.is_absolute()

    def test_get_headers(self):
        """Test header generation"""
        config = AppConfig()
        headers = config.get_headers("test_cookie=value")

        assert "Cookie" in headers
        assert headers["Cookie"] == "test_cookie=value"
        assert "User-Agent" in headers

    def test_get_proxies(self):
        """Test proxy configuration"""
        # With proxy
        config = AppConfig(proxy="http://127.0.0.1:8080")
        proxies = config.get_proxies()

        assert proxies is not None
        assert "http://" in proxies
        assert "https://" in proxies

        # Without proxy
        config = AppConfig(proxy=None)
        proxies = config.get_proxies()

        assert proxies is None


class TestMediaInfo:
    """Test MediaInfo model"""

    def test_media_info_creation(self):
        """Test MediaInfo creation"""
        media = MediaInfo(
            base_uri="https://images.example.com/test.jpg",
            pretty_name="test_image",
            token=["token123"],
            types=[
                {"t": "fullview", "c": "/f/<prettyName>.jpg"},
                {"t": "preview", "c": "/p/<prettyName>.jpg"},
            ],
        )

        assert str(media.base_uri) == "https://images.example.com/test.jpg"
        assert media.pretty_name == "test_image"
        assert media.has_token is True

    def test_get_type(self):
        """Test getting media type"""
        media = MediaInfo(
            base_uri="https://example.com/test.jpg",
            pretty_name="test",
            types=[
                {"t": "fullview", "c": "/full.jpg"},
                {"t": "preview", "c": "/preview.jpg"},
            ],
        )

        fullview = media.get_type("fullview")
        assert fullview is not None
        assert fullview["c"] == "/full.jpg"

        preview = media.get_type("preview")
        assert preview is not None

        unknown = media.get_type("unknown")
        assert unknown is None


class TestDeviation:
    """Test Deviation model"""

    def test_deviation_creation(self):
        """Test Deviation creation"""
        deviation = Deviation(
            deviation_id="123",
            title="Test Art",
            url="https://www.deviantart.com/user/art/test-123",
            author="testuser",
            deviation_type=DeviationType.IMAGE,
            is_downloadable=True,
        )

        assert deviation.deviation_id == "123"
        assert deviation.title == "Test Art"
        assert deviation.author == "testuser"
        assert deviation.deviation_type == DeviationType.IMAGE

    def test_from_api_response(self):
        """Test creating Deviation from API response"""
        api_data = {
            "deviationId": "456",
            "title": "API Test",
            "url": "https://www.deviantart.com/user/art/api-456",
            "author": {"username": "apiuser"},
            "type": "image",
            "isDownloadable": True,
            "isMature": False,
            "stats": {"comments": 10, "favourites": 50},
        }

        deviation = Deviation.from_api_response(api_data)

        assert deviation.deviation_id == "456"
        assert deviation.title == "API Test"
        assert deviation.author == "apiuser"
        assert deviation.stats_comments == 10
        assert deviation.stats_favourites == 50

    def test_deviation_type_normalization(self):
        """Test deviation type normalization"""
        # Image types
        for type_str in ["image", "deviation", "IMAGE"]:
            dev = Deviation(
                deviation_id="1",
                title="Test",
                url="https://example.com",
                author="user",
                deviation_type=type_str,
            )
            assert dev.deviation_type == DeviationType.IMAGE

        # Literature
        dev = Deviation(
            deviation_id="1",
            title="Story",
            url="https://example.com",
            author="user",
            deviation_type="literature",
        )
        assert dev.deviation_type == DeviationType.LITERATURE

    def test_is_downloadable_type(self):
        """Test downloadable type check"""
        # Image is downloadable
        dev = Deviation(
            deviation_id="1",
            title="Image",
            url="https://example.com",
            author="user",
            deviation_type=DeviationType.IMAGE,
        )
        assert dev.is_downloadable_type is True

        # Literature is not downloadable
        dev = Deviation(
            deviation_id="2",
            title="Story",
            url="https://example.com",
            author="user",
            deviation_type=DeviationType.LITERATURE,
        )
        assert dev.is_downloadable_type is False

    def test_get_file_extension(self):
        """Test file extension extraction"""
        # From media URI
        deviation = Deviation(
            deviation_id="1",
            title="Test",
            url="https://example.com",
            author="user",
            media=MediaInfo(
                base_uri="https://images.example.com/art.png",
                pretty_name="test_art",
            ),
        )
        assert deviation.get_file_extension() == ".png"

        # Without media
        deviation = Deviation(
            deviation_id="2",
            title="Test",
            url="https://example.com",
            author="user",
        )
        assert deviation.get_file_extension() == ".jpg"  # Default

    def test_string_representation(self):
        """Test string representations"""
        deviation = Deviation(
            deviation_id="123",
            title="Test Art",
            url="https://example.com",
            author="testuser",
            is_mature=True,
            is_downloadable=True,
        )

        str_repr = str(deviation)
        assert "Test Art" in str_repr
        assert "testuser" in str_repr
        assert "MATURE" in str_repr
        assert "DL" in str_repr

        repr_repr = repr(deviation)
        assert "Deviation" in repr_repr
        assert "123" in repr_repr


class TestDownloadTask:
    """Test DownloadTask model"""

    def test_task_creation(self, mock_deviation, tmp_path):
        """Test task creation"""
        task = DownloadTask(
            deviation=mock_deviation,
            quality=DownloadQuality.FULL,
            destination=tmp_path,
        )

        assert task.deviation == mock_deviation
        assert task.quality == DownloadQuality.FULL
        assert task.priority == 0

    def test_file_path_generation(self, mock_deviation, tmp_path):
        """Test file path generation"""
        task = DownloadTask(
            deviation=mock_deviation,
            quality=DownloadQuality.FULL,
            destination=tmp_path,
        )

        file_path = task.file_path
        assert file_path.parent == tmp_path
        assert "test_artwork" in file_path.name

    def test_file_exists_check(self, mock_deviation, tmp_path):
        """Test file existence check"""
        task = DownloadTask(
            deviation=mock_deviation,
            quality=DownloadQuality.FULL,
            destination=tmp_path,
        )

        # File doesn't exist
        assert task.file_exists is False

        # Create file
        task.file_path.touch()
        assert task.file_exists is True

    def test_task_priority_sorting(self, mock_deviation, tmp_path):
        """Test task sorting by priority"""
        task1 = DownloadTask(
            deviation=mock_deviation,
            quality=DownloadQuality.FULL,
            destination=tmp_path,
            priority=1,
        )

        task2 = DownloadTask(
            deviation=mock_deviation,
            quality=DownloadQuality.FULL,
            destination=tmp_path,
            priority=5,
        )

        # Higher priority should come first
        tasks = sorted([task1, task2])
        assert tasks[0].priority == 1
        assert tasks[1].priority == 5


class TestDownloadResult:
    """Test DownloadResult model"""

    def test_result_creation(self, mock_deviation, tmp_path):
        """Test result creation"""
        task = DownloadTask(
            deviation=mock_deviation,
            quality=DownloadQuality.FULL,
            destination=tmp_path,
        )

        result = DownloadResult(
            task=task,
            status=DownloadStatus.SUCCESS,
            file_path=tmp_path / "test.jpg",
            file_size=1024 * 1024,  # 1 MB
        )

        assert result.is_success is True
        assert result.is_failed is False
        assert result.file_size_mb == 1.0

    def test_result_status_checks(self, mock_deviation, tmp_path):
        """Test status check properties"""
        task = DownloadTask(
            deviation=mock_deviation,
            quality=DownloadQuality.FULL,
            destination=tmp_path,
        )

        # Success
        result = DownloadResult(task=task, status=DownloadStatus.SUCCESS)
        assert result.is_success is True
        assert result.is_failed is False
        assert result.is_skipped is False

        # Failed
        result = DownloadResult(task=task, status=DownloadStatus.FAILED)
        assert result.is_success is False
        assert result.is_failed is True

        # Skipped
        result = DownloadResult(task=task, status=DownloadStatus.SKIPPED)
        assert result.is_skipped is True

    def test_result_to_dict(self, mock_deviation, tmp_path):
        """Test converting result to dictionary"""
        task = DownloadTask(
            deviation=mock_deviation,
            quality=DownloadQuality.FULL,
            destination=tmp_path,
        )

        result = DownloadResult(
            task=task,
            status=DownloadStatus.SUCCESS,
            file_path=tmp_path / "test.jpg",
            file_size=2048,
        )

        data = result.to_dict()

        assert "deviation_id" in data
        assert "title" in data
        assert "author" in data
        assert "status" in data
        assert data["status"] == "success"
        assert data["file_size"] == 2048

    def test_result_string_representation(self, mock_deviation, tmp_path):
        """Test string representation"""
        task = DownloadTask(
            deviation=mock_deviation,
            quality=DownloadQuality.FULL,
            destination=tmp_path,
        )

        # Success
        result = DownloadResult(
            task=task,
            status=DownloadStatus.SUCCESS,
            file_size=1024 * 1024,
        )
        assert "✓" in str(result)
        assert "Test Artwork" in str(result)

        # Failed
        result = DownloadResult(
            task=task,
            status=DownloadStatus.FAILED,
            error_message="Network error",
        )
        assert "✗" in str(result)
        assert "Network error" in str(result)

        # Skipped
        result = DownloadResult(
            task=task,
            status=DownloadStatus.SKIPPED,
        )
        assert "⊘" in str(result)
