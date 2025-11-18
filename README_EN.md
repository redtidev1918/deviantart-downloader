# DeviantArt Downloader

A powerful, feature-rich DeviantArt artwork downloader with intelligent file organization, multiple authentication methods, and anti-ban protection.

[中文文档](README.md) | **English Documentation**

[![Python](https://img.shields.io/badge/Python-3.6%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![i18n](https://img.shields.io/badge/i18n-中文%20%7C%20English-orange.svg)](#internationalization)
[![Version](https://img.shields.io/badge/Version-3.0.0-brightgreen.svg)](#)

---

## ✨ Core Features

- 🚀 **Unified CLI** - Single `devart-dl` command for all features
- 🔐 **5 Login Methods** - Cookie file, interactive input, session save, environment variable, browser
- 🛡️ **Smart Anti-Ban** - 4 preset modes, auto-delay, rate limiting
- 🎯 **Flexible Downloads** - Single URL, full artist collection, batch gallery, search filters
- 📝 **Enhanced Logging** - Colored output, file logging, debug mode
- 📁 **Smart Organization** - 6 file organization modes with metadata
- 🌍 **Internationalization** - Chinese/English bilingual support, auto-detection
- ⚡ **High Performance** - Async download architecture (Python 3.10+)
- 📦 **Zero Config** - Works out of the box, progressive enhancement
- 🏗️ **Modular** - Clean project structure, easy to maintain

---

## 🚀 Quick Start

### Installation

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

### Basic Usage

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

---

## 📥 Main Features

### Single URL Download

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

### Batch Downloads

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

### Search Downloads

```bash
# Search user's artworks
devart-dl search username "landscape"

# Global search
devart-dl search all "digital art"
```

---

## 🔐 Authentication Methods

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

### Method 4: Interactive Input

```bash
# Run interactive login
devart-dl login interactive

# Follow prompts to paste cookie
```

### Method 5: Session Save

```bash
# Automatically saved to ~/.deviantart_dl/session.json after first login
# 30-day validity, auto-loads

# Clear session
devart-dl login clear
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

### Quick Cookie Export 

### One-click export script (Fastest)

```javascript
// 1. Press F12 on DeviantArt logged-in page
// 2. Switch to Console tab
// 3. Paste the following code and press Enter:
(function(){let c=document.cookie;navigator.clipboard.writeText(c).then(()=>alert('✓ Cookie copied!')).catch(()=>{let t=document.createElement('textarea');t.value=c;document.body.appendChild(t);t.select();document.execCommand('copy');document.body.removeChild(t);alert('✓ Cookie copied!')})})();
// 4. Cookie automatically copied to clipboard!
```

**Method 2: Visual export (with UI)**
- Use complete `tools/export_cookies.js` script
- Beautiful export panel appears
- Distinguish key cookies and full cookies

**Method 3: Bookmarklet (Most convenient)**
- Create bookmark, fill URL with above script
- Click bookmark on DeviantArt page
- One-click export

**Method 4: Manual copy (Traditional)**
- Chrome/Edge: `F12` → `Application` → `Cookies`
- Firefox: `F12` → `Storage` → `Cookie`

**📖 Complete export guide:**
```bash
# View all export methods (recommended reading)
cat tools/COOKIE_EXPORT_GUIDE.md
```

---

## 🛡️ Anti-Ban Protection

**Important: Must-read for batch downloads**

### Recommended Config

```bash
# Safe mode (recommended for beginners)
devart-dl gallery username --delay=3 --limit=10

# Balanced mode (daily use)
devart-dl gallery username --delay=2 --limit=24

# Fast mode (use cautiously)
devart-dl gallery username --delay=1 --limit=50
```

### Core Principles

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

### Complete Guide

```bash
devart-dl anti-ban
```

---

## 🌍 Internationalization

Supports Chinese and English bilingual

### Set Language

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

## 📝 Logging System

Enhanced colored logging system with debug and file recording support

### Log Options

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

### Log File Location

```bash
# In debug mode, logs auto-saved to:
~/.deviantart_dl/logs/devart-dl_YYYYMMDD.log

# View logs
tail -f ~/.deviantart_dl/logs/devart-dl_*.log

# Clean old logs
rm ~/.deviantart_dl/logs/*.log
```

### Log Levels

| Level | Color | Purpose |
|-------|-------|---------|
| DEBUG | Cyan | Debug info (only in --debug mode) |
| INFO | Green | General information |
| WARNING | Yellow | Warning info |
| ERROR | Red | Error info |
| CRITICAL | Purple | Critical errors |

### Examples

```bash
# Debug download issues
devart-dl --debug url <URL>

# View detailed download progress
devart-dl --verbose gallery username --delay=2

# Silent background run
devart-dl --quiet artist username > /dev/null 2>&1 &
```

---

## 📁 File Organization 

Smart file management with automatic categorization:

### Organization Modes

| Mode | Description | Directory Structure |
|------|-------------|---------------------|
| `by_author` | By artist (recommended) | `downloads/artist_name/artwork.jpg` |
| `by_date` | By date | `downloads/2025/01/15/artwork.jpg` |
| `by_type` | By file type | `downloads/images/artwork.jpg` |
| `by_gallery` | By gallery | `downloads/artist/gallery_name/artwork.jpg` |
| `mixed` | Hybrid (artist+date) | `downloads/artist/2025-01/artwork.jpg` |
| `flat` | Flat (no organization) | `downloads/artwork.jpg` |

### Usage Examples

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

### Metadata Saving

Each downloaded file saves metadata to `.metadata/` directory:
- Artwork title, author, URL
- Download time, file size
- Quality setting, deviation ID
- JSON format, easy to query and manage

### View Directory Structure

```bash
python tools/file_organizer.py --mode=by_author --show-structure
python tools/file_organizer.py --mode=by_date --show-structure
```

---

## ⚙️ Configuration Options

### Common Options

| Option | Description | Default |
|--------|-------------|---------|
| `--quality=<o\|f\|p>` | Quality: o=original, f=full, p=preview | `f` |
| `--dest=<path>` | Download directory | `./downloads` |
| `--delay=<seconds>` | Delay time (anti-ban) | `1` |
| `--limit=<number>` | Batch quantity | `24` |
| `--organize=<mode>` | File organization mode | `by_author` |
| `--cookies=<path>` | Cookie file path | `cookies.txt` |
| `--proxy=<url>` | Proxy server | - |

### Global Options

| Option | Description |
|--------|-------------|
| `--debug, -d` | Debug mode with file logging |
| `--verbose, -v` | Verbose output |
| `--quiet, -q` | Quiet mode (errors only) |

### Examples

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

## 📚 Command Reference

### Download Commands

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

### Tool Commands

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

### Info Commands

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

## 🏗️ Project Structure

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

## 🔧 Advanced Usage

### Custom Download Script

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

### Using Proxy

```bash
# HTTP proxy
export HTTP_PROXY=http://127.0.0.1:7890
export HTTPS_PROXY=http://127.0.0.1:7890

# SOCKS proxy
export ALL_PROXY=socks5://127.0.0.1:1080

# Command line proxy
devart-dl url <URL> --proxy=http://127.0.0.1:7890
```

### Batch Processing

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

## ❓ FAQ

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

## 📄 License

MIT License - See [LICENSE](LICENSE) file

**Important Disclaimer:**
- This tool is for personal learning and research only
- Respect copyright and terms of service
- Do not use for commercial purposes
- Do not abuse or overload servers
- Author is not responsible for any consequences of misuse

---

## 🙏 Acknowledgments

- DeviantArt for providing the platform
- All contributors and users
- Open source community

---

## 📮 Contact

- Issues: [GitHub Issues](https://github.com/zoidberg-xgd/deviantart-downloader/issues)
- Discussions: [GitHub Discussions](https://github.com/zoidberg-xgd/deviantart-downloader/discussions)

---

## 🌟 Star History

If you find this project helpful, please give it a star! ⭐

---

**Happy Downloading! 🎨**
