"""工具函数模块"""

import os
import logging
from typing import Optional


logger = logging.getLogger(__name__)


def setup_logging(level: str = "INFO", log_file: Optional[str] = None):
    """配置日志系统"""
    # 日志格式
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    
    # 基本配置
    handlers = [logging.StreamHandler()]
    
    if log_file:
        handlers.append(logging.FileHandler(log_file, encoding='utf-8'))
    
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format=log_format,
        datefmt=date_format,
        handlers=handlers
    )
    
    # 降低 requests 库的日志级别
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)


def ensure_directory(path: str) -> bool:
    """确保目录存在"""
    if not os.path.exists(path):
        try:
            os.makedirs(path, exist_ok=True)
            logger.debug(f"Created directory: {path}")
            return True
        except OSError as e:
            logger.error(f"Failed to create directory {path}: {e}")
            return False
    return True


def sanitize_filename(filename: str) -> str:
    """清理文件名中的非法字符"""
    # Windows 非法字符
    illegal_chars = '<>:"/\\|?*'
    
    for char in illegal_chars:
        filename = filename.replace(char, '_')
    
    # 限制文件名长度
    max_length = 200
    if len(filename) > max_length:
        name, ext = os.path.splitext(filename)
        filename = name[:max_length - len(ext)] + ext
    
    return filename


def format_size(size_bytes: int) -> str:
    """格式化文件大小"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"


def get_user_input(prompt: str, valid_answers: Optional[list] = None) -> str:
    """获取用户输入"""
    while True:
        answer = input(prompt).strip().lower()
        
        if valid_answers is None:
            return answer
        
        if answer in valid_answers:
            return answer
        
        print(f"Invalid input. Please enter one of: {', '.join(valid_answers)}")


class ProgressTracker:
    """进度跟踪器"""
    
    def __init__(self, total: int, description: str = "Processing"):
        self.total = total
        self.current = 0
        self.description = description
        self.success_count = 0
        self.fail_count = 0
        self.skip_count = 0
    
    def update(self, increment: int = 1, success: bool = True, skipped: bool = False):
        """更新进度"""
        self.current += increment
        
        if skipped:
            self.skip_count += 1
        elif success:
            self.success_count += 1
        else:
            self.fail_count += 1
        
        self._print_progress()
    
    def _print_progress(self):
        """打印进度信息"""
        percentage = (self.current / self.total * 100) if self.total > 0 else 0
        bar_length = 40
        filled = int(bar_length * self.current / self.total) if self.total > 0 else 0
        bar = '█' * filled + '░' * (bar_length - filled)
        
        status = (
            f"\r{self.description}: [{bar}] "
            f"{self.current}/{self.total} ({percentage:.1f}%) "
            f"✓{self.success_count} ✗{self.fail_count} ⊘{self.skip_count}"
        )
        
        print(status, end='', flush=True)
        
        if self.current >= self.total:
            print()  # 换行
    
    def finish(self):
        """完成进度跟踪"""
        print(f"\n{self.description} completed!")
        print(f"  Success: {self.success_count}")
        print(f"  Failed:  {self.fail_count}")
        print(f"  Skipped: {self.skip_count}")


def print_banner():
    """打印程序横幅"""
    banner = """
╔══════════════════════════════════════════════════════════════════════╗
║          DeviantArt Downloader v2.0 - Refactored Edition             ║
║                    Modern • Modular • Maintainable                    ║
╚══════════════════════════════════════════════════════════════════════╝
"""
    print(banner)


def print_section(title: str):
    """打印分节标题"""
    print(f"\n{'─' * 70}")
    print(f"  {title}")
    print('─' * 70)
