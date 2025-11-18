"""
DeviantArt Downloader - 模块化下载工具

这是一个重构版本，采用面向对象设计和模块化架构。
"""

__version__ = "2.0.0"
__author__ = "DeviantArt Downloader Team"

from .downloader import DeviantArtDownloader
from .config import Config
from .auth import AuthManager

__all__ = ['DeviantArtDownloader', 'Config', 'AuthManager']
