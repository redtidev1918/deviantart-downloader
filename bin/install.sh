#!/bin/bash
# DeviantArt Downloader 安装脚本
# 将 'da' 命令安装到系统路径

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

echo -e "${BOLD}╔══════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}║       DeviantArt Downloader - 安装脚本                              ║${NC}"
echo -e "${BOLD}╚══════════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# 获取当前目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo -e "${BLUE}📁 项目目录: $SCRIPT_DIR${NC}"

# 检查 da 命令是否存在
if [ ! -f "$SCRIPT_DIR/da" ]; then
    echo -e "${RED}✗ 错误: 找不到 'da' 命令文件${NC}"
    exit 1
fi

# 确保 da 可执行
chmod +x "$SCRIPT_DIR/da"
echo -e "${GREEN}✓ 设置 da 命令为可执行${NC}"

# 安装选项
echo ""
echo -e "${BOLD}选择安装方式:${NC}"
echo -e "  ${GREEN}1.${NC} 用户级安装 (推荐) - 仅当前用户可用"
echo -e "  ${GREEN}2.${NC} 系统级安装 - 所有用户可用 (需要 sudo)"
echo -e "  ${GREEN}3.${NC} 创建别名 - 添加到 shell 配置文件"
echo -e "  ${GREEN}4.${NC} 仅测试 - 不安装"
echo ""
read -p "请选择 [1-4]: " choice

case $choice in
    1)
        # 用户级安装
        INSTALL_DIR="$HOME/.local/bin"
        
        # 创建目录
        mkdir -p "$INSTALL_DIR"
        
        # 创建符号链接
        ln -sf "$SCRIPT_DIR/da" "$INSTALL_DIR/da"
        
        echo -e "${GREEN}✓ 已安装到: $INSTALL_DIR/da${NC}"
        
        # 检查是否在 PATH 中
        if [[ ":$PATH:" != *":$INSTALL_DIR:"* ]]; then
            echo ""
            echo -e "${YELLOW}⚠️  注意: $INSTALL_DIR 不在 PATH 中${NC}"
            echo -e "${YELLOW}请将以下内容添加到 ~/.bashrc 或 ~/.zshrc:${NC}"
            echo ""
            echo -e "${BLUE}export PATH=\"\$HOME/.local/bin:\$PATH\"${NC}"
            echo ""
        else
            echo -e "${GREEN}✓ $INSTALL_DIR 已在 PATH 中${NC}"
        fi
        ;;
        
    2)
        # 系统级安装
        INSTALL_DIR="/usr/local/bin"
        
        echo -e "${YELLOW}需要 sudo 权限...${NC}"
        sudo ln -sf "$SCRIPT_DIR/da" "$INSTALL_DIR/da"
        
        echo -e "${GREEN}✓ 已安装到: $INSTALL_DIR/da${NC}"
        ;;
        
    3)
        # 创建别名
        echo ""
        echo -e "${BLUE}选择 shell 类型:${NC}"
        echo -e "  1. Bash (~/.bashrc)"
        echo -e "  2. Zsh (~/.zshrc)"
        echo -e "  3. Fish (~/.config/fish/config.fish)"
        read -p "请选择 [1-3]: " shell_choice
        
        case $shell_choice in
            1)
                SHELL_RC="$HOME/.bashrc"
                ;;
            2)
                SHELL_RC="$HOME/.zshrc"
                ;;
            3)
                SHELL_RC="$HOME/.config/fish/config.fish"
                mkdir -p "$(dirname "$SHELL_RC")"
                ;;
            *)
                echo -e "${RED}无效选择${NC}"
                exit 1
                ;;
        esac
        
        ALIAS_CMD="alias da='$SCRIPT_DIR/da'"
        
        # 检查是否已存在
        if grep -q "alias da=" "$SHELL_RC" 2>/dev/null; then
            echo -e "${YELLOW}⚠️  别名已存在于 $SHELL_RC${NC}"
        else
            echo "" >> "$SHELL_RC"
            echo "# DeviantArt Downloader" >> "$SHELL_RC"
            echo "$ALIAS_CMD" >> "$SHELL_RC"
            echo -e "${GREEN}✓ 已添加别名到: $SHELL_RC${NC}"
        fi
        
        echo ""
        echo -e "${YELLOW}运行以下命令使别名生效:${NC}"
        echo -e "${BLUE}source $SHELL_RC${NC}"
        ;;
        
    4)
        # 仅测试
        echo -e "${BLUE}测试模式 - 不安装${NC}"
        ;;
        
    *)
        echo -e "${RED}无效选择${NC}"
        exit 1
        ;;
esac

# 测试安装
echo ""
echo -e "${BOLD}测试安装:${NC}"
if command -v da &> /dev/null; then
    echo -e "${GREEN}✓ 'da' 命令可用${NC}"
    echo ""
    echo -e "${BLUE}运行 'da help' 查看帮助${NC}"
elif [ "$choice" = "3" ]; then
    echo -e "${YELLOW}⚠️  需要重新加载 shell 配置${NC}"
    echo -e "${BLUE}运行: source $SHELL_RC${NC}"
elif [ "$choice" = "4" ]; then
    echo -e "${BLUE}运行: $SCRIPT_DIR/da help${NC}"
else
    echo -e "${YELLOW}⚠️  'da' 命令未找到${NC}"
    echo -e "${YELLOW}可能需要重新打开终端或运行:${NC}"
    echo -e "${BLUE}export PATH=\"$INSTALL_DIR:\$PATH\"${NC}"
fi

echo ""
echo -e "${GREEN}${BOLD}安装完成！${NC}"
echo ""
echo -e "${BOLD}快速开始:${NC}"
echo -e "  da help              - 查看帮助"
echo -e "  da version           - 查看版本"
echo -e "  da url <URL>         - 下载单个作品"
echo -e "  da artist <用户名>   - 下载作者所有作品"
echo -e "  da anti-ban          - 查看防封指南"
echo ""
