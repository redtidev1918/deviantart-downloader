#!/usr/bin/env python3
"""
通用 Cookie 加载器
从多个来源加载 DeviantArt Cookie
"""

import os
import json
from pathlib import Path
from typing import Optional
from datetime import datetime


def load_cookies(cookie_file: Optional[str] = None) -> Optional[str]:
    """
    从多个来源加载 Cookie
    
    优先级:
    1. 指定的 cookie_file 参数
    2. 环境变量 DEVIANTART_COOKIES
    3. .env 文件
    4. cookies.txt
    5. 会话文件 ~/.deviantart_dl/session.json
    
    Args:
        cookie_file: 指定的 Cookie 文件路径
    
    Returns:
        Cookie 字符串，如果未找到返回 None
    """
    
    # 优先级1: 指定的文件
    if cookie_file and Path(cookie_file).exists():
        try:
            return Path(cookie_file).read_text().strip()
        except:
            pass
    
    # 优先级2: 环境变量
    if 'DEVIANTART_COOKIES' in os.environ:
        cookies = os.environ['DEVIANTART_COOKIES'].strip()
        if cookies:
            return cookies
    
    # 优先级3: .env 文件
    env_file = Path('.env')
    if env_file.exists():
        try:
            for line in env_file.read_text().splitlines():
                if line.strip().startswith('DEVIANTART_COOKIES='):
                    cookies = line.split('=', 1)[1].strip().strip('"\'')
                    if cookies:
                        return cookies
        except:
            pass
    
    # 优先级4: cookies.txt
    cookie_txt = Path('cookies.txt')
    if cookie_txt.exists():
        try:
            cookies = cookie_txt.read_text().strip()
            if cookies:
                return cookies
        except:
            pass
    
    # 优先级5: 会话文件
    session_file = Path.home() / '.deviantart_dl' / 'session.json'
    if session_file.exists():
        try:
            with open(session_file) as f:
                data = json.load(f)
                
                # 检查是否过期
                if 'expires_at' in data:
                    expires_at = datetime.fromisoformat(data['expires_at'])
                    if datetime.now() > expires_at:
                        # 会话已过期
                        return None
                
                cookies = data.get('cookies', '').strip()
                if cookies:
                    return cookies
        except:
            pass
    
    return None


def get_cookie_source(cookie_file: Optional[str] = None) -> str:
    """
    获取 Cookie 来源描述
    
    Returns:
        来源描述字符串
    """
    if cookie_file and Path(cookie_file).exists():
        return f"文件: {cookie_file}"
    
    if 'DEVIANTART_COOKIES' in os.environ:
        return "环境变量"
    
    env_file = Path('.env')
    if env_file.exists():
        try:
            for line in env_file.read_text().splitlines():
                if line.strip().startswith('DEVIANTART_COOKIES='):
                    return ".env 文件"
        except:
            pass
    
    cookie_txt = Path('cookies.txt')
    if cookie_txt.exists():
        return "cookies.txt"
    
    session_file = Path.home() / '.deviantart_dl' / 'session.json'
    if session_file.exists():
        return f"会话文件: {session_file}"
    
    return "未找到"


def has_cookies(cookie_file: Optional[str] = None) -> bool:
    """
    检查是否有可用的 Cookie
    
    Returns:
        是否找到 Cookie
    """
    return load_cookies(cookie_file) is not None


def main():
    """测试 Cookie 加载"""
    print("=" * 70)
    print("  Cookie 加载器测试")
    print("=" * 70)
    print()
    
    cookies = load_cookies()
    source = get_cookie_source()
    
    if cookies:
        print("✓ 找到 Cookie")
        print(f"  来源: {source}")
        print(f"  长度: {len(cookies)} 字符")
        print(f"  预览: {cookies[:50]}..." if len(cookies) > 50 else cookies)
    else:
        print("✗ 未找到 Cookie")
        print()
        print("请使用以下方式之一设置 Cookie:")
        print("  1. devart-dl login interactive")
        print("  2. 创建 cookies.txt 文件")
        print("  3. 设置环境变量: export DEVIANTART_COOKIES=\"...\"")
        print("  4. 在 .env 文件中设置 DEVIANTART_COOKIES=...")
    
    print()
    print("=" * 70)


if __name__ == '__main__':
    main()
