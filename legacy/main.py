#!/usr/bin/env python3
"""
DeviantArt Downloader v2.0 - 重构版主入口

使用示例:
    python main.py gallery username
    python main.py search username "keyword"
    python main.py fav username 123456 --quality=f
"""

import sys

from da_downloader import DeviantArtDownloader, Config
from da_downloader.utils import setup_logging, print_banner


def show_help():
    """显示帮助信息"""
    help_text = '''
╔══════════════════════════════════════════════════════════════════════╗
║             DEVIANTART DOWNLOADER v2.0 - HELP & USAGE                ║
╚══════════════════════════════════════════════════════════════════════╝

ACTION TYPES:
  gallery <PROFILE_NAME>              [OPTIONS]  - Download all arts from profile
  gallery <PROFILE_NAME> <GALLERY_ID> [OPTIONS]  - Download specific gallery
  search  <PROFILE_NAME> <QUERY>      [OPTIONS]  - Search within a profile
  search  all            <QUERY>      [OPTIONS]  - Global search on DeviantArt
  fav     <PROFILE_NAME> <FOLDER_ID>  [OPTIONS]  - Download favourite folder

OPTIONS:
  --ask=<0|1>         Ask before each download (default: 1)
  --cookies=<PATH>    Path to cookies file (default: ./cookies.txt)
  --debug=<0|1>       Debug mode (default: 0)
  --delay=<DECIMAL>   Delay between downloads in seconds (default: 1)
  --dest=<PATH>       Destination folder for downloads
  --limit=<1..60>     Lazy loading limit (default: 24)
  --offset=<INT>      Beginning offset (default: 0)
  --proxy=<URL>       Proxy server (e.g. http://127.0.0.1:8580)
  --quality=<o|f|p>   Quality: o=original, f=full, p=preview (default: o)
  --replace=<0|1>     Replace existing files (default: 1)
  --separate=<0|1>    Separate folders per profile (default: 1 for gallery)

INTERACTIVE ANSWERS:
  q, quit              Quit the application
  s, skip              Skip current batch of items
  a, all               Download all remaining items
  y, yes               Download current item
  p, pre, preview      Download in preview quality
  f, ful, full         Download in full-view quality
  o, org, original     Download in original quality
  <Enter/other>        Skip current item

LOGIN & AUTHENTICATION:
  ✓ Improved login system with automatic validation
  ✓ Interactive guide for cookie setup
  ✓ Better error handling and retry mechanism
  
  To use login features:
  1. Create "cookies.txt" in the project folder
  2. Add your DeviantArt cookies (see guide in app)
  3. Run the script - it validates automatically
  
  Login is REQUIRED for:
  • Downloading original quality images (--quality=o)
  • Accessing private/exclusive content
  • Viewing mature content (if age-restricted)

EXAMPLES:
  python main.py gallery username
  python main.py gallery username --quality=f --ask=0
  python main.py search username "landscape" --limit=50
  python main.py fav username 123456 --dest=./favorites

NEW IN v2.0:
  ✓ Modular architecture - better code organization
  ✓ Object-oriented design - easier to extend
  ✓ Improved logging system - better debugging
  ✓ Better error handling - more robust
  ✓ Progress tracking - see download status
  ✓ Type hints - better IDE support
  ✓ Python 3.10+ support

For detailed documentation, see README.md
'''
    print(help_text)


def parse_arguments() -> tuple:
    """
    解析命令行参数
    
    Returns:
        (action, username, params, options)
    """
    if len(sys.argv) <= 1 or sys.argv[1] in ['-h', '--help', 'help']:
        show_help()
        sys.exit(0)
    
    action = sys.argv[1]
    
    if action not in ['gallery', 'search', 'fav']:
        print(f"Error: Unknown action '{action}'")
        print("Use 'help' to see available actions")
        sys.exit(1)
    
    if len(sys.argv) < 3:
        print(f"Error: Missing arguments for action '{action}'")
        print("Use 'help' to see usage")
        sys.exit(1)
    
    username = sys.argv[2].lower()
    
    # 解析额外参数和选项
    params = []
    options = {}
    
    for arg in sys.argv[3:]:
        if '=' in arg:
            key, value = arg.split('=', 1)
            options[key] = value
        else:
            params.append(arg)
    
    return action, username, params, options


def main():
    """主函数"""
    # 解析参数
    action, username, params, options = parse_arguments()
    
    # 创建配置
    config = Config.from_args(options)
    
    # 设置日志
    log_level = "DEBUG" if config.debug_mode else "INFO"
    setup_logging(level=log_level, log_file=config.log_file)
    
    # 显示横幅
    print_banner()
    
    # 验证配置
    config.validate()
    
    # 显示配置信息
    if config.debug_mode:
        print(config)
    
    # 创建下载器
    downloader = DeviantArtDownloader(config)
    
    # 根据操作类型执行
    try:
        if action == 'gallery':
            folder_id = params[0] if params else None
            downloader.download_gallery(username, folder_id)
            
        elif action == 'search':
            if not params:
                print("Error: Missing search query")
                sys.exit(1)
            query = params[0]
            downloader.download_search(username, query)
            
        elif action == 'fav':
            if not params:
                print("Error: Missing folder ID")
                sys.exit(1)
            folder_id = params[0]
            downloader.download_favorites(username, folder_id)
    
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Exiting...")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nError: {e}")
        if config.debug_mode:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
