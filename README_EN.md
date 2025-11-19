# DeviantArt Downloader

A powerful, feature-rich DeviantArt artwork downloader with intelligent file organization, multiple authentication methods, and anti-ban protection.

[中文文档](README.md) | **English Documentation**

[![PyPI](https://img.shields.io/pypi/v/devart-dl.svg)](https://pypi.org/project/devart-dl/)
[![Python](https://img.shields.io/pypi/pyversions/devart-dl.svg)](https://pypi.org/project/devart-dl/)
[![Downloads](https://img.shields.io/pypi/dm/devart-dl.svg)](https://pypi.org/project/devart-dl/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![i18n](https://img.shields.io/badge/i18n-中文%20%7C%20English-orange.svg)](#internationalization)

---

## ✨ Core Features | 核心特性

-  **Unified CLI** - Single `devart-dl` command for all features
-  **5 Login Methods** - Cookie file, interactive, session save, env var, browser
-  **Smart Anti-Ban** - 4 preset modes, auto delay, rate limiting
-  **Flexible Download** - Single URL, author gallery, batch, search filter
-  **Resume Support** - Auto-resume after interruption, skip downloaded
-  **Auto Retry** - Network errors auto-retry 3 times
-  **1080p Videos** - Auto-select highest quality videos
-  **Auto Proxy** - Auto-load proxy from environment variables
-  **Enhanced Logging** - Colored output, file logging, login status display
-  **Internationalization** - Chinese/English bilingual support
-  **High Performance** - Async download, fast skip existing files
-  **Zero Config** - Works out of box, progressive enhancement
-  **Modular** - Clean project structure, easy to maintain


---

## 🚀 Quick Start | 快速开始

### Installation | 安装

**Method 1: Install from PyPI (Recommended) ⭐**

```bash
# Basic installation
pip install devart-dl

# Or with browser login support
pip install devart-dl[browser]
```

**Method 2: Install from source**

```bash
# Clone repository
git clone https://github.com/zoidberg-xgd/deviantart-downloader.git
cd deviantart-downloader

# Install dependencies
pip install -r requirements.txt

# Install command (optional)
./bin/install.sh
# Or add to PATH manually
export PATH="$HOME/.local/bin:$PATH"
```

### Basic Usage | 基本使用

```bash
# Download single artwork
devart-dl url https://www.deviantart.com/username/art/title-123456

# Download all from artist
devart-dl artist username

# Download gallery
devart-dl gallery username

# Search and download
devart-dl search username "keyword"
```

### ⭐ v3.2.4 New Features Quick Start | 新功能快速开始

```bash
# 1. Auto Proxy + Auto Login (Recommended Setup)
export ALL_PROXY=http://127.0.0.1:7890  # Set proxy
devart-dl login interactive              # One-time login
devart-dl artist username                # Auto-loads proxy & cookies

# 2. Resume Support (Continue after interruption)
devart-dl artist username --ask=0        # Start download
# Press Ctrl+C to interrupt
devart-dl artist username --ask=0        # Re-run, auto-skips downloaded

# 3. 1080p HD Video Downloads
devart-dl artist username --ask=0        # Auto-downloads 1080p videos

# 4. Login Status Display
# Automatically shows at start:
# 🔓 Login Status: ✅ LOGGED IN
#    You can download original quality and mature content

# 5. High-Performance Batch Downloads
devart-dl artist username --ask=0 --proxy=http://127.0.0.1:7890
# ✓ Auto-skip existing files
# ✓ Auto-retry failures 3 times
# ✓ Real-time progress display
# ✓ 1080p video quality
```

---

## 📥 Main Features | 主要功能

### Single URL Download | 单个URL下载

```bash
# Download with full quality (default)
devart-dl url <artwork_url>

# Download original quality (requires login)
devart-dl url <artwork_url> --quality=o

# Custom filename
devart-dl url <artwork_url> --filename=my_artwork

# Organize by author
devart-dl url <artwork_url> --organize=by_author
```

### Batch Downloads | 批量下载

```bash
# Download all artworks from artist
devart-dl artist username

# Download specific gallery
devart-dl gallery username gallery_id

# Download with anti-ban protection
devart-dl gallery username --delay=2 --limit=24

# Download favorites
devart-dl fav username folder_id
```

### Search Downloads | 搜索下载

```bash
# Search user's artworks
devart-dl search username "landscape"

# Global search
devart-dl search all "digital art"
```

---

## 🔐 Authentication Methods | 身份验证方式

5 flexible authentication methods supported:

| Method | Difficulty | Recommended | Use Case |
|--------|-----------|-------------|----------|
| **Cookie File** | Easy | ✅ Recommended | Daily use |
| **Interactive Input** | Easy | ✅ Recommended | First setup |
| **Session Save** | Easiest | ✅ | Long-term use |
| **Environment Variable** | Medium | - | CI/CD, scripts |
| **Browser Auto** | Easiest | ⚠️ Unstable | Try only |

### Method 1: Browser Auto-Login (May be blocked)

**Note:** DeviantArt has anti-automation detection, this method may be blocked. Recommend Method 2 or Method 4.

```bash
# Install dependencies (first time)
pip install selenium webdriver-manager

# Try browser login
devart-dl login browser

# Specify browser
devart-dl login browser --browser=firefox
```

**Known Issues:**
- ⚠️ May encounter "Access Denied" error (anti-automation)
- ⚠️ First run needs to download driver (1-2 minutes)
- ⚠️ Requires browser to be installed

**If you encounter problems, use Method 2 (Cookie file) or Method 4 (Interactive input).**

### Method 2: Cookie File

```bash
# 1. Create cookies.txt
# 2. Paste cookie obtained from browser
# 3. Start downloading
devart-dl gallery username
```

### Method 3: Environment Variable

```bash
# Set environment variable
export DEVIANTART_COOKIES="auth=xxx; auth_secure=xxx; ..."

# Or in .env file
echo 'DEVIANTART_COOKIES=...' > .env
```

### Method 4: Interactive Input (Recommended ⭐)

```bash
# Run interactive login
devart-dl login interactive

# Paste cookie when prompted
# Choose to save as session file (y)
```

**Auto-load mechanism:**
- ✅ After saving, all commands **automatically** load cookies from session file
- ✅ No need to manually create `cookies.txt`
- ✅ No need to specify cookie path each time
- ✅ 30-day validity

### Method 5: Session Management

```bash
# Check session status
devart-dl login validate

# Clear session
devart-dl login clear

# Session file location
~/.deviantart_dl/session.json
```

### Validate Cookie

```bash
# Validate current cookie
devart-dl login validate

# Validate specific cookie
devart-dl login validate --cookies="auth=xxx; ..."

# JSON format output (for scripts)
devart-dl login check --json
```

**Validation includes:**
- ✓ Cookie existence check
- ✓ Login status verification
- ✓ User info retrieval
- ✓ Download permission test
- ✓ Cookie expiry detection

### Cookie Loading Priority

The system searches for cookies in the following order:

**For download commands (gallery, artist, url, etc.):**
1. 📁 Session file `~/.deviantart_dl/session.json` ⭐ **Priority**
2. 📄 Cookie file `cookies.txt`
3. 🌍 Environment variable `DEVIANTART_COOKIES`
4. 📋 .env file

**Recommended workflow:**
```bash
# One-time setup
devart-dl login interactive  # Save to session file

# All future commands auto-load
devart-dl artist username    # ✅ Auto-loads session
devart-dl gallery username   # ✅ Auto-loads session
devart-dl url <URL>          # ✅ Auto-loads session
```

### Quick Cookie Export

**Method 1: Console Script (Recommended ⭐)**

```javascript
// 1. Press F12 on DeviantArt logged-in page
// 2. Switch to Console tab
// 3. Paste the following code and press Enter:
(function(){let c=document.cookie;navigator.clipboard.writeText(c).then(()=>alert('✓ Cookie copied!')).catch(()=>{let t=document.createElement('textarea');t.value=c;document.body.appendChild(t);t.select();document.execCommand('copy');document.body.removeChild(t);alert('✓ Cookie copied!')})})();
// 4. Cookie automatically copied to clipboard!
```

**Method 2: Bookmarklet (Most convenient)**
- Create bookmark, name: `Export DA Cookie`
- URL: `javascript:(function(){...})()`
- Click bookmark on DeviantArt page to export

**Method 3: Manual copy (Traditional)**
- Chrome/Edge: `F12` → `Application` → `Cookies`
- Firefox: `F12` → `Storage` → `Cookie`
- Only need key cookies: `auth`, `auth_secure`, `userinfo`

**📖 Complete export guide:**
```bash
# View all export methods (recommended reading)
cat tools/COOKIE_EXPORT_GUIDE.md
```

---

## 🛡️ Anti-Ban Protection | 防封IP保护

**Important: Must-read for batch downloads**

### Recommended Config | 推荐配置

```bash
# Safe mode (recommended for beginners)
devart-dl gallery username --delay=3 --limit=10

# Balanced mode (daily use)
devart-dl gallery username --delay=2 --limit=24

# Fast mode (use cautiously)
devart-dl gallery username --delay=1 --limit=50
```

### Core Principles | 核心原则

✅ **Must do:**
- Delay ≥ 2 seconds (`--delay=2`)
- Limit batch size (`--limit=24`)
- Stop immediately on 429 error
- Spread large downloads over multiple days

❌ **Never do:**
- No delay or very short delay
- Download hundreds at once
- Ignore rate limit errors
- Continue downloading after IP ban

### Complete Guide | 完整指南

```bash
devart-dl anti-ban
```

---

## 🌍 Internationalization | 国际化

Supports Chinese and English bilingual

### Set Language | 设置语言

```bash
# Method 1: Environment variable
export DEVART_LANG=zh_CN  # Chinese
export DEVART_LANG=en_US  # English

# Method 2: Auto-detect (based on system LANG)
# Chinese system auto Chinese, English system auto English

# Test
python i18n.py --lang=zh_CN --test
python i18n.py --lang=en_US --test
```

---

## 📝 Logging System | 日志系统

Enhanced colored logging system with debug and file recording support

### Log Options | 日志选项

```bash
# Debug mode (enable file logging)
devart-dl --debug gallery username
devart-dl -d url <URL>

# Verbose mode (show all info)
devart-dl --verbose artist username
devart-dl -v gallery username

# Quiet mode (errors only)
devart-dl --quiet gallery username
devart-dl -q url <URL>
```

### Log File Location | 日志文件位置

```bash
# In debug mode, logs auto-saved to:
~/.deviantart_dl/logs/devart-dl_YYYYMMDD.log

# View logs
tail -f ~/.deviantart_dl/logs/devart-dl_*.log

# Clean old logs
rm ~/.deviantart_dl/logs/*.log
```

### Log Levels | 日志级别

| Level | Color | Purpose |
|-------|-------|---------|
| DEBUG | Cyan | Debug info (only in --debug mode) |
| INFO | Green | General information |
| WARNING | Yellow | Warning info |
| ERROR | Red | Error info |
| CRITICAL | Purple | Critical errors |

### Examples | 示例

```bash
# Debug download issues
devart-dl --debug url <URL>

# View detailed download progress
devart-dl --verbose gallery username --delay=2

# Silent background run
devart-dl --quiet artist username > /dev/null 2>&1 &
```

---

## 📁 File Organization | 文件组织

Smart file management with automatic categorization:

### Organization Modes | 组织模式

| Mode | Description | Directory Structure |
|------|-------------|---------------------|
| `by_author` | By artist (recommended) | `downloads/artist_name/artwork.jpg` |
| `by_date` | By date | `downloads/2025/01/15/artwork.jpg` |
| `by_type` | By file type | `downloads/images/artwork.jpg` |
| `by_gallery` | By gallery | `downloads/artist/gallery_name/artwork.jpg` |
| `mixed` | Hybrid (artist+date) | `downloads/artist/2025-01/artwork.jpg` |
| `flat` | Flat (no organization) | `downloads/artwork.jpg` |

### Usage Examples | 使用示例

```bash
# By artist (default)
devart-dl url <URL>
devart-dl url <URL> --organize=by_author

# By date
devart-dl gallery username --organize=by_date

# By type
devart-dl artist username --organize=by_type

# Mixed mode (author+date)
devart-dl gallery username --organize=mixed

# Flat structure
devart-dl url <URL> --organize=flat
```

### Metadata Saving | 元数据保存

Each downloaded file saves metadata to `.metadata/` directory:
- Artwork title, author, URL
- Download time, file size
- Quality setting, deviation ID
- JSON format, easy to query and manage

### View Directory Structure | 查看目录结构

```bash
python tools/file_organizer.py --mode=by_author --show-structure
python tools/file_organizer.py --mode=by_date --show-structure
```

---

## ⚙️ Configuration Options | 配置选项

### Common Options | 通用选项

| Option | Description | Default |
|--------|-------------|---------|
| `--quality=<o\|f\|p>` | Quality: o=original, f=full, p=preview | `f` |
| `--dest=<path>` | Download directory | `./downloads` |
| `--delay=<seconds>` | Delay time (anti-ban) | `1` |
| `--limit=<number>` | Batch quantity | `24` |
| `--organize=<mode>` | File organization mode | `by_author` |
| `--cookies=<path>` | Cookie file path | `cookies.txt` |
| `--proxy=<url>` | Proxy server | - |

### Global Options | 全局选项

| Option | Description |
|--------|-------------|
| `--debug, -d` | Debug mode with file logging |
| `--verbose, -v` | Verbose output |
| `--quiet, -q` | Quiet mode (errors only) |

### Examples | 示例

```bash
# Download original, delay 3 seconds
devart-dl gallery user --quality=o --delay=3

# Use proxy
devart-dl url <URL> --proxy=http://127.0.0.1:7890

# Debug mode with file organization
devart-dl --debug artist username --organize=mixed

# Silent mode, by date organization
devart-dl --quiet gallery username --organize=by_date
```

---

## 📚 Command Reference | 命令参考

### Download Commands | 下载命令

```bash
# Single artwork download
devart-dl url <artwork_url> [options]

# Artist all artworks
devart-dl artist <username> [options]

# Gallery download
devart-dl gallery <username> [gallery_id] [options]

# Search download
devart-dl search <username|all> <query> [options]

# Favorites download
devart-dl fav <username> <folder_id> [options]
```

### Tool Commands | 工具命令

```bash
# Login management
devart-dl login interactive    # Interactive login
devart-dl login browser        # Browser login
devart-dl login validate       # Validate cookie
devart-dl login clear          # Clear session

# Anti-ban guide
devart-dl anti-ban

# Test download
devart-dl test <username>

# Configuration
devart-dl config
```

### Info Commands | 信息命令

```bash
# Help
devart-dl help                 # Main help
devart-dl help <command>       # Command-specific help

# Version
devart-dl version

# Documentation
devart-dl docs
```

---

## 🏗️ Project Structure | 项目结构

```
deviantart_downloader/
├── bin/
│   ├── devart-dl              # Unified CLI entry
│   └── install.sh             # Installation script
├── deviantart_dl/             # Async core (Python 3.10+)
│   ├── __init__.py
│   ├── downloader.py          # Async downloader
│   └── api.py                 # API wrapper
├── da_downloader/             # Stable legacy version
│   ├── main.py
│   └── auth.py
├── tools/                     # Utility tools
│   ├── download_url.py        # URL downloader
│   ├── download_artist.py     # Artist downloader
│   ├── browser_login.py       # Browser auto-login
│   ├── cookie_loader.py       # Universal cookie loader
│   ├── validate_cookies.py    # Cookie validator
│   ├── file_organizer.py      # File organizer
│   ├── export_cookies.js      # Cookie export script
│   ├── logger.py              # Logging system
│   └── i18n.py                # Internationalization
├── docs/                      # Documentation
│   ├── PROJECT_STATUS.md
│   ├── QUICK_START.md
│   └── COOKIE_EXPORT_GUIDE.md
├── README.md                  # Chinese documentation
├── README_EN.md               # English documentation (this file)
├── requirements.txt           # Dependencies
├── .env.example               # Environment variable template
└── .gitignore                 # Git ignore rules
```

---

## 🔧 Advanced Usage | 高级用法

### Custom Download Script | 自定义下载脚本

```python
from deviantart_dl import DeviantArtDownloader

# Create downloader instance
dl = DeviantArtDownloader(
    cookies_file='cookies.txt',
    quality='f',
    delay=2
)

# Download single artwork
dl.download_url('https://www.deviantart.com/...')

# Batch download
artworks = dl.search_user('username', 'keyword')
for art in artworks:
    dl.download(art)
```

### Using Proxy | 使用代理

```bash
# HTTP proxy
export HTTP_PROXY=http://127.0.0.1:7890
export HTTPS_PROXY=http://127.0.0.1:7890

# SOCKS proxy
export ALL_PROXY=socks5://127.0.0.1:1080

# Command line proxy
devart-dl url <URL> --proxy=http://127.0.0.1:7890
```

### Batch Processing | 批处理

```bash
# Download multiple artists
for user in artist1 artist2 artist3; do
    devart-dl artist $user --delay=3 --organize=by_author
    sleep 60  # Wait 1 minute between artists
done

# Download from URL list
cat urls.txt | while read url; do
    devart-dl url "$url" --delay=2
done
```

---

## ❓ FAQ | 常见问题

### Q: Downloads are very slow?
**A:** Try these solutions:
1. Use proxy: `--proxy=http://...`
2. Reduce quality: `--quality=p`
3. Check network connection
4. Increase delay: `--delay=3`

### Q: Got 403 Forbidden error?
**A:** Login required:
1. Run `devart-dl login interactive`
2. Or provide cookie file
3. Check if cookie is expired

### Q: Got 429 Too Many Requests?
**A:** IP rate limited:
1. Stop downloading immediately
2. Wait a few hours
3. Use longer delay: `--delay=5`
4. Reduce batch size: `--limit=10`

### Q: How long do cookies last?
**A:** Usually a few days to weeks. Re-export if expired.

### Q: Can I use multiple cookies on different computers?
**A:** Yes, but DeviantArt may detect abnormal logins.

### Q: Does browser login work?
**A:** May be blocked by anti-automation. Recommend manual cookie export.

### Q: How to organize downloaded files?
**A:** Use `--organize` option:
- `by_author`: By artist (recommended)
- `by_date`: By date
- `mixed`: Author + date

### Q: Where are metadata files saved?
**A:** In `.metadata/` directory under download folder, JSON format.

---

## 📄 License | 许可证

MIT License - See [LICENSE](LICENSE) file

**Important Disclaimer:**
- This tool is for personal learning and research only
- Respect copyright and terms of service
- Do not use for commercial purposes
- Do not abuse or overload servers
- Author is not responsible for any consequences of misuse

---

## 🙏 Acknowledgments | 致谢

- DeviantArt for providing the platform
- All contributors and users
- Open source community

---

## 📮 Contact | 联系方式

- Issues: [GitHub Issues](https://github.com/zoidberg-xgd/deviantart-downloader/issues)
- Discussions: [GitHub Discussions](https://github.com/zoidberg-xgd/deviantart-downloader/discussions)

---

## 🌟 Star History | 星标历史

If you find this project helpful, please give it a star! ⭐

---

**Happy Downloading! 🎨**
