"""Download task and result models"""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field, HttpUrl

from .config import DownloadQuality
from .deviation import Deviation


class DownloadStatus(str, Enum):
    """Download status"""

    PENDING = "pending"
    DOWNLOADING = "downloading"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"


class DownloadTask(BaseModel):
    """Download task specification"""

    deviation: Deviation = Field(..., description="Deviation to download")
    quality: DownloadQuality = Field(..., description="Desired quality")
    destination: Path = Field(..., description="Download destination directory")
    filename: Optional[str] = Field(None, description="Custom filename")
    priority: int = Field(default=0, description="Task priority (higher = first)")

    created_at: datetime = Field(default_factory=datetime.now, description="Task creation time")

    model_config = {"arbitrary_types_allowed": True}

    @property
    def file_path(self) -> Path:
        """Get full file path for download"""
        if self.filename:
            return self.destination / self.filename
        return self.destination / f"{self.deviation.filename_base}{self.deviation.get_file_extension()}"

    @property
    def file_exists(self) -> bool:
        """Check if file already exists"""
        return self.file_path.exists()

    def __lt__(self, other: "DownloadTask") -> bool:
        """Compare tasks by priority (for queue sorting)"""
        return self.priority < other.priority


class DownloadResult(BaseModel):
    """Result of a download operation"""

    task: DownloadTask = Field(..., description="Original download task")
    status: DownloadStatus = Field(..., description="Download status")

    # Success info
    file_path: Optional[Path] = Field(None, description="Downloaded file path")
    file_size: int = Field(default=0, ge=0, description="Downloaded file size in bytes")
    download_url: Optional[HttpUrl] = Field(None, description="Actual download URL used")

    # Error info
    error_message: Optional[str] = Field(None, description="Error message if failed")
    error_type: Optional[str] = Field(None, description="Error type/exception name")

    # Timing
    started_at: Optional[datetime] = Field(None, description="Download start time")
    completed_at: Optional[datetime] = Field(None, description="Download completion time")
    duration_seconds: float = Field(default=0.0, ge=0, description="Download duration")

    # Retries
    attempts: int = Field(default=1, ge=1, description="Number of attempts")

    model_config = {"arbitrary_types_allowed": True}

    @property
    def is_success(self) -> bool:
        """Check if download was successful"""
        return self.status == DownloadStatus.SUCCESS

    @property
    def is_failed(self) -> bool:
        """Check if download failed"""
        return self.status == DownloadStatus.FAILED

    @property
    def is_skipped(self) -> bool:
        """Check if download was skipped"""
        return self.status == DownloadStatus.SKIPPED

    @property
    def file_size_mb(self) -> float:
        """Get file size in MB"""
        return self.file_size / (1024 * 1024)

    def to_dict(self) -> dict:
        """Convert to dictionary for database storage"""
        return {
            "deviation_id": self.task.deviation.deviation_id,
            "title": self.task.deviation.title,
            "author": self.task.deviation.author,
            "url": str(self.task.deviation.url),
            "quality": self.task.quality.value,
            "status": self.status.value,
            "file_path": str(self.file_path) if self.file_path else None,
            "file_size": self.file_size,
            "download_url": str(self.download_url) if self.download_url else None,
            "error_message": self.error_message,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "duration_seconds": self.duration_seconds,
            "attempts": self.attempts,
        }

    def __str__(self) -> str:
        """Human-readable string representation"""
        if self.is_success:
            return f"✓ {self.task.deviation.title} ({self.file_size_mb:.2f} MB)"
        elif self.is_failed:
            return f"✗ {self.task.deviation.title}: {self.error_message}"
        elif self.is_skipped:
            return f"⊘ {self.task.deviation.title} (skipped)"
        else:
            return f"◯ {self.task.deviation.title} ({self.status.value})"
