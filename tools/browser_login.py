#!/usr/bin/env python3
"""
浏览器自动登录工具
通过 Selenium 打开浏览器，让用户登录后自动提取 Cookie
"""

import sys
import json
import time
from pathlib import Path
from typing import Optional, Dict

# 颜色
class C:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    RESET = '\033[0m'


class BrowserLogin:
    """浏览器登录管理器"""
    
    def __init__(self, headless: bool = False):
        self.headless = headless
        self.driver = None
        self.cookies_file = Path("cookies.txt")
        
    def _check_selenium(self) -> bool:
        """检查 Selenium 是否已安装"""
        try:
            import selenium
            from selenium import webdriver
            return True
        except ImportError:
            return False
    
    def _install_selenium_guide(self):
        """显示 Selenium 安装指南"""
        print(f"""
{C.YELLOW}═══════════════════════════════════════════════════════════════════════{C.RESET}
{C.YELLOW}  Selenium 未安装{C.RESET}
{C.YELLOW}═══════════════════════════════════════════════════════════════════════{C.RESET}

{C.BOLD}需要安装 Selenium 才能使用浏览器登录功能{C.RESET}

{C.GREEN}安装方法：{C.RESET}

  {C.BLUE}1. 安装 Selenium{C.RESET}
     pip install selenium

  {C.BLUE}2. 安装浏览器驱动（选择一个）{C.RESET}
  
     {C.GREEN}方式 A: Chrome (推荐){C.RESET}
     pip install webdriver-manager
     
     {C.GREEN}方式 B: Firefox{C.RESET}
     pip install webdriver-manager
     
     {C.GREEN}方式 C: 手动下载{C.RESET}
     - Chrome: https://chromedriver.chromium.org/
     - Firefox: https://github.com/mozilla/geckodriver/releases

{C.BOLD}安装后重新运行此命令{C.RESET}
""")
    
    def login(self, browser: str = "chrome", save: bool = True) -> Optional[str]:
        """
        通过浏览器登录
        
        Args:
            browser: 浏览器类型 (chrome, firefox, edge)
            save: 是否保存 Cookie 到文件
        
        Returns:
            Cookie 字符串或 None
        """
        # 检查 Selenium
        if not self._check_selenium():
            self._install_selenium_guide()
            return None
        
        try:
            from selenium import webdriver
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
        except ImportError as e:
            print(f"{C.RED}导入错误: {e}{C.RESET}")
            self._install_selenium_guide()
            return None
        
        print(f"{C.BLUE}{'='*70}{C.RESET}")
        print(f"{C.BLUE}  浏览器自动登录{C.RESET}")
        print(f"{C.BLUE}{'='*70}{C.RESET}\n")
        
        try:
            # 创建浏览器实例
            print(f"{C.YELLOW}正在启动 {browser.title()} 浏览器...{C.RESET}")
            self.driver = self._create_driver(browser)
            
            if not self.driver:
                return None
            
            # 打开 DeviantArt 登录页
            login_url = "https://www.deviantart.com/users/login"
            print(f"{C.BLUE}正在打开登录页...{C.RESET}")
            self.driver.get(login_url)
            
            # 等待用户登录
            print(f"\n{C.GREEN}{'='*70}{C.RESET}")
            print(f"{C.GREEN}  请在浏览器中登录 DeviantArt{C.RESET}")
            print(f"{C.GREEN}{'='*70}{C.RESET}\n")
            print(f"{C.YELLOW}提示：{C.RESET}")
            print(f"  1. 在打开的浏览器中输入用户名和密码")
            print(f"  2. 完成登录后，{C.BOLD}保持浏览器打开{C.RESET}")
            print(f"  3. 回到终端，按 {C.GREEN}Enter{C.RESET} 继续\n")
            
            input(f"{C.YELLOW}登录完成后按 Enter 键...{C.RESET}")
            
            # 检查是否登录成功
            current_url = self.driver.current_url
            if "login" in current_url.lower():
                print(f"{C.YELLOW}⚠ 似乎还未登录，是否继续？(y/n): {C.RESET}", end='')
                if input().lower() not in ['y', 'yes', '是']:
                    print(f"{C.RED}已取消{C.RESET}")
                    return None
            
            # 提取 Cookie
            print(f"\n{C.BLUE}正在提取 Cookie...{C.RESET}")
            cookies = self._extract_cookies()
            
            if not cookies:
                print(f"{C.RED}✗ 未能提取 Cookie{C.RESET}")
                return None
            
            print(f"{C.GREEN}✓ Cookie 提取成功{C.RESET}")
            print(f"  长度: {len(cookies)} 字符")
            
            # 保存 Cookie
            if save:
                if self._save_cookies(cookies):
                    print(f"{C.GREEN}✓ Cookie 已保存到: {self.cookies_file}{C.RESET}")
            
            return cookies
            
        except Exception as e:
            print(f"{C.RED}✗ 错误: {e}{C.RESET}")
            return None
        
        finally:
            # 关闭浏览器
            if self.driver:
                print(f"\n{C.YELLOW}关闭浏览器...{C.RESET}")
                try:
                    self.driver.quit()
                except:
                    pass
    
    def _create_driver(self, browser: str):
        """创建浏览器驱动"""
        from selenium import webdriver
        
        try:
            if browser.lower() == "chrome":
                return self._create_chrome_driver()
            elif browser.lower() == "firefox":
                return self._create_firefox_driver()
            elif browser.lower() == "edge":
                return self._create_edge_driver()
            else:
                print(f"{C.RED}不支持的浏览器: {browser}{C.RESET}")
                return None
        except Exception as e:
            print(f"{C.RED}创建浏览器失败: {e}{C.RESET}")
            print(f"\n{C.YELLOW}建议：{C.RESET}")
            print(f"  1. 确保已安装浏览器")
            print(f"  2. 安装 webdriver-manager: pip install webdriver-manager")
            print(f"  3. 或手动下载对应的浏览器驱动")
            return None
    
    def _create_chrome_driver(self):
        """创建 Chrome 驱动"""
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        
        options = Options()
        if self.headless:
            options.add_argument('--headless')
        
        # 尝试使用 webdriver-manager
        try:
            from webdriver_manager.chrome import ChromeDriverManager
            from selenium.webdriver.chrome.service import Service
            service = Service(ChromeDriverManager().install())
            return webdriver.Chrome(service=service, options=options)
        except:
            # 尝试直接创建
            return webdriver.Chrome(options=options)
    
    def _create_firefox_driver(self):
        """创建 Firefox 驱动"""
        from selenium import webdriver
        from selenium.webdriver.firefox.options import Options
        
        options = Options()
        if self.headless:
            options.add_argument('--headless')
        
        try:
            from webdriver_manager.firefox import GeckoDriverManager
            from selenium.webdriver.firefox.service import Service
            service = Service(GeckoDriverManager().install())
            return webdriver.Firefox(service=service, options=options)
        except:
            return webdriver.Firefox(options=options)
    
    def _create_edge_driver(self):
        """创建 Edge 驱动"""
        from selenium import webdriver
        from selenium.webdriver.edge.options import Options
        
        options = Options()
        if self.headless:
            options.add_argument('--headless')
        
        try:
            from webdriver_manager.microsoft import EdgeChromiumDriverManager
            from selenium.webdriver.edge.service import Service
            service = Service(EdgeChromiumDriverManager().install())
            return webdriver.Edge(service=service, options=options)
        except:
            return webdriver.Edge(options=options)
    
    def _extract_cookies(self) -> Optional[str]:
        """提取浏览器 Cookie"""
        if not self.driver:
            return None
        
        try:
            # 获取所有 Cookie
            cookies = self.driver.get_cookies()
            
            # 转换为字符串格式
            cookie_pairs = []
            for cookie in cookies:
                name = cookie.get('name', '')
                value = cookie.get('value', '')
                if name and value:
                    cookie_pairs.append(f"{name}={value}")
            
            cookie_string = '; '.join(cookie_pairs)
            
            # 验证是否包含认证信息
            if 'auth' in cookie_string or 'userinfo' in cookie_string:
                return cookie_string
            else:
                print(f"{C.YELLOW}⚠ Cookie 中未找到认证信息{C.RESET}")
                return cookie_string
            
        except Exception as e:
            print(f"{C.RED}提取 Cookie 失败: {e}{C.RESET}")
            return None
    
    def _save_cookies(self, cookies: str) -> bool:
        """保存 Cookie 到文件"""
        try:
            with open(self.cookies_file, 'w', encoding='utf-8') as f:
                f.write("# DeviantArt Cookies\n")
                f.write("# 自动生成于浏览器登录\n\n")
                f.write(cookies)
            return True
        except Exception as e:
            print(f"{C.RED}保存 Cookie 失败: {e}{C.RESET}")
            return False


def print_help():
    """打印帮助信息"""
    print(f"""
{C.BOLD}╔══════════════════════════════════════════════════════════════════════╗
║               浏览器自动登录 - Browser Auto Login                      ║
╚══════════════════════════════════════════════════════════════════════╝{C.RESET}

{C.GREEN}用法:{C.RESET}
  python browser_login.py [options]

{C.GREEN}选项:{C.RESET}
  --browser=<chrome|firefox|edge>  指定浏览器 (默认: chrome)
  --no-save                         不保存 Cookie 到文件
  --headless                        无头模式（后台运行）
  -h, --help                        显示此帮助

{C.GREEN}示例:{C.RESET}
  # 使用 Chrome 登录（推荐）
  python browser_login.py
  
  # 使用 Firefox
  python browser_login.py --browser=firefox
  
  # 使用 Edge
  python browser_login.py --browser=edge
  
  # 不保存 Cookie
  python browser_login.py --no-save

{C.BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{C.RESET}

{C.GREEN}工作流程:{C.RESET}
  1. 脚本自动打开浏览器
  2. 在浏览器中手动登录 DeviantArt
  3. 登录完成后按 Enter 键
  4. 脚本自动提取并保存 Cookie
  5. 之后可直接使用下载功能

{C.BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{C.RESET}

{C.GREEN}优点:{C.RESET}
  ✓ 无需手动复制 Cookie
  ✓ 可视化登录过程
  ✓ 支持多因素认证
  ✓ 自动验证和保存

{C.YELLOW}注意:{C.RESET}
  • 需要安装 Selenium: pip install selenium webdriver-manager
  • 首次运行会自动下载浏览器驱动
  • 需要系统中已安装对应浏览器

{C.BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{C.RESET}

{C.GREEN}与统一命令集成:{C.RESET}
  devart-dl login browser           # 使用浏览器登录
  devart-dl login browser --firefox # 指定浏览器
""")


def main():
    """主函数"""
    if '-h' in sys.argv or '--help' in sys.argv:
        print_help()
        return 0
    
    # 解析参数
    browser = 'chrome'
    save = True
    headless = False
    
    for arg in sys.argv[1:]:
        if arg.startswith('--browser='):
            browser = arg.split('=')[1]
        elif arg == '--no-save':
            save = False
        elif arg == '--headless':
            headless = True
    
    # 创建登录器
    login_manager = BrowserLogin(headless=headless)
    
    # 执行登录
    cookies = login_manager.login(browser=browser, save=save)
    
    if cookies:
        print(f"\n{C.GREEN}{C.BOLD}✓ 登录成功！{C.RESET}")
        if save:
            print(f"{C.GREEN}Cookie 已保存，现在可以开始下载了{C.RESET}\n")
            print(f"{C.BLUE}试试:{C.RESET}")
            print(f"  devart-dl gallery username")
            print(f"  devart-dl artist username")
        else:
            print(f"{C.YELLOW}Cookie 未保存，请手动保存以下内容到 cookies.txt:{C.RESET}")
            print(f"\n{cookies[:100]}...\n")
        return 0
    else:
        print(f"\n{C.RED}✗ 登录失败{C.RESET}")
        print(f"{C.YELLOW}请检查:{C.RESET}")
        print(f"  1. 是否已安装 Selenium")
        print(f"  2. 浏览器是否正确安装")
        print(f"  3. 是否在浏览器中成功登录")
        return 1


if __name__ == '__main__':
    sys.exit(main())
