#!/usr/bin/env python3
"""
DeviantArt Downloader CLI Entry Point
用于 pip 安装后的命令行入口
"""

import sys
import os
from pathlib import Path


def main():
    """CLI 主入口"""
    # 获取包的安装目录
    package_dir = Path(__file__).parent
    
    # 导入 devart-dl 脚本
    devart_dl_path = package_dir / "devart-dl"
    
    if devart_dl_path.exists():
        # 直接执行 devart-dl 脚本
        import subprocess
        result = subprocess.run([sys.executable, str(devart_dl_path)] + sys.argv[1:])
        sys.exit(result.returncode)
    else:
        # 如果找不到，尝试从当前目录
        print("错误: 找不到 devart-dl 脚本")
        print(f"搜索路径: {devart_dl_path}")
        sys.exit(1)


if __name__ == "__main__":
    main()
