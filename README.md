# DeviantArt Downloader

DeviantArt 作品批量下载工具。支持智能文件分类、多账号登录及防封控机制。

[English Documentation](README_EN.md)

[![PyPI](https://img.shields.io/pypi/v/devart-dl.svg)](https://pypi.org/project/devart-dl/)
[![Python](https://img.shields.io/pypi/pyversions/devart-dl.svg)](https://pypi.org/project/devart-dl/)
[![Downloads](https://img.shields.io/pypi/dm/devart-dl.svg)](https://pypi.org/project/devart-dl/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 核心特性

- **统一命令行**：使用 `devart-dl` 即可调用所有功能。
- **多种登录支持**：支持 Cookie 文件、交互式输入、环境变量等多种方式。
- **防封控机制**：内置多种预设模式，自动控制请求频率。
- **灵活下载**：支持单图、画廊、作者全集、收藏夹及搜索结果下载。
- **断点续传**：自动记录下载进度，中断后可无缝继续。
- **高清画质**：自动优先下载最高质量（包括 1080p 视频）。
- **自动代理**：支持从环境变量自动读取代理设置。
- **文件管理**：支持按作者、日期、类型等方式自动归档文件。



---

## 快速开始

### 安装

推荐使用 `pip` 安装：

```bash
pip install devart-dl

# 如需浏览器登录支持（可选）
pip install "devart-dl[browser]"
```

也可以从源码安装：

```bash
git clone https://github.com/zoidberg-xgd/deviantart-downloader.git
cd deviantart-downloader
pip install -r requirements.txt
```

### 基本用法

```bash
# 下载单张作品
devart-dl url https://www.deviantart.com/username/art/title-123456

# 下载画师所有作品
devart-dl artist username

# 下载画廊
devart-dl gallery username

# 搜索并下载
devart-dl search username "keyword"
```

### 常用功能

**配置代理与登录**

```bash
# 设置代理（可选）
export ALL_PROXY=http://127.0.0.1:7890

# 交互式登录（推荐）
devart-dl login interactive
# 按提示输入 Cookie 后，会自动保存会话，后续命令无需再次登录

# 下载画师作品（自动使用已保存的登录信息）
devart-dl artist username
```

**断点续传与批量下载**

```bash
# 下载画师作品，若中断重新运行即可（自动跳过已下载文件）
devart-dl artist username --ask=0

# 下载 1080p 视频
# 工具会自动选择最高画质，无需额外配置
```

---

## 主要功能

### 下载模式

```bash
# 单张下载
devart-dl url <artwork_url>
# 下载原图（需登录）
devart-dl url <artwork_url> --quality=o

# 批量下载（画师、画廊、收藏夹）
devart-dl artist username
devart-dl gallery username [gallery_id]
devart-dl fav username [folder_id]

# 搜索下载
devart-dl search username "keyword"
devart-dl search all "digital art"
```

### 登录认证

为访问成熟内容或下载原图，建议进行登录配置。

1. **交互式登录（推荐）**
   
   ```bash
   devart-dl login interactive
   ```
   
   按提示输入 Cookie 即可。登录信息会保存至本地会话文件中（`~/.deviantart_dl/session.json`），长期有效。

2. **Cookie 文件**
   
   创建 `cookies.txt` 并填入浏览器导出的 Cookie，工具会自动读取。

3. **环境变量**
   
   ```bash
   export DEVIANTART_COOKIES="auth=xxx; auth_secure=xxx; ..."
   ```

> **获取 Cookie 提示**：在浏览器登录 DeviantArt 后，按 F12 打开开发者工具，在 Console 中输入 `document.cookie` 即可获取。

### 防封控机制

批量下载时建议开启延迟限制，以避免触发反爬虫策略。

```bash
# 推荐配置
devart-dl gallery username --delay=2 --limit=24
```

- `--delay`：请求间隔秒数（建议 ≥ 2秒）
- `--limit`：单次批处理数量


---

## 国际化

工具支持中英双语，会自动根据系统语言设置（`LANG`）切换。也可以手动强制设置：

```bash
export DEVART_LANG=zh_CN  # 强制中文
export DEVART_LANG=en_US  # 强制英文
```

---

## 日志系统

支持多级日志输出，便于调试和监控。

```bash
# 调试模式（详细日志并保存到文件）
devart-dl --debug gallery username

# 安静模式（仅显示错误）
devart-dl --quiet gallery username

# 日志文件默认保存位置
# ~/.deviantart_dl/logs/
```

---

## 文件管理

下载的文件默认按作者分类，也可以通过 `--organize` 参数调整。

| 模式 | 说明 | 示例路径 |
|------|------|-------------|
| `by_author` | 按作者分类（默认） | `downloads/artist_name/artwork.jpg` |
| `by_date` | 按日期分类 | `downloads/2025/01/15/artwork.jpg` |
| `by_type` | 按类型分类 | `downloads/images/artwork.jpg` |
| `by_gallery` | 按画廊分类 | `downloads/artist/gallery_name/artwork.jpg` |
| `mixed` | 混合模式 | `downloads/artist/2025-01/artwork.jpg` |
| `flat` | 不分类 | `downloads/artwork.jpg` |

此外，每次下载都会在 `.metadata/` 目录下保存对应的元数据（JSON格式），方便后续整理。


---

## 配置参数

### 常用选项

| 选项 | 说明 | 默认值 |
|------|------|--------|
| `--quality` | 图片质量：`o` (原图), `f` (全图), `p` (预览) | `f` |
| `--dest` | 下载目录 | `./downloads` |
| `--delay` | 下载间隔（秒），用于防封 | `1` |
| `--limit` | 批量下载时的数量限制 | `24` |
| `--organize` | 文件分类模式 | `by_author` |
| `--proxy` | 代理地址 (HTTP/SOCKS) | - |

### 调试选项

- `--debug, -d`：开启调试模式（输出详细日志并保存到文件）。
- `--verbose, -v`：显示详细运行信息。
- `--quiet, -q`：静默模式，仅显示错误信息。

---

## 常用命令速查

```bash
# 基础下载
devart-dl url <artwork_url>
devart-dl artist <username>
devart-dl gallery <username> [gallery_id]
devart-dl search <username|all> <query>
devart-dl fav <username> <folder_id>

# 工具命令
devart-dl login interactive    # 交互式登录
devart-dl login validate       # 验证 Cookie 有效性
devart-dl anti-ban             # 查看防封指南
devart-dl version              # 查看版本
```

---

## 高级用法

### 代理设置

除了命令行参数 `--proxy`，也支持环境变量：

```bash
# HTTP/HTTPS 代理
export ALL_PROXY=http://127.0.0.1:7890

# SOCKS5 代理
export ALL_PROXY=socks5://127.0.0.1:1080
```

### Python 脚本调用

支持在 Python 代码中直接调用：

```python
from deviantart_dl import DeviantArtDownloader

dl = DeviantArtDownloader(
    cookies_file='cookies.txt',
    quality='f',
    delay=2
)

# 下载单个作品
dl.download_url('https://www.deviantart.com/example/art/work-123')

# 搜索并下载
artworks = dl.search_user('username', 'keyword')
for art in artworks:
    dl.download(art)
```

---

## 常见问题

**Q: 下载速度慢？**
A: 建议配置代理（`--proxy`），或适当降低图片质量（`--quality=p`）。

**Q: 出现 403 Forbidden？**
A: 通常是因为未登录或 Cookie 过期。请运行 `devart-dl login interactive` 重新登录。

**Q: 出现 429 Too Many Requests？**
A: 请求过于频繁导致 IP 被限制。请停止下载数小时，并在后续使用时增加延迟（`--delay`）。

**Q: 如何导出 Cookie？**
A: 推荐使用 Chrome/Edge 开发者工具 (F12) -> Application -> Cookies，复制 `auth` 和 `auth_secure` 字段。或参考 `devart-dl login interactive` 的提示。

---

## 许可证与免责声明

本项目基于 [MIT License](LICENSE) 开源。

**注意**：本工具仅供个人学习和研究使用。使用者应遵守 DeviantArt 服务条款及版权规定，请勿用于商业用途或大规模抓取导致服务器过载。作者不对任何滥用后果负责。


