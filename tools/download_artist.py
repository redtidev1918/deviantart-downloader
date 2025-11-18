#!/usr/bin/env python3
"""
DeviantArt Artist Downloader - 通过作者 URL 批量下载所有作品

支持的 URL 格式:
- https://www.deviantart.com/username
- https://www.deviantart.com/username/gallery
- https://www.deviantart.com/username/gallery/12345
- https://deviantart.com/username
"""

import re
import sys
import subprocess
from pathlib import Path
from urllib.parse import urlparse

# 获取项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.resolve()

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
║        DeviantArt Artist Downloader - 作者作品批量下载工具            ║
╚══════════════════════════════════════════════════════════════════════╝{Colors.RESET}

{Colors.BOLD}用法:{Colors.RESET}
  python download_artist.py <ARTIST_URL> [OPTIONS]

{Colors.BOLD}支持的 URL 格式:{Colors.RESET}
  ✓ https://www.deviantart.com/username
  ✓ https://www.deviantart.com/username/gallery
  ✓ https://www.deviantart.com/username/gallery/12345678
  ✓ https://deviantart.com/username
  ✓ 或直接输入用户名

{Colors.BOLD}选项:{Colors.RESET}
  --quality=<o|f|p>   质量: o=原图, f=全图, p=预览 (默认: f)
  --dest=<PATH>       下载目录 (默认: ./downloads)
  --cookies=<PATH>    Cookie 文件路径 (默认: ./cookies.txt)
  --ask=<0|1>         是否询问每个下载 (默认: 0)
  --limit=<NUM>       每次加载数量 (默认: 24)
  --offset=<NUM>      起始偏移量 (默认: 0)
  --delay=<SEC>       下载延迟秒数 (默认: 1)
  --version=<v1|v2>   使用的版本 (默认: v2)

{Colors.BOLD}示例:{Colors.RESET}
  {Colors.BLUE}# 通过用户主页 URL 下载所有作品{Colors.RESET}
  python download_artist.py https://www.deviantart.com/username

  {Colors.BLUE}# 下载特定画廊{Colors.RESET}
  python download_artist.py https://www.deviantart.com/username/gallery/12345678

  {Colors.BLUE}# 下载原图质量 (需要登录){Colors.RESET}
  python download_artist.py https://www.deviantart.com/username --quality=o

  {Colors.BLUE}# 自定义下载目录{Colors.RESET}
  python download_artist.py https://www.deviantart.com/username --dest=./my_collection

  {Colors.BLUE}# 直接使用用户名{Colors.RESET}
  python download_artist.py username --quality=f

  {Colors.BLUE}# 批量下载不询问{Colors.RESET}
  python download_artist.py username --ask=0 --delay=2

{Colors.BOLD}下载模式:{Colors.RESET}
  • 默认模式: 下载所有画廊作品
  • 画廊 ID: 下载特定画廊 (从 URL 自动提取)
  • 全部作品: 包括所有公开内容

{Colors.BOLD}注意:{Colors.RESET}
  • 需要先安装主程序的依赖: pip install requests
  • 下载原图需要配置 cookies.txt
  • 大量下载建议设置延迟避免被限流

{Colors.BOLD}工作原理:{Colors.RESET}
  1. 从 URL 提取用户名和画廊 ID (如果有)
  2. 调用 main.py (v2) 或 deviantart_downloader.py (v1)
  3. 批量下载所有作品
''')

def extract_info_from_url(url: str) -> tuple[str, str | None]:
    """
    从 URL 提取用户名和画廊 ID
    
    Returns:
        (username, gallery_id)
    """
    # 如果输入的是纯用户名
    if '/' not in url and '.' not in url:
        return url, None
    
    # 解析 URL
    parsed = urlparse(url)
    path = parsed.path
    
    # 提取用户名
    # 路径格式: /username 或 /username/gallery 或 /username/gallery/12345
    parts = [p for p in path.split('/') if p]
    
    if not parts:
        raise ValueError("无法从 URL 提取用户名")
    
    username = parts[0]
    
    # 提取画廊 ID
    gallery_id = None
    if len(parts) >= 3 and parts[1] == 'gallery':
        # /username/gallery/12345
        gallery_id = parts[2]
    
    return username, gallery_id

def build_command(username: str, gallery_id: str | None, options: dict, version: str = 'v2') -> list[str]:
    """
    构建下载命令
    
    Args:
        username: 用户名
        gallery_id: 画廊 ID (可选)
        options: 选项字典
        version: 使用的版本 (v1 或 v2)
    
    Returns:
        命令列表
    """
    if version == 'v2':
        script_path = PROJECT_ROOT / 'legacy' / 'main.py'
        cmd = ['python3', str(script_path)]
    else:
        script_path = PROJECT_ROOT / 'legacy' / 'deviantart_downloader.py'
        cmd = ['python3', str(script_path)]
    
    # 添加操作类型
    cmd.append('gallery')
    cmd.append(username)
    
    # 如果有画廊 ID
    if gallery_id:
        cmd.append(gallery_id)
    
    # 添加选项
    for key, value in options.items():
        if value is not None:
            cmd.append(f'{key}={value}')
    
    return cmd

def main():
    """主函数"""
    if len(sys.argv) < 2 or sys.argv[1] in ['-h', '--help', 'help']:
        print_help()
        sys.exit(0)
    
    url_or_username = sys.argv[1]
    
    # 解析选项
    options = {}
    version = 'v2'
    
    for arg in sys.argv[2:]:
        if '=' not in arg:
            continue
        
        key, value = arg.split('=', 1)
        
        if key == '--version':
            version = value
        else:
            options[key] = value
    
    print(f"{Colors.BOLD}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}  DeviantArt Artist Downloader{Colors.RESET}")
    print(f"{Colors.BOLD}{'='*70}{Colors.RESET}\n")
    
    try:
        # 提取用户名和画廊 ID
        username, gallery_id = extract_info_from_url(url_or_username)
        
        print(f"{Colors.GREEN}✓ 用户名: {username}{Colors.RESET}")
        if gallery_id:
            print(f"{Colors.GREEN}✓ 画廊 ID: {gallery_id}{Colors.RESET}")
        else:
            print(f"{Colors.BLUE}ℹ 下载模式: 所有画廊作品{Colors.RESET}")
        
        # 显示配置
        print(f"\n{Colors.BOLD}下载配置:{Colors.RESET}")
        quality_map = {'o': '原图', 'f': '全图', 'p': '预览'}
        quality = options.get('--quality', 'f')
        print(f"  质量: {quality_map.get(quality, quality)}")
        print(f"  目录: {options.get('--dest', './downloads')}")
        print(f"  版本: {version}")
        print(f"  询问: {'是' if options.get('--ask', '0') == '1' else '否'}")
        
        # 构建命令
        cmd = build_command(username, gallery_id, options, version)
        
        print(f"\n{Colors.BLUE}执行命令:{Colors.RESET}")
        print(f"  {' '.join(cmd)}\n")
        
        # 确认
        response = input(f"{Colors.YELLOW}是否开始下载? (y/n): {Colors.RESET}")
        if response.lower() not in ['y', 'yes', '是']:
            print(f"{Colors.YELLOW}✗ 已取消{Colors.RESET}")
            sys.exit(0)
        
        print(f"\n{Colors.GREEN}{'='*70}{Colors.RESET}")
        print(f"{Colors.GREEN}开始下载...{Colors.RESET}")
        print(f"{Colors.GREEN}{'='*70}{Colors.RESET}\n")
        
        # 执行命令（设置工作目录为项目根目录，以便 Python 能找到模块）
        result = subprocess.run(cmd, cwd=str(PROJECT_ROOT))
        
        if result.returncode == 0:
            print(f"\n{Colors.GREEN}{Colors.BOLD}{'='*70}{Colors.RESET}")
            print(f"{Colors.GREEN}{Colors.BOLD}  🎉 下载完成！{Colors.RESET}")
            print(f"{Colors.GREEN}{Colors.BOLD}{'='*70}{Colors.RESET}\n")
        else:
            print(f"\n{Colors.RED}✗ 下载过程中出现错误 (退出码: {result.returncode}){Colors.RESET}")
            sys.exit(result.returncode)
        
    except ValueError as e:
        print(f"{Colors.RED}✗ 错误: {e}{Colors.RESET}")
        print(f"\n{Colors.YELLOW}提示: 请提供有效的 DeviantArt URL 或用户名{Colors.RESET}")
        print(f"{Colors.YELLOW}示例: python download_artist.py username{Colors.RESET}")
        print(f"{Colors.YELLOW}      python download_artist.py https://www.deviantart.com/username{Colors.RESET}")
        sys.exit(1)
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}✗ 用户中断{Colors.RESET}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}✗ 意外错误: {e}{Colors.RESET}")
        sys.exit(1)

if __name__ == '__main__':
    main()
