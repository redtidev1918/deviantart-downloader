"""认证和 Cookie 管理模块"""

import os
import logging
from typing import Optional
import requests


logger = logging.getLogger(__name__)


class AuthManager:
    """认证管理器 - 处理 Cookie 和登录状态"""
    
    def __init__(self, cookies_path: str = "cookies.txt"):
        self.cookies_path = cookies_path
        self.cookies: str = ""
        self.is_logged_in: bool = False
        
    def load_cookies(self) -> str:
        """加载 Cookie 文件"""
        if not os.path.isfile(self.cookies_path):
            logger.info(f"No cookie file found at {self.cookies_path} (optional for public content)")
            return ""
        
        try:
            with open(self.cookies_path, 'r', encoding='utf-8') as f:
                cookies = f.read().strip()
            
            # 移除注释行
            lines = [line.strip() for line in cookies.split('\n') 
                    if line.strip() and not line.strip().startswith('#')]
            cookies = ' '.join(lines)
            
            if cookies:
                logger.info(f"✓ Loaded cookies from: {self.cookies_path}")
                self.cookies = cookies
                return cookies
            else:
                logger.warning(f"Cookie file is empty: {self.cookies_path}")
                return ""
        except Exception as e:
            logger.error(f"Error loading cookies: {e}")
            return ""
    
    def validate_cookies(self, cookies: Optional[str] = None) -> bool:
        """验证 Cookie 是否包含认证信息"""
        if cookies is None:
            cookies = self.cookies
        
        if not cookies:
            return False
        
        # 检查关键的认证 Cookie
        auth_indicators = ['auth=', 'auth_secure=', 'userinfo=']
        has_auth = any(indicator in cookies for indicator in auth_indicators)
        
        if has_auth:
            logger.info("✓ Cookies appear valid (contains auth tokens)")
        else:
            logger.warning("⚠ Cookies may be invalid or incomplete")
        
        return has_auth
    
    def check_login_status(self, headers: dict, proxies: dict) -> bool:
        """检查登录状态"""
        try:
            response = requests.get(
                'https://www.deviantart.com',
                headers=headers,
                proxies=proxies,
                timeout=10
            )
            
            if 'window.__CSRF_TOKEN__' in response.text:
                if 'data-userid' in response.text or '"isLoggedIn":true' in response.text:
                    logger.info("✓ Successfully logged in!")
                    self.is_logged_in = True
                    return True
                else:
                    logger.info("! Not logged in (public access only)")
                    self.is_logged_in = False
                    return False
        except Exception as e:
            logger.warning(f"Could not verify login status: {e}")
            return False
    
    def reload_cookies(self) -> str:
        """重新加载 Cookie"""
        logger.info("Reloading cookies...")
        return self.load_cookies()
    
    @staticmethod
    def show_login_guide():
        """显示登录指南"""
        guide = '''
╔══════════════════════════════════════════════════════════════════════╗
║                    HOW TO GET DEVIANTART COOKIES                     ║
╚══════════════════════════════════════════════════════════════════════╝

1. Open DeviantArt in your browser and LOGIN to your account
   → https://www.deviantart.com

2. Open Browser Developer Tools:
   • Chrome/Edge: Press F12 or Ctrl+Shift+I (Cmd+Option+I on Mac)
   • Firefox: Press F12 or Ctrl+Shift+I (Cmd+Option+I on Mac)

3. Go to "Application" tab (Chrome) or "Storage" tab (Firefox)

4. In the left sidebar, expand "Cookies" and click on:
   → https://www.deviantart.com

5. Copy ALL cookie values in this format:
   cookie1=value1; cookie2=value2; cookie3=value3

   Important cookies to include:
   • auth
   • auth_secure
   • userinfo

6. Paste the copied cookies into a file named "cookies.txt"
   in the same folder as this script

Alternatively, you can use browser extensions like:
• "EditThisCookie" (Chrome)
• "Cookie-Editor" (Firefox/Chrome)

'''
        print(guide)
    
    def prompt_for_cookies(self, require_auth: bool = False) -> bool:
        """提示用户配置 Cookie"""
        if not self.cookies:
            print("! Running without cookies - only public content accessible")
            
            if require_auth:
                print("\n⚠ WARNING: This operation requires login!")
                answer = input("Show login guide? (y/n): ").lower()
                if answer in ['y', 'yes']:
                    self.show_login_guide()
                    input("\nPress Enter after setting up cookies, or Ctrl+C to exit...")
                    self.cookies = self.reload_cookies()
                    return bool(self.cookies)
        
        elif not self.validate_cookies():
            answer = input("Do you want to see the cookie setup guide? (y/n): ").lower()
            if answer in ['y', 'yes']:
                self.show_login_guide()
        
        return bool(self.cookies)
