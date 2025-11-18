#!/usr/bin/env python3
"""
增强的日志系统
Enhanced Logging System

支持：
- 彩色控制台输出
- 文件日志
- 多级别日志
- 调试模式
- i18n支持
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional


# 颜色代码
class LogColor:
    """ANSI颜色代码"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    RESET = '\033[0m'
    
    # 日志级别颜色
    DEBUG = '\033[36m'     # 青色
    INFO = '\033[32m'      # 绿色
    WARNING = '\033[33m'   # 黄色
    ERROR = '\033[31m'     # 红色
    CRITICAL = '\033[35m'  # 紫色


class ColoredFormatter(logging.Formatter):
    """彩色日志格式化器"""
    
    FORMATS = {
        logging.DEBUG: f"{LogColor.DEBUG}%(levelname)s{LogColor.RESET} - %(message)s",
        logging.INFO: f"{LogColor.INFO}%(levelname)s{LogColor.RESET} - %(message)s",
        logging.WARNING: f"{LogColor.WARNING}%(levelname)s{LogColor.RESET} - %(message)s",
        logging.ERROR: f"{LogColor.RED}%(levelname)s{LogColor.RESET} - %(message)s",
        logging.CRITICAL: f"{LogColor.CRITICAL}%(levelname)s{LogColor.RESET} - %(message)s",
    }
    
    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, datefmt='%H:%M:%S')
        return formatter.format(record)


class DetailedFormatter(logging.Formatter):
    """详细的日志格式化器（用于文件）"""
    
    def __init__(self):
        fmt = '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
        super().__init__(fmt, datefmt='%Y-%m-%d %H:%M:%S')


class Logger:
    """增强的日志管理器"""
    
    _instance: Optional['Logger'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        self.logger = logging.getLogger('deviantart_downloader')
        self.logger.setLevel(logging.DEBUG)
        self.logger.propagate = False
        
        # 清除已有的处理器
        self.logger.handlers.clear()
        
        # 控制台处理器（默认INFO级别）
        self.console_handler = None
        self.file_handler = None
        
        # 设置默认
        self.setup_console(level=logging.INFO)
    
    def setup_console(self, level: int = logging.INFO, colored: bool = True):
        """设置控制台日志"""
        if self.console_handler:
            self.logger.removeHandler(self.console_handler)
        
        self.console_handler = logging.StreamHandler(sys.stdout)
        self.console_handler.setLevel(level)
        
        if colored and sys.stdout.isatty():
            self.console_handler.setFormatter(ColoredFormatter())
        else:
            formatter = logging.Formatter(
                '%(levelname)s - %(message)s',
                datefmt='%H:%M:%S'
            )
            self.console_handler.setFormatter(formatter)
        
        self.logger.addHandler(self.console_handler)
    
    def setup_file(
        self, 
        log_file: Optional[str] = None,
        level: int = logging.DEBUG,
        max_bytes: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5
    ):
        """设置文件日志"""
        if not log_file:
            # 默认日志文件位置
            log_dir = Path.home() / '.deviantart_dl' / 'logs'
            log_dir.mkdir(parents=True, exist_ok=True)
            log_file = log_dir / f"devart-dl_{datetime.now().strftime('%Y%m%d')}.log"
        
        # 移除旧的文件处理器
        if self.file_handler:
            self.logger.removeHandler(self.file_handler)
            self.file_handler.close()
        
        # 使用 RotatingFileHandler
        from logging.handlers import RotatingFileHandler
        
        self.file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        self.file_handler.setLevel(level)
        self.file_handler.setFormatter(DetailedFormatter())
        
        self.logger.addHandler(self.file_handler)
        
        return log_file
    
    def set_level(self, level: int):
        """设置日志级别"""
        self.logger.setLevel(level)
        if self.console_handler:
            self.console_handler.setLevel(level)
    
    def debug(self, msg: str, *args, **kwargs):
        """DEBUG级别日志"""
        self.logger.debug(msg, *args, **kwargs)
    
    def info(self, msg: str, *args, **kwargs):
        """INFO级别日志"""
        self.logger.info(msg, *args, **kwargs)
    
    def warning(self, msg: str, *args, **kwargs):
        """WARNING级别日志"""
        self.logger.warning(msg, *args, **kwargs)
    
    def error(self, msg: str, *args, **kwargs):
        """ERROR级别日志"""
        self.logger.error(msg, *args, **kwargs)
    
    def critical(self, msg: str, *args, **kwargs):
        """CRITICAL级别日志"""
        self.logger.critical(msg, *args, **kwargs)
    
    def exception(self, msg: str, *args, **kwargs):
        """记录异常"""
        self.logger.exception(msg, *args, **kwargs)
    
    def success(self, msg: str):
        """成功消息（INFO级别，带特殊标记）"""
        self.logger.info(f"✓ {msg}")
    
    def fail(self, msg: str):
        """失败消息（ERROR级别，带特殊标记）"""
        self.logger.error(f"✗ {msg}")
    
    def progress(self, current: int, total: int, msg: str = ""):
        """进度日志"""
        percentage = (current / total * 100) if total > 0 else 0
        self.logger.info(f"进度: {current}/{total} ({percentage:.1f}%) {msg}")
    
    def section(self, title: str):
        """章节标题"""
        separator = "=" * 70
        self.logger.info("")
        self.logger.info(separator)
        self.logger.info(f"  {title}")
        self.logger.info(separator)
    
    def get_logger(self) -> logging.Logger:
        """获取底层logger对象"""
        return self.logger


# 全局实例
_logger: Optional[Logger] = None


def get_logger() -> Logger:
    """获取全局日志实例"""
    global _logger
    if _logger is None:
        _logger = Logger()
    return _logger


def setup_logger(
    level: int = logging.INFO,
    enable_file: bool = False,
    log_file: Optional[str] = None,
    colored: bool = True,
    debug: bool = False
) -> Logger:
    """
    设置全局日志配置
    
    Args:
        level: 日志级别
        enable_file: 是否启用文件日志
        log_file: 日志文件路径（None则使用默认）
        colored: 是否使用彩色输出
        debug: 是否启用调试模式
    
    Returns:
        Logger实例
    """
    logger = get_logger()
    
    # 调试模式
    if debug:
        level = logging.DEBUG
    
    # 设置控制台
    logger.setup_console(level=level, colored=colored)
    
    # 设置文件日志
    if enable_file:
        log_path = logger.setup_file(log_file=log_file, level=logging.DEBUG)
        logger.info(f"日志文件: {log_path}")
    
    return logger


# 便捷函数
def debug(msg: str, *args, **kwargs):
    """DEBUG日志"""
    get_logger().debug(msg, *args, **kwargs)


def info(msg: str, *args, **kwargs):
    """INFO日志"""
    get_logger().info(msg, *args, **kwargs)


def warning(msg: str, *args, **kwargs):
    """WARNING日志"""
    get_logger().warning(msg, *args, **kwargs)


def error(msg: str, *args, **kwargs):
    """ERROR日志"""
    get_logger().error(msg, *args, **kwargs)


def critical(msg: str, *args, **kwargs):
    """CRITICAL日志"""
    get_logger().critical(msg, *args, **kwargs)


def exception(msg: str, *args, **kwargs):
    """异常日志"""
    get_logger().exception(msg, *args, **kwargs)


def success(msg: str):
    """成功消息"""
    get_logger().success(msg)


def fail(msg: str):
    """失败消息"""
    get_logger().fail(msg)


def progress(current: int, total: int, msg: str = ""):
    """进度日志"""
    get_logger().progress(current, total, msg)


def section(title: str):
    """章节标题"""
    get_logger().section(title)


# 测试和示例
def main():
    """测试日志系统"""
    print("=" * 70)
    print("  DeviantArt Downloader - 日志系统测试")
    print("=" * 70)
    print()
    
    # 设置日志
    logger = setup_logger(
        level=logging.DEBUG,
        enable_file=True,
        colored=True,
        debug=True
    )
    
    # 测试各级别日志
    section("测试各级别日志")
    debug("这是一条DEBUG消息 - 用于调试信息")
    info("这是一条INFO消息 - 用于一般信息")
    warning("这是一条WARNING消息 - 用于警告信息")
    error("这是一条ERROR消息 - 用于错误信息")
    critical("这是一条CRITICAL消息 - 用于严重错误")
    
    # 测试便捷函数
    section("测试便捷函数")
    success("操作成功！")
    fail("操作失败！")
    
    # 测试进度
    section("测试进度显示")
    for i in range(0, 101, 20):
        progress(i, 100, f"下载中...")
        import time
        time.sleep(0.3)
    
    # 测试异常
    section("测试异常记录")
    try:
        1 / 0
    except Exception as e:
        exception(f"捕获异常: {e}")
    
    print()
    print("✓ 日志系统测试完成")
    print(f"✓ 日志文件已保存")


if __name__ == '__main__':
    main()
