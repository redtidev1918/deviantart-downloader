"""配置管理模块"""

import os
from typing import Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class Config:
    """配置类 - 管理所有下载器配置"""
    
    # 基本设置
    ask_before_download: bool = True
    debug_mode: bool = False
    delay_seconds: float = 1.0
    
    # 路径设置
    cookies_path: str = "cookies.txt"
    destination_folder: Optional[str] = None
    
    # API 设置
    lazy_load_limit: int = 24
    offset: int = 0
    
    # 网络设置
    proxy: str = ""
    max_retries: int = 3
    retry_delay: int = 3
    timeout: int = 180
    
    # 下载设置
    quality: str = "o"  # o=original, f=full, p=preview
    replace_existing: bool = True
    separate_folders: bool = True
    
    # 日志设置
    log_file: Optional[str] = None
    log_level: str = "INFO"
    
    # 内部使用
    _defaults: Dict[str, Any] = field(default_factory=dict, repr=False)
    
    def __post_init__(self):
        """初始化后处理"""
        self._defaults = {
            'ask_before_download': self.ask_before_download,
            'debug_mode': self.debug_mode,
            'delay_seconds': self.delay_seconds,
            'quality': self.quality,
        }
    
    @classmethod
    def from_args(cls, args: Dict[str, str]) -> 'Config':
        """从命令行参数创建配置"""
        config = cls()
        
        # 映射命令行参数到配置字段
        mapping = {
            '--ask': ('ask_before_download', lambda x: x == '1'),
            '--cookies': ('cookies_path', str),
            '--debug': ('debug_mode', lambda x: x == '1'),
            '--delay': ('delay_seconds', float),
            '--dest': ('destination_folder', str),
            '--limit': ('lazy_load_limit', int),
            '--offset': ('offset', int),
            '--proxy': ('proxy', str),
            '--quality': ('quality', str),
            '--replace': ('replace_existing', lambda x: x == '1'),
            '--separate': ('separate_folders', lambda x: x == '1'),
        }
        
        for arg, value in args.items():
            if arg in mapping:
                field_name, converter = mapping[arg]
                try:
                    setattr(config, field_name, converter(value))
                except (ValueError, TypeError) as e:
                    print(f"Warning: Invalid value for {arg}: {value} ({e})")
        
        return config
    
    def get_headers(self, cookies: str = "") -> Dict[str, str]:
        """获取 HTTP 请求头"""
        return {
            "accept": "application/json, text/plain, */*",
            "cookie": cookies,
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
    
    def get_proxies(self) -> Dict[str, str]:
        """获取代理配置"""
        if self.proxy:
            return {'http': self.proxy, 'https': self.proxy}
        return {}
    
    def validate(self) -> bool:
        """验证配置有效性"""
        if self.quality not in ['o', 'f', 'p']:
            print(f"Invalid quality: {self.quality}. Using default 'o'")
            self.quality = 'o'
            return False
        
        if self.lazy_load_limit < 1 or self.lazy_load_limit > 60:
            print(f"Invalid limit: {self.lazy_load_limit}. Using default 24")
            self.lazy_load_limit = 24
            return False
        
        if self.offset < 0:
            print(f"Invalid offset: {self.offset}. Using default 0")
            self.offset = 0
            return False
        
        return True
    
    def __str__(self) -> str:
        """字符串表示"""
        return (
            f"Config(\n"
            f"  quality={self.quality}, "
            f"  ask={self.ask_before_download}, "
            f"  delay={self.delay_seconds}s\n"
            f"  limit={self.lazy_load_limit}, "
            f"  offset={self.offset}, "
            f"  proxy={'yes' if self.proxy else 'no'}\n"
            f")"
        )
