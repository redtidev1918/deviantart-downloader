"""核心下载器模块"""

import os
import logging
from pathlib import Path
from time import sleep
from typing import Optional

from .config import Config
from .auth import AuthManager
from .api import DeviantArtAPI
from .errors import DeviantArtError
from .http import HttpDownloader
from .models import DownloadTask, DownloadResult, ActionType, Quality
from .utils import ensure_directory, sanitize_filename
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
        
        # 可靠的文件传输：流式下载 + .part + Range 续传 + 重试/429 + 响应校验。
        self.http = HttpDownloader(
            session=self.api.session,
            max_retries=config.max_retries,
            retry_backoff=float(config.retry_delay),
            timeout=config.timeout,
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
            logger.info("📊 Resume from previous session:")
            logger.info(f"  Downloaded: {stats['downloaded']}, Failed: {stats['failed']}, Skipped: {stats['skipped']}")
        
        if not self.api.get_csrf_token(username):
            logger.error("Failed to get CSRF token")
            return
        
        # 检查并显示登录状态
        self._show_login_status()
        
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
        
        # 显示登录状态
        self._show_login_status()
        
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
        """从 URL 下载作品，并验证每一个分页续传位置。"""
        if offset is None:
            offset = self.config.offset
        url_with_limit = url.replace('<LIMIT>', str(self.config.lazy_load_limit))
        seen_pages = set()

        while True:
            page_key = (offset, cursor)
            if page_key in seen_pages:
                raise RuntimeError(
                    f"Pagination did not advance (offset={offset}, cursor={cursor!r})"
                )
            seen_pages.add(page_key)

            deviations, has_more, next_offset, next_cursor = self.api.fetch_deviations(
                url_with_limit, offset, cursor
            )
            if not deviations:
                logger.warning("No downloadable records parsed on this page")

            for i, deviation in enumerate(deviations, start=offset):
                if not deviation.is_downloadable_type():
                    logger.info(f"[{i}] Skipped (not downloadable type): {deviation.title}")
                    self.total_skipped += 1
                    if self.progress:
                        self.progress.mark_skipped(deviation.deviation_id)
                    continue

                destination = self._get_destination_folder(username, deviation.author)
                filename = sanitize_filename(deviation.get_filename())
                file_path = os.path.join(destination, filename)

                if os.path.isfile(file_path) and not self.config.replace_existing:
                    logger.info(f"[{i}] ✓ Already exists: {deviation.title}")
                    self.total_skipped += 1
                    if self.progress:
                        self.progress.mark_downloaded(deviation.deviation_id, file_path)
                    continue

                if (
                    self.progress
                    and not self.config.replace_existing
                    and self.progress.is_downloaded(deviation.deviation_id, file_path)
                ):
                    logger.info(f"[{i}] ✓ Already downloaded: {deviation.title}")
                    self.total_skipped += 1
                    continue

                if self.progress and self.progress.is_failed(deviation.deviation_id):
                    logger.info(
                        f"[{i}] 🔄 Retrying previous failure: {deviation.title}"
                    )

                task = DownloadTask(
                    deviation=deviation,
                    quality=Quality(self.config.quality),
                    destination=destination,
                    index=i
                )
                result = self._download_single(task)

                if self.progress:
                    if result.success:
                        self.progress.mark_downloaded(
                            deviation.deviation_id, result.file_path
                        )
                    elif not result.skipped:
                        self.progress.mark_failed(
                            deviation.deviation_id, result.error or "Unknown error"
                        )

                if result.success:
                    self.total_downloaded += 1
                elif result.skipped:
                    self.total_skipped += 1
                else:
                    self.total_failed += 1

                if (
                    self.config.delay_seconds > 0
                    and (not self.config.ask_before_download or self.download_all)
                ):
                    sleep(self.config.delay_seconds)

            if self.progress:
                self.progress.update_position(next_offset, next_cursor)
            if not has_more:
                break

            logger.info(
                "Fetching next page (offset: %s, cursor: %s)...",
                next_offset,
                next_cursor or "-",
            )
            offset, cursor = next_offset, next_cursor

        logger.info("=" * 70)
        logger.info("Download session completed!")
        logger.info(f"  Downloaded: {self.total_downloaded}")
        logger.info(f"  Failed:     {self.total_failed}")
        logger.info(f"  Skipped:    {self.total_skipped}")
        if self.total_failed:
            logger.warning("Failed items were retained and will be retried next run.")
        logger.info("=" * 70)
    
    def _download_single(self, task: DownloadTask) -> DownloadResult:
        """下载单个作品"""
        deviation = task.deviation
        
        # 准备目标文件夹
        ensure_directory(task.destination)
        
        # 获取文件名
        filename = sanitize_filename(deviation.get_filename())
        file_path = os.path.join(task.destination, filename)
        
        # 注意：文件存在检查已在外层完成，这里不需要重复检查
        
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
        
        # 如果是原图且需要登录，自动降级到全图质量
        if quality == 'o' and not download_url:
            logger.warning(f"[{task.index}] Original quality requires login, falling back to full quality")
            quality = 'f'
            download_url = self.api.get_download_url(deviation, quality)
        
        if not download_url:
            logger.error(f"[{task.index}] Failed to get download URL: {deviation.title}")
            return DownloadResult(task=task, success=False, error="No download URL")
        
        # 原图 URL 可能提供更准确的扩展名。
        if quality == 'o' and '.' in download_url:
            ext = '.' + download_url.split('?')[0].split('.')[-1]
            if 1 < len(ext) <= 10:
                file_path = os.path.splitext(file_path)[0] + ext

        try:
            self.http.download(
                download_url, Path(file_path), overwrite=self.config.replace_existing
            )
        except DeviantArtError as exc:
            logger.error(f"[{task.index}] Failed to download: {deviation.title} ({exc})")
            return DownloadResult(task=task, success=False, error=str(exc))

        logger.info(f"[{task.index}] ✓ Downloaded: {os.path.basename(file_path)}")
        return DownloadResult(task=task, success=True, file_path=file_path)
    
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
    
    def _show_login_status(self):
        """显示登录状态"""
        logger.info("=" * 70)
        if self.auth.cookies:
            is_logged_in = self.auth.check_login_status(self.api.headers, self.api.proxies)
            if is_logged_in:
                logger.info("🔓 Login Status: ✅ LOGGED IN")
                logger.info("   You can download original quality and mature content")
            else:
                logger.info("🔒 Login Status: ⚠️  NOT LOGGED IN")
                logger.info("   Limited to public content and full quality")
        else:
            logger.info("🔒 Login Status: ⚠️  NO COOKIES")
            logger.info("   Limited to public content only")
            logger.info("   Run 'devart-dl login interactive' to login")
        logger.info("=" * 70)
    
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
