#!/usr/bin/env python3
"""
国际化 (i18n) 支持
Internationalization Support

支持语言 / Supported Languages:
- 简体中文 (zh_CN)
- English (en_US)
"""

import os
import json
from pathlib import Path
from typing import Dict, Optional


class I18n:
    """轻量级国际化管理器"""
    
    SUPPORTED_LANGUAGES = {
        'zh_CN': '简体中文',
        'zh': '简体中文',
        'en_US': 'English',
        'en': 'English',
    }
    
    def __init__(self, lang: Optional[str] = None):
        """
        初始化国际化
        
        Args:
            lang: 语言代码 (zh_CN, en_US) 或 None (自动检测)
        """
        self.current_lang = self._detect_language(lang)
        self.translations = self._load_translations()
    
    def _detect_language(self, lang: Optional[str]) -> str:
        """检测语言"""
        # 1. 使用指定的语言
        if lang and lang in self.SUPPORTED_LANGUAGES:
            return self._normalize_lang(lang)
        
        # 2. 从环境变量检测
        env_lang = os.getenv('LANG', '').split('.')[0]
        if env_lang.startswith('zh'):
            return 'zh_CN'
        
        env_lang = os.getenv('DEVART_LANG', '')
        if env_lang in self.SUPPORTED_LANGUAGES:
            return self._normalize_lang(env_lang)
        
        # 3. 默认英文
        return 'en_US'
    
    def _normalize_lang(self, lang: str) -> str:
        """规范化语言代码"""
        if lang.startswith('zh'):
            return 'zh_CN'
        return 'en_US'
    
    def _load_translations(self) -> Dict[str, Dict[str, str]]:
        """加载翻译文本"""
        return {
            'zh_CN': self._get_zh_translations(),
            'en_US': self._get_en_translations(),
        }
    
    def _get_zh_translations(self) -> Dict[str, str]:
        """中文翻译"""
        return {
            # 通用
            'app_name': 'DeviantArt 下载器',
            'version': '版本',
            'help': '帮助',
            'error': '错误',
            'warning': '警告',
            'success': '成功',
            'cancel': '取消',
            'yes': '是',
            'no': '否',
            
            # 命令
            'command_gallery': '下载画廊',
            'command_search': '搜索下载',
            'command_fav': '下载收藏',
            'command_url': 'URL下载',
            'command_artist': '作者下载',
            'command_login': '登录管理',
            'command_anti_ban': '防封指南',
            'command_config': '配置管理',
            'command_version': '版本信息',
            'command_docs': '文档列表',
            
            # 下载状态
            'downloading': '下载中',
            'downloaded': '已下载',
            'failed': '失败',
            'skipped': '跳过',
            'exists': '已存在',
            
            # 质量
            'quality_original': '原图',
            'quality_full': '全图',
            'quality_preview': '预览',
            
            # 登录
            'login_required': '需要登录',
            'login_optional': '可选登录',
            'cookie_loaded': 'Cookie 已加载',
            'cookie_missing': '未找到 Cookie',
            'auth_success': '认证成功',
            'auth_failed': '认证失败',
            
            # 消息
            'msg_start': '开始下载',
            'msg_complete': '下载完成',
            'msg_error': '发生错误',
            'msg_rate_limit': '遇到速率限制，请稍后重试',
            'msg_network_error': '网络错误',
            'msg_file_exists': '文件已存在',
            'msg_invalid_url': '无效的 URL',
            
            # 帮助文本
            'usage': '用法',
            'options': '选项',
            'examples': '示例',
            'description': '描述',
            'arguments': '参数',
            
            # CLI标题
            'cli_title': 'DeviantArt Downloader - 统一命令行工具',
            'cli_batch_download': '批量下载',
            'cli_url_download': 'URL 下载',
            'cli_tools': '工具',
            'cli_info': '信息',
            'cli_common_options': '通用选项',
            'cli_quick_examples': '快速示例',
            'cli_get_more_help': '获取更多帮助',
            'cli_architecture': '架构说明',
            
            # 命令描述
            'cmd_gallery': '下载画廊作品',
            'cmd_search': '搜索并下载',
            'cmd_fav': '下载收藏夹',
            'cmd_url': '下载单个作品',
            'cmd_artist': '下载作者所有作品',
            'cmd_login': '登录管理（多种方式）',
            'cmd_anti_ban': '查看防封IP指南',
            'cmd_test': '测试下载（下载1个文件）',
            'cmd_config': '查看/编辑配置',
            'cmd_help': '查看帮助',
            'cmd_version': '查看版本信息',
            'cmd_docs': '查看文档列表',
        }
    
    def _get_en_translations(self) -> Dict[str, str]:
        """English translations"""
        return {
            # General
            'app_name': 'DeviantArt Downloader',
            'version': 'Version',
            'help': 'Help',
            'error': 'Error',
            'warning': 'Warning',
            'success': 'Success',
            'cancel': 'Cancel',
            'yes': 'Yes',
            'no': 'No',
            
            # Commands
            'command_gallery': 'Download Gallery',
            'command_search': 'Search & Download',
            'command_fav': 'Download Favorites',
            'command_url': 'URL Download',
            'command_artist': 'Artist Download',
            'command_login': 'Login Manager',
            'command_anti_ban': 'Anti-Ban Guide',
            'command_config': 'Configuration',
            'command_version': 'Version Info',
            'command_docs': 'Documentation',
            
            # Download Status
            'downloading': 'Downloading',
            'downloaded': 'Downloaded',
            'failed': 'Failed',
            'skipped': 'Skipped',
            'exists': 'Already Exists',
            
            # Quality
            'quality_original': 'Original',
            'quality_full': 'Full',
            'quality_preview': 'Preview',
            
            # Login
            'login_required': 'Login Required',
            'login_optional': 'Login Optional',
            'cookie_loaded': 'Cookie Loaded',
            'cookie_missing': 'Cookie Not Found',
            'auth_success': 'Authentication Successful',
            'auth_failed': 'Authentication Failed',
            
            # Messages
            'msg_start': 'Starting download',
            'msg_complete': 'Download complete',
            'msg_error': 'An error occurred',
            'msg_rate_limit': 'Rate limit reached, please try again later',
            'msg_network_error': 'Network error',
            'msg_file_exists': 'File already exists',
            'msg_invalid_url': 'Invalid URL',
            
            # Help text
            'usage': 'Usage',
            'options': 'Options',
            'examples': 'Examples',
            'description': 'Description',
            'arguments': 'Arguments',
            
            # CLI titles
            'cli_title': 'DeviantArt Downloader - Unified CLI',
            'cli_batch_download': 'Batch Download',
            'cli_url_download': 'URL Download',
            'cli_tools': 'Tools',
            'cli_info': 'Information',
            'cli_common_options': 'Common Options',
            'cli_quick_examples': 'Quick Examples',
            'cli_get_more_help': 'Get More Help',
            'cli_architecture': 'Architecture',
            
            # Command descriptions
            'cmd_gallery': 'Download gallery artworks',
            'cmd_search': 'Search and download',
            'cmd_fav': 'Download favorites',
            'cmd_url': 'Download single artwork',
            'cmd_artist': 'Download all artworks from artist',
            'cmd_login': 'Login management (multiple methods)',
            'cmd_anti_ban': 'View anti-ban guide',
            'cmd_test': 'Test download (1 file)',
            'cmd_config': 'View/edit configuration',
            'cmd_help': 'Show help',
            'cmd_version': 'Show version info',
            'cmd_docs': 'Show documentation list',
        }
    
    def t(self, key: str, **kwargs) -> str:
        """
        翻译文本
        
        Args:
            key: 翻译键
            **kwargs: 格式化参数
        
        Returns:
            翻译后的文本
        """
        text = self.translations.get(self.current_lang, {}).get(key, key)
        
        if kwargs:
            try:
                return text.format(**kwargs)
            except:
                return text
        
        return text
    
    def set_language(self, lang: str) -> bool:
        """设置语言"""
        lang = self._normalize_lang(lang)
        if lang in self.translations:
            self.current_lang = lang
            return True
        return False
    
    def get_language(self) -> str:
        """获取当前语言"""
        return self.current_lang
    
    def get_language_name(self) -> str:
        """获取当前语言名称"""
        return self.SUPPORTED_LANGUAGES.get(self.current_lang, 'Unknown')


# 全局实例
_i18n_instance: Optional[I18n] = None


def init_i18n(lang: Optional[str] = None) -> I18n:
    """初始化国际化"""
    global _i18n_instance
    _i18n_instance = I18n(lang)
    return _i18n_instance


def get_i18n() -> I18n:
    """获取国际化实例"""
    global _i18n_instance
    if _i18n_instance is None:
        _i18n_instance = I18n()
    return _i18n_instance


def t(key: str, **kwargs) -> str:
    """翻译快捷方式"""
    return get_i18n().t(key, **kwargs)


def set_language(lang: str) -> bool:
    """设置语言"""
    return get_i18n().set_language(lang)


def get_language() -> str:
    """获取当前语言"""
    return get_i18n().get_language()


# 命令行工具
def main():
    """命令行工具"""
    import sys
    
    if '--help' in sys.argv or '-h' in sys.argv:
        print("""
DeviantArt Downloader - 国际化 (i18n) 工具

用法:
  python i18n.py [options]

选项:
  --lang=<code>     设置语言 (zh_CN, en_US)
  --test            测试翻译
  --list            列出支持的语言

示例:
  python i18n.py --lang=zh_CN --test
  python i18n.py --list
  
环境变量:
  DEVART_LANG       设置默认语言
  LANG              系统语言（自动检测）
""")
        return
    
    if '--list' in sys.argv:
        print("支持的语言 / Supported Languages:")
        for code, name in I18n.SUPPORTED_LANGUAGES.items():
            print(f"  {code:8} - {name}")
        return
    
    # 检测语言参数
    lang = None
    for arg in sys.argv:
        if arg.startswith('--lang='):
            lang = arg.split('=')[1]
    
    # 初始化
    i18n = init_i18n(lang)
    
    print(f"当前语言 / Current Language: {i18n.get_language_name()} ({i18n.get_language()})")
    
    if '--test' in sys.argv:
        print("\n测试翻译 / Testing translations:\n")
        
        test_keys = [
            'app_name',
            'command_gallery',
            'downloading',
            'quality_original',
            'auth_success',
            'msg_complete',
        ]
        
        for key in test_keys:
            print(f"  {key:20} -> {i18n.t(key)}")


if __name__ == '__main__':
    main()
