"""数据模型模块"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
from enum import Enum


class ActionType(Enum):
    """操作类型枚举"""
    GALLERY = "gallery"
    SEARCH = "search"
    FAVORITE = "fav"


class Quality(Enum):
    """图片质量枚举"""
    ORIGINAL = "o"
    FULL = "f"
    PREVIEW = "p"


@dataclass
class Deviation:
    """作品数据模型"""
    deviation_id: str
    title: str
    url: str
    author: str
    media: Dict[str, Any]
    is_downloadable: bool
    is_mature: bool
    deviation_type: str
    
    @classmethod
    def from_api_response(cls, data: Dict[str, Any]) -> 'Deviation':
        """从 API 响应创建 Deviation 对象"""
        # 处理嵌套的 deviation 结构
        if 'deviation' in data:
            data = data['deviation']
        
        return cls(
            deviation_id=data.get('deviationId', ''),
            title=data.get('title', 'Untitled'),
            url=data.get('url', ''),
            author=data.get('author', {}).get('username', 'Unknown'),
            media=data.get('media', {}),
            is_downloadable=data.get('isDownloadable', False),
            is_mature=data.get('isMature', False),
            deviation_type=data.get('type', 'unknown')
        )
    
    def get_filename(self) -> str:
        """获取文件名"""
        media = self.media
        if not media or 'prettyName' not in media:
            return f"{self.title}.jpg"
        
        pretty_name = media['prettyName']
        base_uri = media.get('baseUri', '')
        
        # 从 baseUri 提取文件扩展名
        ext = self._extract_extension(base_uri)
        return f"{pretty_name}{ext}"
    
    def _extract_extension(self, uri: str) -> str:
        """从 URI 提取文件扩展名"""
        parts = uri.split('.')
        if len(parts) > 1:
            return f".{parts[-1]}"
        return ".jpg"
    
    def is_downloadable_type(self) -> bool:
        """检查是否可下载类型"""
        return self.deviation_type not in ['literature']
    
    def __str__(self) -> str:
        """字符串表示"""
        flags = []
        if self.is_mature:
            flags.append("MATURE")
        if self.is_downloadable:
            flags.append("DOWNLOADABLE")
        
        flag_str = f" [{', '.join(flags)}]" if flags else ""
        return f"{self.title} by {self.author}{flag_str}"


@dataclass
class DownloadTask:
    """下载任务"""
    deviation: Deviation
    quality: Quality
    destination: str
    index: int = 0
    
    def __str__(self) -> str:
        return f"Task[{self.index}]: {self.deviation.title} ({self.quality.value})"


@dataclass
class DownloadResult:
    """下载结果"""
    task: DownloadTask
    success: bool
    file_path: Optional[str] = None
    error: Optional[str] = None
    skipped: bool = False
    
    def __str__(self) -> str:
        if self.success:
            return f"✓ Downloaded: {self.file_path}"
        elif self.skipped:
            return f"⊘ Skipped: {self.task.deviation.title}"
        else:
            return f"✗ Failed: {self.task.deviation.title} - {self.error}"
