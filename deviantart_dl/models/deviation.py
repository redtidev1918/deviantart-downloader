"""Deviation data models"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, HttpUrl, field_validator


class DeviationType(str, Enum):
    """Types of deviations"""

    IMAGE = "image"
    LITERATURE = "literature"
    VIDEO = "video"
    UNKNOWN = "unknown"


class MediaInfo(BaseModel):
    """Media information from DeviantArt API"""

    base_uri: HttpUrl = Field(..., description="Base URI for media")
    pretty_name: str = Field(..., description="Pretty filename")
    token: list[str] = Field(default_factory=list, description="Access tokens")
    types: list[dict[str, Any]] = Field(default_factory=list, description="Available media types")

    @property
    def has_token(self) -> bool:
        """Check if media has access token"""
        return len(self.token) > 0

    def get_type(self, type_name: str) -> Optional[dict[str, Any]]:
        """Get media type by name (e.g., 'fullview', 'preview')"""
        return next((t for t in self.types if t.get("t") == type_name), None)


class Deviation(BaseModel):
    """
    DeviantArt deviation (artwork) model.

    This model validates and normalizes data from the DeviantArt API.
    """

    deviation_id: str = Field(..., min_length=1, description="Unique deviation ID")
    title: str = Field(..., description="Deviation title")
    url: HttpUrl = Field(..., description="Deviation page URL")
    author: str = Field(..., description="Author username")
    published_time: Optional[datetime] = Field(None, description="Publication timestamp")

    # Media information
    media: Optional[MediaInfo] = Field(None, description="Media information")
    thumbnail_url: Optional[HttpUrl] = Field(None, description="Thumbnail URL")

    # Properties
    deviation_type: DeviationType = Field(
        default=DeviationType.UNKNOWN, description="Type of deviation"
    )
    is_downloadable: bool = Field(default=False, description="Has download button")
    is_mature: bool = Field(default=False, description="Contains mature content")
    is_favourited: bool = Field(default=False, description="Is in favourites")

    # Stats
    stats_comments: int = Field(default=0, ge=0, description="Number of comments")
    stats_favourites: int = Field(default=0, ge=0, description="Number of favourites")

    # Raw data (for debugging)
    raw_data: dict[str, Any] = Field(default_factory=dict, description="Raw API response")

    model_config = {"extra": "ignore"}

    @field_validator("deviation_type", mode="before")
    @classmethod
    def normalize_type(cls, v: Any) -> DeviationType:
        """Normalize deviation type from API response"""
        if isinstance(v, DeviationType):
            return v

        type_str = str(v).lower()
        type_mapping = {
            "image": DeviationType.IMAGE,
            "deviation": DeviationType.IMAGE,
            "literature": DeviationType.LITERATURE,
            "video": DeviationType.VIDEO,
            "film": DeviationType.VIDEO,
        }
        return type_mapping.get(type_str, DeviationType.UNKNOWN)

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> "Deviation":
        """
        Create Deviation from DeviantArt API response.

        Handles both 'results' and 'deviations' formats.
        """
        # Handle nested structure
        if "deviation" in data:
            data = data["deviation"]

        # Extract author
        author_data = data.get("author", {})
        author = author_data.get("username", "unknown")

        # Extract media
        media_data = data.get("media")
        media = MediaInfo(**media_data) if media_data else None

        # Extract stats
        stats = data.get("stats", {})

        # Build deviation
        return cls(
            deviation_id=str(data.get("deviationId", data.get("deviationid", ""))),
            title=data.get("title", "Untitled"),
            url=data.get("url", "https://deviantart.com"),
            author=author,
            published_time=data.get("publishedTime", data.get("published_time")),
            media=media,
            thumbnail_url=data.get("thumbs", [{}])[0].get("src") if data.get("thumbs") else None,
            deviation_type=data.get("type", "unknown"),
            is_downloadable=data.get(
                "isDownloadable", data.get("is_downloadable", False)
            ),
            is_mature=data.get("isMature", data.get("is_mature", False)),
            is_favourited=data.get(
                "isFavourited", data.get("is_favourited", False)
            ),
            stats_comments=stats.get("comments", 0),
            stats_favourites=stats.get("favourites", 0),
            raw_data=data,
        )

    @property
    def is_downloadable_type(self) -> bool:
        """Check if deviation type supports downloading"""
        return self.deviation_type in {DeviationType.IMAGE, DeviationType.VIDEO}

    @property
    def filename_base(self) -> str:
        """Get base filename from media or title"""
        if self.media:
            return self.media.pretty_name
        # Sanitize title for filename
        return "".join(c for c in self.title if c.isalnum() or c in (" ", "-", "_")).strip()

    def get_file_extension(self) -> str:
        """Extract file extension from media URI"""
        if not self.media:
            return ".jpg"

        uri = str(self.media.base_uri)
        parts = uri.split(".")
        if len(parts) > 1:
            return f".{parts[-1].split('?')[0]}"  # Remove query params
        return ".jpg"

    def __str__(self) -> str:
        """Human-readable string representation"""
        flags = []
        if self.is_mature:
            flags.append("MATURE")
        if self.is_downloadable:
            flags.append("DL")
        if self.is_favourited:
            flags.append("FAV")

        flag_str = f" [{', '.join(flags)}]" if flags else ""
        return f"{self.title} by {self.author}{flag_str}"

    def __repr__(self) -> str:
        """Developer-friendly representation"""
        return f"Deviation(id={self.deviation_id}, title={self.title!r}, author={self.author!r})"
