#!/usr/bin/env python3
"""
Cookie 验证工具
验证 DeviantArt Cookie 是否合法可用

使用方法:
    python validate_cookies.py
    python validate_cookies.py --cookies="auth=xxx; ..."
    devart-dl login validate
"""

import sys
import os
import json
import requests
from pathlib import Path
from typing import Dict, Optional, Tuple

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from tools.logger import get_logger
    logger = get_logger()
except:
    import logging
    logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.INFO)


class CookieValidator:
    """Cookie 验证器"""
    
    # DeviantArt API 端点
    WHOAMI_URL = "https://www.deviantart.com/_napi/da-user-profile/api/init/about"
    PROFILE_URL = "https://www.deviantart.com/_napi/shared_api/user/info"
    
    def __init__(self, cookies: Optional[str] = None):
        """
        初始化验证器
        
        Args:
            cookies: Cookie 字符串
        """
        self.cookies = cookies or self._load_cookies()
        self.session = requests.Session()
        self._setup_session()
    
    def _load_cookies(self) -> Optional[str]:
        """从文件或环境变量加载 Cookie"""
        # 1. 从环境变量
        if 'DEVIANTART_COOKIES' in os.environ:
            return os.environ['DEVIANTART_COOKIES']
        
        # 2. 从 cookies.txt
        cookie_file = Path('cookies.txt')
        if cookie_file.exists():
            return cookie_file.read_text().strip()
        
        # 3. 从会话文件
        session_file = Path.home() / '.deviantart_dl' / 'session.json'
        if session_file.exists():
            try:
                with open(session_file) as f:
                    data = json.load(f)
                    return data.get('cookies')
            except:
                pass
        
        return None
    
    def _setup_session(self):
        """设置请求会话"""
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.deviantart.com/',
        })
        
        if self.cookies:
            # 解析 Cookie 字符串
            cookie_dict = {}
            for item in self.cookies.split(';'):
                if '=' in item:
                    key, value = item.strip().split('=', 1)
                    cookie_dict[key] = value
            
            # 设置到 session
            for key, value in cookie_dict.items():
                self.session.cookies.set(key, value, domain='.deviantart.com')
    
    def validate(self) -> Tuple[bool, Dict]:
        """
        验证 Cookie
        
        Returns:
            (is_valid, info) - 是否有效和用户信息
        """
        if not self.cookies:
            return False, {'error': 'No cookies provided'}
        
        result = {
            'valid': False,
            'logged_in': False,
            'username': None,
            'user_id': None,
            'is_premium': False,
            'cookies_found': {},
            'errors': []
        }
        
        # 检查必要的 Cookie
        cookie_dict = {}
        for item in self.cookies.split(';'):
            if '=' in item:
                key, value = item.strip().split('=', 1)
                cookie_dict[key] = value
        
        result['cookies_found'] = {
            'auth': 'auth' in cookie_dict,
            'auth_secure': 'auth_secure' in cookie_dict,
            'userinfo': 'userinfo' in cookie_dict,
        }
        
        # 测试1: 检查基本登录状态
        try:
            response = self.session.get(
                'https://www.deviantart.com/',
                timeout=10
            )
            
            # 检查是否重定向到登录页
            if 'users/login' in response.url:
                result['errors'].append('Redirected to login page - cookies expired')
                return False, result
            
            # 检查页面内容
            if 'isLoggedIn":true' in response.text or '"loggedIn":true' in response.text:
                result['logged_in'] = True
            
        except Exception as e:
            result['errors'].append(f'Basic check failed: {str(e)}')
        
        # 测试2: 获取用户信息
        try:
            response = self.session.get(
                self.WHOAMI_URL,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # 提取用户信息
                if 'user' in data:
                    user = data['user']
                    result['username'] = user.get('username')
                    result['user_id'] = user.get('userId')
                    result['is_premium'] = user.get('isPremium', False)
                    result['logged_in'] = True
                    result['valid'] = True
                elif 'error' in data:
                    result['errors'].append(f"API Error: {data['error']}")
            else:
                result['errors'].append(f'API returned status {response.status_code}')
                
        except Exception as e:
            result['errors'].append(f'User info check failed: {str(e)}')
        
        # 测试3: 测试下载权限
        if result['logged_in']:
            try:
                test_url = 'https://www.deviantart.com/browse'
                response = self.session.get(test_url, timeout=10)
                if response.status_code == 200:
                    result['can_browse'] = True
            except:
                result['can_browse'] = False
        
        return result['valid'], result
    
    def print_result(self, is_valid: bool, info: Dict):
        """打印验证结果"""
        print("\n" + "=" * 70)
        print("  🍪 Cookie 验证结果")
        print("=" * 70)
        print()
        
        # 总体状态
        if is_valid:
            print("✅ Cookie 有效且可用！")
        else:
            print("❌ Cookie 无效或已过期")
        
        print()
        print("-" * 70)
        
        # Cookie 存在性检查
        print("\n📋 Cookie 检查:")
        cookies = info.get('cookies_found', {})
        for name, exists in cookies.items():
            status = "✓" if exists else "✗"
            print(f"  {status} {name}: {'找到' if exists else '未找到'}")
        
        # 登录状态
        print("\n🔐 登录状态:")
        if info.get('logged_in'):
            print("  ✓ 已登录")
            if info.get('username'):
                print(f"  👤 用户名: {info['username']}")
            if info.get('user_id'):
                print(f"  🆔 用户ID: {info['user_id']}")
            if info.get('is_premium'):
                print("  ⭐ Core/Premium 用户")
        else:
            print("  ✗ 未登录")
        
        # 权限检查
        if info.get('can_browse') is not None:
            print("\n🔍 权限检查:")
            if info['can_browse']:
                print("  ✓ 可以浏览内容")
            else:
                print("  ✗ 无法浏览内容")
        
        # 错误信息
        if info.get('errors'):
            print("\n⚠️  错误信息:")
            for error in info['errors']:
                print(f"  • {error}")
        
        # 建议
        print("\n💡 建议:")
        if not is_valid:
            print("  1. Cookie 可能已过期，请重新登录")
            print("  2. 运行: devart-dl login interactive")
            print("  3. 或使用浏览器登录后重新导出 Cookie")
        else:
            print("  ✓ Cookie 工作正常，可以开始下载！")
            print("  • 运行: devart-dl gallery <username>")
            print("  • 运行: devart-dl url <artwork_url>")
        
        print("\n" + "=" * 70)
        print()


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='验证 DeviantArt Cookie')
    parser.add_argument('--cookies', help='Cookie 字符串')
    parser.add_argument('--json', action='store_true', help='输出 JSON 格式')
    parser.add_argument('-q', '--quiet', action='store_true', help='安静模式')
    
    args = parser.parse_args()
    
    # 创建验证器
    validator = CookieValidator(cookies=args.cookies)
    
    if not validator.cookies:
        print("❌ 错误: 未找到 Cookie")
        print()
        print("请使用以下方式之一提供 Cookie:")
        print("  1. 命令行参数: --cookies=\"auth=xxx; ...\"")
        print("  2. 环境变量: export DEVIANTART_COOKIES=\"...\"")
        print("  3. 文件: cookies.txt")
        print("  4. 会话文件: ~/.deviantart_dl/session.json")
        print()
        print("获取 Cookie:")
        print("  devart-dl login interactive")
        print("  或参考: tools/COOKIE_EXPORT_GUIDE.md")
        return 1
    
    if not args.quiet:
        print("正在验证 Cookie...")
    
    # 执行验证
    is_valid, info = validator.validate()
    
    # 输出结果
    if args.json:
        print(json.dumps(info, indent=2, ensure_ascii=False))
    else:
        validator.print_result(is_valid, info)
    
    # 返回状态码
    return 0 if is_valid else 1


if __name__ == '__main__':
    sys.exit(main())
