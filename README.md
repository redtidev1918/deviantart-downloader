# DeviantArt Downloader

> 🎨 专业的 DeviantArt 作品批量下载工具
> 
> Professional DeviantArt Batch Downloader with Browser Auto-Login & Anti-Ban

**中文文档** | [English Documentation](README_EN.md)

[![Python](https://img.shields.io/badge/Python-3.6%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![i18n](https://img.shields.io/badge/i18n-中文%20%7C%20English-orange.svg)](#国际化)
[![Version](https://img.shields.io/badge/Version-3.0.0-brightgreen.svg)](#)

---

## ✨ 核心特性 | Core Features

-  **统一CLI** - 单一命令 `devart-dl` 访问所有功能
-  **5种登录方式** - Cookie文件、交互输入、会话保存、环境变量、浏览器
-  **智能防封** - 4种预设模式、自动延迟、速率限制
-  **灵活下载** - URL单图、作者全集、画廊批量、搜索过滤
-  **增强日志** - 彩色输出、文件记录、调试模式 
-  **国际化** - 中文/英文双语支持，自动检测
-  **高性能** - 异步下载架构（Python 3.10+）
-  **零配置** - 开箱即用，渐进增强
-  **模块化** - 清晰的项目结构，易于维护

---

## 🚀 快速开始 | Quick Start

### 安装 | Installation

```bash
# 克隆仓库
git clone https://github.com/zoidberg-xgd/deviantart-downloader.git
cd deviantart-downloader

# 安装依赖
pip install requests

# 安装统一命令（可选）
./install.sh
```

### 基本使用 | Basic Usage

```bash
# 方式1: 使用统一命令
devart-dl url <作品URL>              # 下载单个作品
devart-dl artist <用户名>            # 下载作者所有作品
devart-dl gallery <用户名>           # 下载画廊

# 方式2: 直接运行脚本
python download_url.py <作品URL>
python download_artist.py <用户名>
python main.py gallery <用户名>
```

---

## 📋 主要功能 | Main Features

### 1. URL 下载 | URL Download

下载单个作品，支持标准URL和短链接

```bash
# 标准URL
devart-dl url https://www.deviantart.com/user/art/title-123456

# 短链接
devart-dl url https://fav.me/de12345

# 自定义质量和目录
devart-dl url <URL> --quality=o --dest=./downloads
```

### 2. 作者下载 | Artist Download

通过作者主页URL批量下载所有作品

```bash
# 下载作者所有作品
devart-dl artist username

# 或使用完整URL
devart-dl artist https://www.deviantart.com/username

# 指定选项
devart-dl artist username --quality=f --delay=2
```

### 3. 画廊下载 | Gallery Download

批量下载画廊内容

```bash
# 下载所有画廊
devart-dl gallery username

# 下载特定画廊
devart-dl gallery username 12345678

# 安全模式（推荐）
devart-dl gallery username --delay=3 --limit=10
```

### 4. 搜索下载 | Search Download

搜索并下载匹配的作品

```bash
# 在用户作品中搜索
devart-dl search username "landscape"

# 全站搜索
devart-dl search all "digital art"
```

---

## 🔐 登录方式 | Authentication

支持5种灵活的登录方式：

| 方式 | 难度 | 推荐 | 适用场景 |
|------|------|------|---------|
| **Cookie 文件** | 简单 | ✅ 推荐 | 日常使用 |
| **交互输入** | 简单 | ✅ 推荐 | 首次设置 |
| **会话保存** | 最简单 | ✅ | 长期使用 |
| **环境变量** | 中等 | - | CI/CD、脚本 |
| **浏览器自动** | 最简单 | ⚠️ 不稳定 | 仅供尝试 |

### 方式1: 浏览器自动登录 

**注意：** DeviantArt 有反自动化检测，此方式可能被阻止。推荐使用方式2或方式4。

```bash
# 安装依赖（仅首次）
pip install selenium webdriver-manager

# 尝试使用浏览器登录
devart-dl login browser

# 指定浏览器
devart-dl login browser --browser=firefox
```

**已知问题：**
- 可能遇到"Access Denied"错误（反自动化）
- 首次运行需下载驱动（1-2分钟）
- 需要已安装对应浏览器

**如果遇到问题，请使用方式2（Cookie文件）或方式4（交互输入）。**

### 方式2: Cookie 文件

```bash
# 1. 创建 cookies.txt
# 2. 粘贴从浏览器获取的 Cookie
# 3. 开始下载
devart-dl gallery username
```

### 方式3: 环境变量

```bash
# 设置环境变量
export DEVIANTART_COOKIES="auth=xxx; auth_secure=xxx; ..."

# 或在 .env 文件
echo 'DEVIANTART_COOKIES=...' > .env
```

### 方式4: 交互式输入

```bash
# 运行交互式登录
devart-dl login interactive

# 按提示粘贴 Cookie
```

### 方式5: 会话保存

```bash
# 首次登录后自动保存到 ~/.deviantart_dl/session.json
# 30天有效期，自动加载

# 清除会话
devart-dl login clear
```

### 验证 Cookie 是否有效 ⭐新增

```bash
# 验证当前 Cookie
devart-dl login validate

# 验证指定 Cookie
devart-dl login validate --cookies="auth=xxx; ..."

# JSON 格式输出（用于脚本）
devart-dl login check --json
```

**验证内容：**
- ✓ Cookie 存在性检查
- ✓ 登录状态验证
- ✓ 用户信息获取
- ✓ 下载权限测试
- ✓ Cookie 过期检测

### 快速获取 Cookie 

**方法1: 一键导出脚本（最快）**

```javascript
// 1. 在 DeviantArt 登录后的页面按 F12
// 2. 切换到 Console 标签
// 3. 粘贴以下代码并回车：
(function(){let c=document.cookie;navigator.clipboard.writeText(c).then(()=>alert('✓ Cookie已复制！')).catch(()=>{let t=document.createElement('textarea');t.value=c;document.body.appendChild(t);t.select();document.execCommand('copy');document.body.removeChild(t);alert('✓ Cookie已复制！')})})();
// 4. Cookie 自动复制到剪贴板！
```

**方法2: 可视化导出（带UI）**
- 使用 `tools/export_cookies.js` 完整脚本
- 弹出漂亮的导出面板
- 区分关键Cookie和完整Cookie

**方法3: 书签工具（最方便）**
- 创建书签，网址填入上面的脚本
- 在 DeviantArt 页面点击书签
- 一键导出

**方法4: 手动复制（传统）**
- Chrome/Edge: `F12` → `Application` → `Cookies`
- Firefox: `F12` → `存储` → `Cookie`

**📖 完整导出指南:**
```bash
# 查看所有导出方法（推荐阅读）
cat tools/COOKIE_EXPORT_GUIDE.md
```

---

## 🛡️ 防封IP | Anti-Ban

**重要：批量下载必读**

### 推荐配置

```bash
# 安全模式（推荐新手）
devart-dl gallery username --delay=3 --limit=10

# 平衡模式（日常使用）
devart-dl gallery username --delay=2 --limit=24

# 快速模式（谨慎使用）
devart-dl gallery username --delay=1 --limit=50
```

### 核心原则

✅ **必须做:**
- 延迟 ≥ 2秒 (`--delay=2`)
- 限制批次大小 (`--limit=24`)
- 遇到429错误立即停止
- 大量下载分多天进行

❌ **禁止做:**
- 延迟 < 1秒
- 短时间下载数百文件
- 忽略速率限制错误

### 完整指南

```bash
devart-dl anti-ban
```

---

## 🌍 国际化 | i18n

支持中文和英文双语

### 设置语言

```bash
# 方式1: 环境变量
export DEVART_LANG=zh_CN  # 中文
export DEVART_LANG=en_US  # English

# 方式2: 自动检测（根据系统LANG）
# 中文系统自动中文，英文系统自动英文

# 测试
python i18n.py --lang=zh_CN --test
python i18n.py --lang=en_US --test
```

---

## 📝 日志系统 | Logging

增强的彩色日志系统，支持调试和文件记录

### 日志选项

```bash
# 调试模式（启用文件日志）
devart-dl --debug gallery username
devart-dl -d url <URL>

# 详细模式（显示所有信息）
devart-dl --verbose artist username
devart-dl -v gallery username

# 安静模式（仅显示错误）
devart-dl --quiet gallery username
devart-dl -q url <URL>
```

### 日志文件位置

```bash
# 调试模式下，日志自动保存到：
~/.deviantart_dl/logs/devart-dl_YYYYMMDD.log

# 查看日志
tail -f ~/.deviantart_dl/logs/devart-dl_*.log

# 清理旧日志
rm ~/.deviantart_dl/logs/*.log
```

### 日志级别

| 级别 | 颜色 | 用途 |
|------|------|------|
| DEBUG | 青色 | 调试信息（仅在 --debug 模式） |
| INFO | 绿色 | 一般信息 |
| WARNING | 黄色 | 警告信息 |
| ERROR | 红色 | 错误信息 |
| CRITICAL | 紫色 | 严重错误 |

### 示例

```bash
# 调试下载问题
devart-dl --debug url <URL>

# 查看详细下载进度
devart-dl --verbose gallery username --delay=2

# 后台静默运行
devart-dl --quiet artist username > /dev/null 2>&1 &
```

---

## ⚙️ 配置选项 | Options

### 通用选项

| 选项 | 说明 | 默认值 |
|------|------|--------|
| `--quality=<o\|f\|p>` | 质量：o=原图, f=全图, p=预览 | `f` |
| `--dest=<path>` | 下载目录 | `./downloads` |
| `--delay=<seconds>` | 延迟时间（防封） | `1` |
| `--limit=<number>` | 每批数量 | `24` |
| `--organize=<mode>` | 文件组织模式 ⭐新增 | `by_author` |

### 文件组织模式 ⭐新增

智能管理下载的文件，自动分类整理：

**可用模式：**

| 模式 | 说明 | 目录结构示例 |
|------|------|-------------|
| `by_author` | 按作者分类（推荐） | `downloads/artist_name/artwork.jpg` |
| `by_date` | 按日期分类 | `downloads/2025/01/15/artwork.jpg` |
| `by_type` | 按文件类型分类 | `downloads/images/artwork.jpg` |
| `by_gallery` | 按画廊分类 | `downloads/artist/gallery_name/artwork.jpg` |
| `mixed` | 混合模式（作者+日期） | `downloads/artist/2025-01/artwork.jpg` |
| `flat` | 扁平结构（无分类） | `downloads/artwork.jpg` |

**使用示例：**

```bash
# 按作者分类（默认）
devart-dl url <URL>
devart-dl url <URL> --organize=by_author

# 按日期分类
devart-dl gallery username --organize=by_date

# 按类型分类
devart-dl artist username --organize=by_type

# 混合模式（作者+日期）
devart-dl gallery username --organize=mixed

# 扁平结构
devart-dl url <URL> --organize=flat
```

**元数据保存：**

每个下载的文件都会保存元数据到 `.metadata/` 目录：
- 作品标题、作者、URL
- 下载时间、文件大小
- 质量设置、deviation ID
- JSON 格式，易于查询和管理

**查看目录结构：**

```bash
python tools/file_organizer.py --mode=by_author --show-structure
python tools/file_organizer.py --mode=by_date --show-structure
```
| `--cookies=<path>` | Cookie文件路径 | `cookies.txt` |
| `--proxy=<url>` | 代理服务器 | - |
| `--ask=<0\|1>` | 是否询问 | `1` |

### 示例

```bash
# 下载原图，延迟3秒
devart-dl gallery user --quality=o --delay=3

# 使用代理，批量下载
devart-dl gallery user --proxy=http://127.0.0.1:7890 --ask=0

# 自定义目录
devart-dl artist user --dest=~/MyArt --quality=f
```

---

## 📖 命令参考 | Command Reference

### 核心命令

```bash
devart-dl url <URL>               # URL下载
devart-dl artist <username>       # 作者下载
devart-dl gallery <username>      # 画廊下载
devart-dl search <user> <query>   # 搜索下载
devart-dl fav <user> <folder_id>  # 收藏夹下载
```

### 工具命令

```bash
devart-dl login [interactive|clear]  # 登录管理
devart-dl anti-ban                   # 防封指南
devart-dl config                     # 配置管理
devart-dl test <username>            # 测试下载
```

### 信息命令

```bash
devart-dl help              # 帮助
devart-dl help <command>    # 命令帮助
devart-dl version           # 版本
devart-dl docs              # 文档
```

---

## 🏗️ 项目结构 | Project Structure

```
deviantart-downloader/
├── devart-dl              # 统一CLI入口
├── install.sh             # 安装脚本
│
├── 核心工具 | Core Tools
│   ├── download_url.py       # URL下载器
│   ├── download_artist.py    # 作者下载器
│   ├── main.py               # 批量下载器
│   └── deviantart_downloader.py  # 原始脚本（兼容）
│
├── 功能模块 | Modules
│   ├── da_downloader/        # 稳定版模块
│   ├── deviantart_dl/        # 异步版模块
│   ├── auth_manager.py       # 多种登录
│   ├── anti_ban_config.py    # 防封配置
│   └── i18n.py               # 国际化
│
├── 配置 | Config
│   ├── requirements.txt      # 依赖
│   ├── pyproject.toml        # 项目配置
│   ├── setup.py              # 安装配置
│   └── .gitignore
│
└── 文档 | Docs
    └── README.md             # 本文档
```

---

## 🔧 高级用法 | Advanced Usage

### 使用代理

```bash
# HTTP代理
devart-dl gallery user --proxy=http://127.0.0.1:7890

# SOCKS代理（需要额外依赖）
pip install requests[socks]
devart-dl gallery user --proxy=socks5://127.0.0.1:1080
```

### 批处理

```bash
# 批量下载多个用户
for user in user1 user2 user3; do
    devart-dl artist $user --delay=3
    sleep 300  # 用户间休息5分钟
done
```

### 分批下载

```bash
# 避免一次下载太多
devart-dl gallery user --limit=50 --offset=0
devart-dl gallery user --limit=50 --offset=50
devart-dl gallery user --limit=50 --offset=100
```

### 作为Python库

```python
from da_downloader import DeviantArtDownloader, Config

config = Config(
    quality='f',
    delay_seconds=2.0,
    ask_before_download=False
)

downloader = DeviantArtDownloader(config)
downloader.download_gallery('username')
```

---

## ❓ 常见问题 | FAQ

### Q: 需要登录吗？

**部分功能需要：**
- 下载原图 (`--quality=o`)
- 成熟内容
- 私密作品
- 收藏夹

**不需要登录：**
- 下载全图/预览图
- 公开作品
- 大部分画廊

### Q: 如何避免被封IP？

1. 设置延迟 ≥ 2秒
2. 限制批次大小
3. 使用代理轮换
4. 遇到429立即停止
5. 查看完整指南：`devart-dl anti-ban`

### Q: 支持哪些URL格式？

- 标准: `https://www.deviantart.com/user/art/title-123456`
- 短链: `https://fav.me/dxxxxxx`
- 主页: `https://www.deviantart.com/username`
- 画廊: `https://www.deviantart.com/user/gallery/12345`

### Q: 下载速度慢？

- 减少延迟（风险：可能被封）
- 使用代理
- 检查网络连接
- 注意：为防封，不建议过快

### Q: 如何更新？

```bash
git pull origin main
pip install -r requirements.txt --upgrade
```

---

## 🤝 贡献 | Contributing

欢迎贡献代码、报告问题或提出建议！

```bash
# Fork项目 → 创建分支 → 提交代码 → Pull Request
```

---

## 📄 许可证 | License

MIT License - 仅供学习和个人使用

---

## 🔗 相关链接 | Links

- **GitHub**: https://github.com/zoidberg-xgd/deviantart-downloader
- **Issues**: https://github.com/zoidberg-xgd/deviantart-downloader/issues
- **Discussions**: https://github.com/zoidberg-xgd/deviantart-downloader/discussions
- **DeviantArt**: https://www.deviantart.com

---

[⬆ 返回顶部](#deviantart-downloader)

