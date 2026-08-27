#!/usr/bin/env python3
"""
多种登录方式管理器
支持：Cookie文件、环境变量、交互式输入、Session保存
"""

import os
import json
from pathlib import Path
from typing import Dict
from datetime import datetime, timedelta

# 颜色
class C:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    RESET = '\033[0m'


class MultiAuthManager:
    """支持多种登录方式的认证管理器"""
    
    def __init__(self):
        self.cookies: str = ""
        self.auth_method: str = ""
        self.session_file = Path.home() / ".deviantart_dl" / "session.json"
        
    def authenticate(self, method: str = "auto") -> tuple[bool, str]:
        """
        认证主入口
        
        Args:
            method: 认证方式
                - auto: 自动选择（推荐）
                - file: Cookie 文件
                - env: 环境变量
                - input: 交互式输入
                - session: 已保存的会话
        
        Returns:
            (成功标志, Cookie字符串)
        """
        if method == "auto":
            return self._auto_authenticate()
        elif method == "file":
            return self._authenticate_from_file()
        elif method == "env":
            return self._authenticate_from_env()
        elif method == "input":
            return self._authenticate_interactive()
        elif method == "session":
            return self._authenticate_from_session()
        else:
            print(f"{C.RED}✗ 未知的认证方式: {method}{C.RESET}")
            return False, ""
    
    def _auto_authenticate(self) -> tuple[bool, str]:
        """自动选择最佳认证方式"""
        print(f"{C.BLUE}🔐 自动选择认证方式...{C.RESET}")
        
        # 1. 尝试会话文件（最快）
        if self.session_file.exists():
            success, cookies = self._authenticate_from_session()
            if success:
                print(f"{C.GREEN}✓ 使用已保存的会话{C.RESET}")
                return True, cookies
        
        # 2. 尝试环境变量
        success, cookies = self._authenticate_from_env()
        if success:
            print(f"{C.GREEN}✓ 从环境变量加载{C.RESET}")
            return True, cookies
        
        # 3. 尝试 Cookie 文件
        success, cookies = self._authenticate_from_file()
        if success:
            print(f"{C.GREEN}✓ 从 Cookie 文件加载{C.RESET}")
            return True, cookies
        
        # 4. 未找到任何认证
        print(f"{C.YELLOW}⚠ 未找到登录信息（某些功能可能受限）{C.RESET}")
        return False, ""
    
    def _authenticate_from_file(self, path: str = "cookies.txt") -> tuple[bool, str]:
        """从 Cookie 文件加载"""
        cookie_path = Path(path)
        
        if not cookie_path.exists():
            return False, ""
        
        try:
            with open(cookie_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
            # 移除注释
            lines = [line.strip() for line in content.split('\n')
                    if line.strip() and not line.strip().startswith('#')]
            cookies = ' '.join(lines)
            
            if self._validate_cookies(cookies):
                self.cookies = cookies
                self.auth_method = "file"
                return True, cookies
            
            return False, ""
        except Exception as e:
            print(f"{C.RED}✗ 读取 Cookie 文件失败: {e}{C.RESET}")
            return False, ""
    
    def _authenticate_from_env(self) -> tuple[bool, str]:
        """从环境变量加载"""
        # 尝试多个环境变量名
        env_vars = [
            'DEVIANTART_COOKIES',
            'DA_COOKIES',
            'DEVART_COOKIES',
        ]
        
        for var in env_vars:
            cookies = os.getenv(var, '').strip()
            if cookies and self._validate_cookies(cookies):
                self.cookies = cookies
                self.auth_method = "env"
                return True, cookies
        
        return False, ""
    
    def _authenticate_interactive(self) -> tuple[bool, str]:
        """交互式输入 Cookie"""
        print(f"\n{C.BLUE}═══════════════════════════════════════════════════════{C.RESET}")
        print(f"{C.BLUE}        交互式 Cookie 输入{C.RESET}")
        print(f"{C.BLUE}═══════════════════════════════════════════════════════{C.RESET}\n")
        
        print(f"{C.YELLOW}如何获取 Cookie：{C.RESET}")
        print("1. 在浏览器中登录 DeviantArt")
        print("2. 打开开发者工具 (F12)")
        print("3. 切换到 'Network' 标签")
        print("4. 刷新页面")
        print("5. 点击任意请求，查看 'Cookie' 请求头")
        print("6. 复制完整的 Cookie 字符串\n")
        
        print(f"{C.GREEN}请粘贴 Cookie 内容（输入后按回车）：{C.RESET}")
        cookies = input().strip()
        
        if not cookies:
            print(f"{C.RED}✗ Cookie 为空{C.RESET}")
            return False, ""
        
        if self._validate_cookies(cookies):
            self.cookies = cookies
            self.auth_method = "input"
            
            # 询问是否保存
            save = input(f"\n{C.YELLOW}是否保存为会话文件？(y/n): {C.RESET}").lower()
            if save in ['y', 'yes', '是']:
                self._save_session(cookies)
            
            return True, cookies
        else:
            print(f"{C.RED}✗ Cookie 格式无效{C.RESET}")
            return False, ""
    
    def _authenticate_from_session(self) -> tuple[bool, str]:
        """从保存的会话文件加载"""
        if not self.session_file.exists():
            return False, ""
        
        try:
            with open(self.session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            
            # 检查会话是否过期
            saved_time = datetime.fromisoformat(session_data.get('saved_at', ''))
            if datetime.now() - saved_time > timedelta(days=30):
                print(f"{C.YELLOW}⚠ 会话已过期（超过30天）{C.RESET}")
                return False, ""
            
            cookies = session_data.get('cookies', '')
            if self._validate_cookies(cookies):
                self.cookies = cookies
                self.auth_method = "session"
                return True, cookies
            
            return False, ""
        except Exception:
            return False, ""
    
    def _save_session(self, cookies: str) -> bool:
        """保存会话到文件"""
        try:
            # 创建目录
            self.session_file.parent.mkdir(parents=True, exist_ok=True)
            
            session_data = {
                'cookies': cookies,
                'saved_at': datetime.now().isoformat(),
                'method': self.auth_method,
            }
            
            with open(self.session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2)
            
            # 设置文件权限（仅用户可读写）
            os.chmod(self.session_file, 0o600)
            
            print(f"{C.GREEN}✓ 会话已保存: {self.session_file}{C.RESET}")
            return True
        except Exception as e:
            print(f"{C.RED}✗ 保存会话失败: {e}{C.RESET}")
            return False
    
    def _validate_cookies(self, cookies: str) -> bool:
        """验证 Cookie 格式"""
        if not cookies:
            return False
        
        # 检查是否包含认证相关的 Cookie
        auth_indicators = ['auth=', 'auth_secure=', 'userinfo=']
        return any(indicator in cookies for indicator in auth_indicators)
    
    def clear_session(self) -> bool:
        """清除保存的会话"""
        if self.session_file.exists():
            try:
                self.session_file.unlink()
                print(f"{C.GREEN}✓ 会话已清除{C.RESET}")
                return True
            except Exception as e:
                print(f"{C.RED}✗ 清除会话失败: {e}{C.RESET}")
                return False
        return True
    
    def get_cookies(self) -> str:
        """获取当前 Cookie"""
        return self.cookies
    
    def is_authenticated(self) -> bool:
        """检查是否已认证"""
        return bool(self.cookies and self.auth_method)
    
    def get_auth_info(self) -> Dict[str, str]:
        """获取认证信息"""
        return {
            'method': self.auth_method,
            'authenticated': str(self.is_authenticated()),
            'session_exists': str(self.session_file.exists()),
        }


def print_login_guide():
    """打印登录方式指南"""
    print(f"""
{C.BLUE}╔══════════════════════════════════════════════════════════════════════╗
║                    多种登录方式指南                                    ║
╚══════════════════════════════════════════════════════════════════════╝{C.RESET}

{C.GREEN}方式1: Cookie 文件（推荐）{C.RESET}

  1. 创建 cookies.txt 文件
  2. 粘贴从浏览器获取的 Cookie
  3. 运行下载命令

  优点: ✓ 简单方便  ✓ 可重复使用  ✓ 易于备份
  
{C.GREEN}方式2: 环境变量{C.RESET}

  设置环境变量：
  export DEVIANTART_COOKIES="auth=xxx; auth_secure=xxx; ..."
  
  或在 .env 文件中：
  DEVIANTART_COOKIES=auth=xxx; auth_secure=xxx; ...
  
  优点: ✓ 安全  ✓ 适合CI/CD  ✓ 不留本地文件
  
{C.GREEN}方式3: 交互式输入{C.RESET}

  运行命令：
  python auth_manager.py --method=input
  
  按提示粘贴 Cookie
  
  优点: ✓ 灵活  ✓ 可选择保存  ✓ 适合测试
  
{C.GREEN}方式4: 会话保存{C.RESET}

  首次输入后自动保存到：
  ~/.deviantart_dl/session.json
  
  下次自动使用
  
  优点: ✓ 最方便  ✓ 自动加载  ✓ 30天有效期
  
{C.BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{C.RESET}

{C.YELLOW}如何获取 Cookie：{C.RESET}

  Chrome/Edge:
    1. 登录 DeviantArt
    2. F12 打开开发者工具
    3. Network 标签
    4. 刷新页面
    5. 点击任意请求 → Headers
    6. 复制 Cookie 请求头
  
  Firefox:
    1. 登录 DeviantArt
    2. F12 打开开发者工具
    3. 网络标签
    4. 刷新页面
    5. 点击请求 → 标头
    6. 复制 Cookie
  
  Safari:
    1. 登录 DeviantArt
    2. 开发 → 显示网页检查器
    3. 网络标签
    4. 刷新页面
    5. 查看 Cookie 请求头

{C.BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{C.RESET}

{C.YELLOW}命令示例：{C.RESET}

  # 自动选择（推荐）
  devart-dl gallery username
  
  # 指定 Cookie 文件
  devart-dl gallery username --cookies=./my_cookies.txt
  
  # 使用环境变量
  export DEVIANTART_COOKIES="..."
  devart-dl gallery username
  
  # 交互式输入
  python auth_manager.py --method=input
  
  # 清除会话
  python auth_manager.py --clear-session

{C.BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{C.RESET}

{C.GREEN}需要登录的功能：{C.RESET}
  • 下载原图（--quality=o）
  • 访问成熟内容
  • 查看私密作品
  • 访问收藏夹

{C.YELLOW}不需要登录的功能：{C.RESET}
  • 下载全图（--quality=f）
  • 下载预览图（--quality=p）
  • 公开作品
  • 大部分画廊内容
""")


def main():
    """主函数 - 测试和管理认证"""
    import sys
    
    if '--help' in sys.argv or '-h' in sys.argv:
        print_login_guide()
        return
    
    auth = MultiAuthManager()
    
    if '--clear-session' in sys.argv:
        auth.clear_session()
        return
    
    if '--method=input' in sys.argv:
        success, cookies = auth.authenticate(method="input")
    else:
        # 默认自动模式
        success, cookies = auth.authenticate(method="auto")
    
    if success:
        print(f"\n{C.GREEN}✓ 认证成功{C.RESET}")
        info = auth.get_auth_info()
        print(f"  方式: {info['method']}")
        print(f"  Cookie 长度: {len(cookies)} 字符")
    else:
        print(f"\n{C.YELLOW}未登录（公开内容仍可访问）{C.RESET}")
        print(f"\n运行 {C.GREEN}python auth_manager.py --help{C.RESET} 查看登录指南")


if __name__ == "__main__":
    main()
