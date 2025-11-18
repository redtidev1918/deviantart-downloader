"""Application configuration using Pydantic Settings"""

from enum import Enum
from pathlib import Path
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DownloadQuality(str, Enum):
    """Download quality levels"""

    ORIGINAL = "original"
    FULL = "full"
    PREVIEW = "preview"


class AppConfig(BaseSettings):
    """
    Application configuration with validation.

    Can be loaded from:
    - Environment variables (DA_*)
    - .env file
    - config.yaml
    - Command line arguments
    """

    model_config = SettingsConfigDict(
        env_prefix="DA_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Download settings
    quality: DownloadQuality = Field(
        default=DownloadQuality.ORIGINAL,
        description="Download quality (original/full/preview)",
    )

    ask_before_download: bool = Field(
        default=False, description="Ask before each download"
    )

    replace_existing: bool = Field(
        default=False, description="Replace existing files"
    )

    separate_folders: bool = Field(
        default=True, description="Create separate folders per artist"
    )

    # Path settings
    destination: Path = Field(
        default=Path("downloads"), description="Download destination folder"
    )

    cookies_file: Path = Field(
        default=Path("cookies.txt"), description="Path to cookies file"
    )

    database_path: Path = Field(
        default=Path("downloads.db"), description="SQLite database path"
    )

    # Network settings
    proxy: Optional[str] = Field(default=None, description="HTTP/HTTPS proxy URL")

    timeout: int = Field(default=30, ge=1, le=300, description="Request timeout in seconds")

    max_retries: int = Field(default=3, ge=0, le=10, description="Maximum retry attempts")

    retry_delay: float = Field(
        default=2.0, ge=0.1, le=60.0, description="Delay between retries (seconds)"
    )

    # Performance settings
    concurrent_downloads: int = Field(
        default=3, ge=1, le=10, description="Number of concurrent downloads"
    )

    rate_limit_delay: float = Field(
        default=1.0, ge=0.0, le=10.0, description="Delay between requests (seconds)"
    )

    # API settings
    lazy_load_limit: int = Field(
        default=24, ge=1, le=60, description="Items per API request"
    )

    offset: int = Field(default=0, ge=0, description="Starting offset")

    # Logging settings
    log_level: str = Field(default="INFO", description="Logging level")

    log_file: Optional[Path] = Field(default=None, description="Log file path")

    verbose: bool = Field(default=False, description="Verbose output")

    # Debug settings
    debug: bool = Field(default=False, description="Enable debug mode")

    dry_run: bool = Field(default=False, description="Dry run mode (no actual downloads)")

    @field_validator("destination", "cookies_file", "database_path")
    @classmethod
    def resolve_path(cls, v: Path) -> Path:
        """Resolve and expand paths"""
        return v.expanduser().resolve()

    @field_validator("proxy")
    @classmethod
    def validate_proxy(cls, v: Optional[str]) -> Optional[str]:
        """Validate proxy URL format"""
        if v and not (v.startswith("http://") or v.startswith("https://")):
            raise ValueError("Proxy must start with http:// or https://")
        return v

    @property
    def is_authenticated(self) -> bool:
        """Check if cookies file exists"""
        return self.cookies_file.exists()

    def ensure_directories(self) -> None:
        """Ensure all required directories exist"""
        self.destination.mkdir(parents=True, exist_ok=True)
        if self.log_file:
            self.log_file.parent.mkdir(parents=True, exist_ok=True)

    def get_headers(self, cookies: str = "") -> dict[str, str]:
        """Get HTTP headers for requests"""
        return {
            "Accept": "application/json, text/plain, */*",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Cookie": cookies,
        }

    def get_proxies(self) -> dict[str, str] | None:
        """Get proxy configuration"""
        if self.proxy:
            return {"http://": self.proxy, "https://": self.proxy}
        return None
