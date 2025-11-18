"""核心下载器模块"""

import os
import logging
from time import sleep
from typing import List, Optional

from .config import Config
from .auth import AuthManager
from .api import DeviantArtAPI
from .models import Deviation, DownloadTask, DownloadResult, ActionType, Quality
from .utils import ensure_directory, sanitize_filename, ProgressTracker
from .progress import ProgressManager


logger = logging.getLogger(__name__)


class DeviantArtDownloader:
    """DeviantArt 下载器主类"""
    
    # 交互式命令常量
    CMD_QUIT = ('q', 'quit')
    CMD_SKIP = ('s', 'skip')
    CMD_ALL = ('a', 'all')
    CMD_YES = ('y', 'yes')
    CMD_PREVIEW = ('p', 'pre', 'preview')
    CMD_FULL = ('f', 'ful', 'full')
    CMD_ORIGINAL = ('o', 'org', 'original')
    
    def __init__(self, config: Config):
        self.config = config
        self.auth = AuthManager(config.cookies_path)
        
        # 加载并验证 cookies
        cookies = self.auth.load_cookies()
        
        # 初始化 API 客户端
        headers = config.get_headers(cookies)
        proxies = config.get_proxies()
        
        self.api = DeviantArtAPI(
            headers=headers,
            proxies=proxies,
            retry_delay=config.retry_delay,
            max_retries=config.max_retries
        )
        
        # 状态变量
        self.download_all = False
        self.total_downloaded = 0
        self.total_failed = 0
        self.total_skipped = 0
        
        # 进度管理器（稍后初始化，需要session_name）
        self.progress: Optional[ProgressManager] = None
    
    def download_gallery(self, username: str, folder_id: Optional[str] = None):
        """下载画廊（支持断点续传）"""
        logger.info(f"Starting gallery download for user: {username}")
        
        # 初始化进度管理器
        session_name = f"gallery_{username}_{folder_id or 'all'}"
        self.progress = ProgressManager(session_name)
        
        # 显示上次进度
        stats = self.progress.get_stats()
        if stats['total'] > 0:
            logger.info(f"📊 Resume from previous session:")
            logger.info(f"  Downloaded: {stats['downloaded']}, Failed: {stats['failed']}, Skipped: {stats['skipped']}")
        
        if not self.api.get_csrf_token(username):
            logger.error("Failed to get CSRF token")
            return
        
        # 检查登录状态
        if self.auth.cookies:
            self.auth.check_login_status(self.api.headers, self.api.proxies)
        
        # 构建 API URL
        url = self.api.build_api_url(ActionType.GALLERY, username, folder_id=folder_id)
        
        # 开始下载
        self._download_from_url(url, username)
    
    def download_search(self, username: str, query: str):
        """搜索并下载"""
        logger.info(f"Searching for '{query}' in {username}'s gallery")
        
        if username.lower() != 'all':
            if not self.api.get_csrf_token(username):
                logger.error("Failed to get CSRF token")
                return
        else:
            # 全局搜索，使用通用页面获取 token
            if not self.api.get_csrf_token(''):
                logger.error("Failed to get CSRF token")
                return
        
        # 构建 API URL
        url = self.api.build_api_url(ActionType.SEARCH, username, query=query)
        
        # 开始下载
        self._download_from_url(url, username if username != 'all' else 'search')
    
    def download_favorites(self, username: str, folder_id: str):
        """下载收藏夹"""
        logger.info(f"Downloading favorites from {username}, folder: {folder_id}")
        
        if not self.api.get_csrf_token(username):
            logger.error("Failed to get CSRF token")
            return
        
        # 构建 API URL
        url = self.api.build_api_url(ActionType.FAVORITE, username, folder_id=folder_id)
        
        # 开始下载
        self._download_from_url(url, username)
    
    def _download_from_url(self, url: str, username: str, 
                          offset: Optional[int] = None, cursor: str = ""):
        """从 URL 下载作品（递归处理分页）"""
        if offset is None:
            offset = self.config.offset
        
        # 获取作品列表
        url_with_limit = url.replace('<LIMIT>', str(self.config.lazy_load_limit))
        deviations, has_more, next_offset, next_cursor = self.api.fetch_deviations(
            url_with_limit, offset, cursor
        )
        
        if not deviations:
            logger.warning("No deviations found")
            return
        
        # 处理每个作品
        for i, deviation in enumerate(deviations, start=offset):
            # 检查是否可下载类型
            if not deviation.is_downloadable_type():
                logger.info(f"[{i}] Skipped (not downloadable type): {deviation.title}")
                self.total_skipped += 1
                if self.progress:
                    self.progress.mark_skipped(deviation.deviation_id)
                continue
            
            # 检查是否已下载（断点续传）
            if self.progress and self.progress.is_downloaded(deviation.deviation_id):
                logger.info(f"[{i}] ✓ Already downloaded: {deviation.title}")
                self.total_skipped += 1
                continue
            
            # 检查是否需要重试
            if self.progress and self.progress.is_failed(deviation.deviation_id):
                if not self.progress.should_retry(deviation.deviation_id):
                    logger.info(f"[{i}] ✗ Max retries exceeded: {deviation.title}")
                    self.total_failed += 1
                    continue
                logger.info(f"[{i}] 🔄 Retrying (attempt {self.progress.get_retry_count(deviation.deviation_id) + 1}): {deviation.title}")
            
            # 创建下载任务
            task = DownloadTask(
                deviation=deviation,
                quality=Quality(self.config.quality),
                destination=self._get_destination_folder(username, deviation.author),
                index=i
            )
            
            # 执行下载
            result = self._download_single(task)
            
            # 更新进度管理器
            if self.progress:
                if result.success:
                    self.progress.mark_downloaded(deviation.deviation_id)
                elif not result.skipped:
                    self.progress.mark_failed(deviation.deviation_id, result.error or "Unknown error")
            
            # 更新统计
            if result.success:
                self.total_downloaded += 1
            elif result.skipped:
                self.total_skipped += 1
            else:
                self.total_failed += 1
            
            # 延迟
            if not self.config.ask_before_download and not self.download_all:
                sleep(self.config.delay_seconds)
        
        # 更新进度位置
        if self.progress:
            self.progress.update_position(next_offset, next_cursor)
        
        # 处理分页
        if has_more:
            logger.info(f"Fetching next page (offset: {next_offset})...")
            self._download_from_url(url, username, next_offset, next_cursor)
        else:
            logger.info("=" * 70)
            logger.info("Download session completed!")
            logger.info(f"  Downloaded: {self.total_downloaded}")
            logger.info(f"  Failed:     {self.total_failed}")
            logger.info(f"  Skipped:    {self.total_skipped}")
            
            # 清除进度文件（下载完成）
            if self.progress:
                logger.info("  Clearing progress...")
                self.progress.clear()
            logger.info("=" * 70)
    
    def _download_single(self, task: DownloadTask) -> DownloadResult:
        """下载单个作品"""
        deviation = task.deviation
        
        # 准备目标文件夹
        ensure_directory(task.destination)
        
        # 获取文件名
        filename = sanitize_filename(deviation.get_filename())
        file_path = os.path.join(task.destination, filename)
        
        # 检查文件是否已存在
        if os.path.isfile(file_path) and not self.config.replace_existing:
            logger.info(f"[{task.index}] Skipped (already exists): {filename}")
            return DownloadResult(task=task, success=False, skipped=True)
        
        # 询问用户（如果需要）
        quality = task.quality.value
        if self.config.ask_before_download and not self.download_all:
            quality = self._ask_user(task, file_path)
            
            if quality is None:
                return DownloadResult(task=task, success=False, skipped=True)
            elif quality == 'skip_all':
                return DownloadResult(task=task, success=False, skipped=True)
        
        # 获取下载 URL
        download_url = self.api.get_download_url(deviation, quality)
        
        # 如果是原图且需要登录
        if quality == 'o' and not download_url:
            logger.warning("Original quality requires login")
            if not self._handle_login_required():
                return DownloadResult(
                    task=task,
                    success=False,
                    error="Login required for original quality"
                )
            # 重试获取下载 URL
            download_url = self.api.get_download_url(deviation, quality)
        
        if not download_url:
            logger.error(f"[{task.index}] Failed to get download URL: {deviation.title}")
            return DownloadResult(task=task, success=False, error="No download URL")
        
        # 下载文件
        content = self.api.download_file(download_url, self.config.timeout)
        if not content:
            logger.error(f"[{task.index}] Failed to download: {deviation.title}")
            return DownloadResult(task=task, success=False, error="Download failed")
        
        # 保存文件
        try:
            # 更新文件扩展名（从实际下载的 URL）
            if quality == 'o' and '.' in download_url:
                ext = '.' + download_url.split('?')[0].split('.')[-1]
                file_path = os.path.splitext(file_path)[0] + ext
            
            with open(file_path, 'wb') as f:
                f.write(content)
            
            logger.info(f"[{task.index}] ✓ Downloaded: {filename}")
            return DownloadResult(task=task, success=True, file_path=file_path)
            
        except OSError as e:
            logger.error(f"Failed to save file: {e}")
            input("Please close the file if it's open and press Enter...")
            # 重试
            try:
                with open(file_path, 'wb') as f:
                    f.write(content)
                return DownloadResult(task=task, success=True, file_path=file_path)
            except OSError as e2:
                return DownloadResult(task=task, success=False, error=str(e2))
    
    def _ask_user(self, task: DownloadTask, file_path: str) -> Optional[str]:
        """询问用户是否下载"""
        deviation = task.deviation
        
        # 构建提示信息
        title_info = f"[{task.index}] {deviation.title}"
        if deviation.is_mature:
            title_info += " [MATURE CONTENT]"
        if os.path.isfile(file_path):
            title_info += " [ALREADY DOWNLOADED]"
        
        print(f"\n{title_info}")
        print(f"By: {deviation.author}")
        print(f"URL: {deviation.url}")
        
        # 显示操作选项说明（首次或按需）
        if not hasattr(self, '_options_shown'):
            print("\n操作选项 | Options:")
            print("  y - YES      下载此作品 | Download this")
            print("  n - NO       跳过此作品 | Skip this")
            print("  a - ALL      下载全部（推荐）| Download all (Recommended)")
            print("  s - SKIP     跳过全部 | Skip all")
            print("  q - QUIT     退出程序 | Quit")
            print("  p - PREVIEW  预览质量 | Preview quality")
            print("  f - FULL     全图质量 | Full quality")
            print("  o - ORIGINAL 原图质量 | Original quality")
            self._options_shown = True
        
        answer = input("\nAction [y/n/a/s/q/p/f/o]: ").strip().lower()
        
        if answer in self.CMD_QUIT:
            logger.info("User requested quit")
            exit(0)
        elif answer in self.CMD_SKIP:
            return 'skip_all'
        elif answer in self.CMD_ALL:
            self.download_all = True
            return task.quality.value
        elif answer in self.CMD_YES:
            return task.quality.value
        elif answer in self.CMD_PREVIEW:
            return 'p'
        elif answer in self.CMD_FULL:
            return 'f'
        elif answer in self.CMD_ORIGINAL:
            return 'o'
        else:
            return None
    
    def _handle_login_required(self) -> bool:
        """处理需要登录的情况"""
        attempts = 0
        max_attempts = 3
        
        while attempts < max_attempts:
            if attempts == 0:
                AuthManager.show_login_guide()
            
            cmd = input("\nAfter updating cookies.txt, press ENTER to retry (or 'q' to quit): ")
            if cmd.lower() in self.CMD_QUIT:
                return False
            
            # 重新加载 cookies
            new_cookies = self.auth.reload_cookies()
            if not new_cookies:
                logger.warning("Still no cookies found")
                attempts += 1
                continue
            
            # 更新 headers
            self.api.headers['cookie'] = new_cookies
            
            if self.auth.validate_cookies(new_cookies):
                logger.info("✓ Cookies updated successfully")
                return True
            
            attempts += 1
        
        logger.error("Failed to authenticate after multiple attempts")
        return False
    
    def _get_destination_folder(self, base_username: str, author: str) -> str:
        """获取目标文件夹路径"""
        # 基础目录
        if self.config.destination_folder:
            base_dir = self.config.destination_folder
        else:
            base_dir = "Downloads"
        
        # 是否为每个作者创建单独文件夹
        if self.config.separate_folders:
            return os.path.join(base_dir, author)
        else:
            return base_dir
