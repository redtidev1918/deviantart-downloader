#!/usr/bin/env python3
"""
DeviantArt URL Downloader - 直接下载单个作品

支持的 URL 格式:
- https://www.deviantart.com/username/art/title-123456
- https://deviantart.com/username/art/title-123456
- https://fav.me/dxxxxxx
"""

import html
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import requests

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from tools.cookie_loader import load_cookies as load_cookies_from_sources, get_cookie_source
    from tools.file_organizer import FileOrganizer
except:
    # 备用方案
    def load_cookies_from_sources(cookie_file=None):
        return None
    def get_cookie_source(cookie_file=None):
        return "未找到"
    FileOrganizer = None

# 颜色输出
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_help():
    """显示帮助信息"""
    print(f'''
{Colors.BOLD}╔══════════════════════════════════════════════════════════════════════╗
║           DeviantArt URL Downloader - 单作品快速下载工具              ║
╚══════════════════════════════════════════════════════════════════════╝{Colors.RESET}

{Colors.BOLD}用法:{Colors.RESET}
  python download_url.py <URL> [OPTIONS]

{Colors.BOLD}支持的 URL 格式:{Colors.RESET}
  • https://www.deviantart.com/username/art/title-123456
  • https://deviantart.com/username/art/title-123456  
  • https://fav.me/dxxxxxx (短链接)

{Colors.BOLD}选项:{Colors.RESET}
  --quality=<o|f|p>   质量: o=原图, f=全图, p=预览 (默认: f)
  --dest=<PATH>       下载目录 (默认: ./downloads)
  --cookies=<PATH>    Cookie 文件路径 (默认: ./cookies.txt)
  --filename=<NAME>   自定义文件名 (不含扩展名)
  --organize=<MODE>   文件组织模式:
                      by_author  - 按作者分类 (默认)
                      by_date    - 按日期分类
                      by_type    - 按文件类型分类
                      flat       - 扁平结构
                      mixed      - 混合模式 (作者/日期)

{Colors.BOLD}示例:{Colors.RESET}
  {Colors.BLUE}# 下载全图质量{Colors.RESET}
  python download_url.py https://www.deviantart.com/user/art/artwork-123456

  {Colors.BLUE}# 下载原图 (需要登录){Colors.RESET}
  python download_url.py https://www.deviantart.com/user/art/artwork-123456 --quality=o

  {Colors.BLUE}# 指定下载目录和文件名{Colors.RESET}
  python download_url.py <URL> --dest=./my_art --filename=cool_art

  {Colors.BLUE}# 使用短链接{Colors.RESET}
  python download_url.py https://fav.me/de12345

{Colors.BOLD}注意:{Colors.RESET}
  • 下载原图 (--quality=o) 需要登录，请先配置 cookies.txt
  • 成熟内容可能需要登录才能查看
''')

def load_cookies(path: str = "cookies.txt") -> str:
    """
    加载 Cookie
    
    支持多个来源:
    1. 指定的文件
    2. 环境变量
    3. .env 文件
    4. cookies.txt
    5. 会话文件 ~/.deviantart_dl/session.json
    """
    cookies = load_cookies_from_sources(path if path != "cookies.txt" else None)
    return cookies or ""

def extract_deviation_id(url: str) -> Optional[str]:
    """从 URL 提取作品 ID"""
    # 标准格式: /art/title-123456
    match = re.search(r'/art/[^/]+-(\d+)', url)
    if match:
        return match.group(1)
    
    # fav.me 短链接
    if 'fav.me' in url:
        return None  # 需要跟随重定向
    
    return None

def resolve_short_url(url: str) -> str:
    """解析短链接"""
    try:
        response = requests.head(url, allow_redirects=True, timeout=10)
        return response.url
    except:
        return url

def get_deviation_info(url: str, cookies: str) -> dict:
    """获取作品信息"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Cookie": cookies
    }
    
    print(f"{Colors.BLUE}📡 正在获取作品信息...{Colors.RESET}")
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"{Colors.RED}✗ 无法访问 URL: {e}{Colors.RESET}")
        sys.exit(1)
    
    html_content = response.text
    
    # 提取 JSON 数据
    try:
        # 查找 window.__INITIAL_STATE__
        start_marker = 'window.__INITIAL_STATE__ = JSON.parse("'
        if start_marker in html_content:
            start = html_content.index(start_marker) + len(start_marker)
            end = html_content.index('");', start)
            json_str = html_content[start:end]
            # 解码转义
            json_str = json_str.encode().decode('unicode_escape')
            data = json.loads(json_str)
            
            # 提取 deviation 信息
            deviation = None
            if isinstance(data, dict):
                if '@@entities' in data and isinstance(data['@@entities'], dict):
                    if 'deviation' in data['@@entities']:
                        deviations = data['@@entities']['deviation']
                        # 获取第一个 deviation
                        if isinstance(deviations, dict):
                            deviation = list(deviations.values())[0] if deviations else None
                
                if deviation:
                    return deviation
    except Exception as e:
        print(f"{Colors.YELLOW}⚠ 解析 JSON 失败: {e}{Colors.RESET}")
    
    # 备用方案：查找下载链接
    print(f"{Colors.YELLOW}⚠ 使用备用解析方案{Colors.RESET}")
    return {"url": url, "html": html_content}

def get_download_url(deviation: dict, quality: str, cookies: str) -> tuple[str, str]:
    """
    获取下载链接
    
    Returns:
        (download_url, filename)
    """
    # 如果有 media 信息
    if isinstance(deviation, dict) and 'media' in deviation:
        media = deviation['media']
        if not isinstance(media, dict):
            raise ValueError("Media 数据格式错误")
        
        base_uri = media.get('baseUri', '')
        pretty_name = media.get('prettyName', 'download')
        
        # 安全获取 token
        token = ''
        if 'token' in media:
            token_data = media['token']
            if isinstance(token_data, list) and token_data:
                token = token_data[0]
            elif isinstance(token_data, str):
                token = token_data
        
        types = media.get('types', [])
        if not isinstance(types, list):
            types = []
        
        # 根据质量选择
        if quality == 'o' and deviation.get('isDownloadable'):
            # 原图需要从页面提取
            return get_original_url(deviation.get('url', ''), cookies)
        
        elif quality == 'f':
            # 全图
            full_view = next((t for t in types if t.get('t') == 'fullview'), None)
            if full_view and 'c' in full_view:
                url = base_uri + full_view['c'].replace('<prettyName>', pretty_name)
            else:
                url = base_uri
            
            if token:
                url += f"?token={token}"
            
            ext = extract_extension(base_uri)
            return url, f"{pretty_name}{ext}"
        
        else:  # preview
            preview = next((t for t in types if t.get('t') == 'preview'), None)
            if preview and 'c' in preview:
                url = base_uri + preview['c'].replace('<prettyName>', pretty_name)
                if token:
                    url += f"?token={token}"
                ext = extract_extension(base_uri)
                return url, f"{pretty_name}{ext}"
    
    # 备用：从 HTML 提取
    if 'html' in deviation:
        return extract_from_html(deviation['html'], quality, cookies)
    
    raise ValueError("无法找到下载链接")

def get_original_url(page_url: str, cookies: str) -> tuple[str, str]:
    """获取原图下载链接"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Cookie": cookies
    }
    
    print(f"{Colors.BLUE}🔍 正在查找原图下载链接...{Colors.RESET}")
    
    response = requests.get(page_url, headers=headers, timeout=30)
    html_content = response.text
    
    download_marker = 'https://www.deviantart.com/download/'
    
    if download_marker not in html_content:
        raise ValueError("未找到下载链接 (可能需要登录)")
    
    # 提取下载 URL
    parts = html_content.split(download_marker)[1].split('"')[0]
    download_url = html.unescape(download_marker + parts)
    
    # 从 URL 提取文件名
    filename = download_url.split('/')[-1].split('?')[0]
    
    return download_url, filename

def extract_from_html(html_content: str, quality: str, cookies: str) -> tuple[str, str]:
    """从 HTML 提取下载链接（备用方案）"""
    # 查找图片 URL
    patterns = [
        r'<img[^>]+src="(https://images-wixmp[^"]+)"',
        r'<img[^>]+data-src="(https://images-wixmp[^"]+)"',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, html_content)
        if match:
            url = html.unescape(match.group(1))
            filename = "download" + extract_extension(url)
            return url, filename
    
    raise ValueError("无法从页面提取下载链接")

def extract_extension(url: str) -> str:
    """提取文件扩展名"""
    parts = url.split('.')
    if len(parts) > 1:
        ext = parts[-1].split('?')[0]
        return f".{ext}"
    return ".jpg"

def download_file(url: str, filepath: Path, cookies: str) -> None:
    """下载文件"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Cookie": cookies
    }
    
    print(f"{Colors.BLUE}⬇️  正在下载...{Colors.RESET}")
    
    try:
        response = requests.get(url, headers=headers, timeout=180, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        
        with open(filepath, 'wb') as f:
            if total_size == 0:
                f.write(response.content)
            else:
                downloaded = 0
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        # 简单进度显示
                        progress = downloaded / total_size * 100
                        print(f"\r{Colors.BLUE}进度: {progress:.1f}%{Colors.RESET}", end='', flush=True)
                print()  # 换行
        
        file_size = filepath.stat().st_size / (1024 * 1024)
        print(f"{Colors.GREEN}✓ 下载完成: {filepath.name} ({file_size:.2f} MB){Colors.RESET}")
        
    except Exception as e:
        if filepath.exists():
            filepath.unlink()
        raise Exception(f"下载失败: {e}")

def main():
    """主函数"""
    if len(sys.argv) < 2 or sys.argv[1] in ['-h', '--help', 'help']:
        print_help()
        sys.exit(0)
    
    url = sys.argv[1]
    
    # 解析选项
    quality = 'f'  # 默认全图
    dest = Path('./downloads')
    cookies_path = 'cookies.txt'
    custom_filename = None
    organize_mode = 'by_author'  # 默认按作者组织
    
    for arg in sys.argv[2:]:
        if arg.startswith('--quality='):
            quality = arg.split('=')[1]
        elif arg.startswith('--dest='):
            dest = Path(arg.split('=')[1])
        elif arg.startswith('--cookies='):
            cookies_path = arg.split('=')[1]
        elif arg.startswith('--filename='):
            custom_filename = arg.split('=')[1]
        elif arg.startswith('--organize='):
            organize_mode = arg.split('=')[1]
    
    # 验证质量参数
    if quality not in ['o', 'f', 'p']:
        print(f"{Colors.RED}✗ 无效的质量参数: {quality}{Colors.RESET}")
        print("使用 --quality=o (原图), f (全图), 或 p (预览)")
        sys.exit(1)
    
    print(f"{Colors.BOLD}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}  DeviantArt URL Downloader{Colors.RESET}")
    print(f"{Colors.BOLD}{'='*70}{Colors.RESET}\n")
    
    # 加载 cookies
    cookies = load_cookies(cookies_path)
    if cookies:
        source = get_cookie_source(cookies_path if cookies_path != "cookies.txt" else None)
        print(f"{Colors.GREEN}✓ 已加载 Cookie{Colors.RESET} ({source}, {len(cookies)} 字符)")
    else:
        print(f"{Colors.YELLOW}⚠ 未找到 Cookie (某些功能可能受限){Colors.RESET}")
        print(f"{Colors.YELLOW}提示: 运行 'devart-dl login interactive' 设置登录{Colors.RESET}")
    
    # 解析短链接
    if 'fav.me' in url:
        print(f"{Colors.BLUE}🔗 正在解析短链接...{Colors.RESET}")
        url = resolve_short_url(url)
        print(f"{Colors.GREEN}✓ 重定向到: {url}{Colors.RESET}")
    
    try:
        # 获取作品信息
        deviation = get_deviation_info(url, cookies)
        
        # 显示作品信息
        if isinstance(deviation, dict):
            if 'title' in deviation:
                print(f"{Colors.GREEN}📝 标题: {deviation['title']}{Colors.RESET}")
            if 'author' in deviation and isinstance(deviation['author'], dict):
                if 'username' in deviation['author']:
                    print(f"{Colors.GREEN}👤 作者: {deviation['author']['username']}{Colors.RESET}")
        
        # 获取下载链接
        download_url, filename = get_download_url(deviation, quality, cookies)
        
        # 使用自定义文件名
        if custom_filename:
            ext = Path(filename).suffix
            filename = f"{custom_filename}{ext}"
        
        # 准备元数据
        metadata = {
            'title': deviation.get('title', 'Unknown'),
            'author': deviation.get('author', {}).get('username') if isinstance(deviation.get('author'), dict) else None,
            'url': url,
            'download_url': download_url,
            'quality': quality,
            'date': deviation.get('publishedTime', datetime.now().isoformat())[:10],
            'deviation_id': deviation.get('deviationId'),
        }
        
        # 使用文件组织器
        if FileOrganizer and organize_mode != 'flat':
            organizer = FileOrganizer(base_dir=str(dest), mode=organize_mode)
            final_path = organizer.get_file_path(
                filename=filename,
                author=metadata['author'],
                date=metadata['date'],
                file_type='image'
            )
            print(f"{Colors.BLUE}📂 组织模式: {organize_mode}{Colors.RESET}")
        else:
            # 扁平结构或无组织器
            dest.mkdir(parents=True, exist_ok=True)
            final_path = dest / filename
        
        # 确保目录存在
        final_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 检查文件是否存在
        if final_path.exists():
            response = input(f"{Colors.YELLOW}⚠ 文件已存在，是否覆盖? (y/n): {Colors.RESET}")
            if response.lower() not in ['y', 'yes']:
                print(f"{Colors.YELLOW}✗ 已取消下载{Colors.RESET}")
                sys.exit(0)
        
        # 下载文件
        download_file(download_url, final_path, cookies)
        
        # 保存元数据
        if FileOrganizer and organize_mode != 'flat':
            organizer._save_metadata(final_path, metadata)
            print(f"{Colors.GREEN}✓ 已保存元数据{Colors.RESET}")
        
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 下载成功！{Colors.RESET}")
        print(f"{Colors.GREEN}   文件位置: {final_path.absolute()}{Colors.RESET}")
        if metadata['author']:
            print(f"{Colors.GREEN}   作者: {metadata['author']}{Colors.RESET}")
        print()
        
    except Exception as e:
        print(f"\n{Colors.RED}✗ 错误: {e}{Colors.RESET}")
        sys.exit(1)

if __name__ == '__main__':
    main()
