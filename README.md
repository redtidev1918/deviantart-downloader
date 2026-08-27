# DeviantArt Downloader

DeviantArt 作品批量下载工具。支持智能文件分类、多账号登录及防封控机制。

[English Documentation](README_EN.md)

[![CI](https://github.com/redtidev1918/deviantart-downloader/actions/workflows/ci.yml/badge.svg)](https://github.com/redtidev1918/deviantart-downloader/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/devart-dl.svg)](https://pypi.org/project/devart-dl/)
[![Python](https://img.shields.io/pypi/pyversions/devart-dl.svg)](https://pypi.org/project/devart-dl/)
[![Downloads](https://img.shields.io/pypi/dm/devart-dl.svg)](https://pypi.org/project/devart-dl/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

更新日志见 [CHANGELOG.md](CHANGELOG.md)。

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
git clone https://github.com/redtidev1918/deviantart-downloader.git
cd deviantart-downloader
pip install .
```

需要 Python 3.10 或更高版本。

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

> **提示**：画廊下载会遍历**所有**画廊文件夹（包括非 Featured 文件夹）。
> 下载进度保存在 `~/.deviantart_dl/progress/`，中断后重新运行同一命令即可
> 续传；上次失败的文件会自动重试。如需完全重新下载，删除对应的进度
> `.json` 文件并加 `--replace=1`。

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
devart-dl gallery username --debug=1

# 下载目录默认为 ./Downloads，可用 --dest 调整
devart-dl gallery username --dest=./my_downloads
```

---

## 文件管理

画廊/收藏夹下载默认**按作者分文件夹**保存，可用 `--separate` 控制：

```bash
devart-dl gallery username --separate=1   # 每位作者一个文件夹（默认）
devart-dl gallery username --separate=0   # 全部保存到同一目录
```

`devart-dl url` 单图下载额外支持 `--organize=<模式>` 分类归档：

| 模式 | 说明 | 示例路径 |
|------|------|-------------|
| `by_author` | 按作者分类（默认） | `downloads/artist_name/artwork.jpg` |
| `flat` | 不分类 | `downloads/artwork.jpg` |


---

## 配置参数

### 常用选项

| 选项 | 说明 | 默认值 |
|------|------|--------|
| `--quality` | 图片质量：`o` (原图, 需登录), `f` (全图), `p` (预览) | `f` |
| `--dest` | 下载目录 | `./Downloads` |
| `--delay` | 下载间隔（秒），用于防封 | `1` |
| `--limit` | 每页加载数量（1–60） | `24` |
| `--offset` | 起始偏移（配合续传使用） | `0` |
| `--separate` | 是否按作者分文件夹 `0\|1` | `1` |
| `--replace` | 是否覆盖已存在文件 `0\|1` | `0`（跳过） |
| `--cookies` | Cookie 文件路径 | `./cookies.txt` |
| `--proxy` | 代理地址 (HTTP/SOCKS) | 自动读取环境变量 |

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

支持在 Python 代码中直接调用（异步核心库）：

```python
import asyncio
from pathlib import Path
from deviantart_dl import DeviantArtDownloader, AppConfig

config = AppConfig(
    cookies_file=Path('cookies.txt'),
    destination=Path('downloads'),
    quality='full',
    ask_before_download=False,
)

async def main():
    async with DeviantArtDownloader(config) as dl:
        await dl.download_gallery('username')

asyncio.run(main())
```

---

## 常见问题

**Q: 下载不完整 / 只下了一部分 / 像是跳着下？**
A: 请升级到 **v3.3.1+**。旧版本只下载 Featured（精选）文件夹，其他画廊
文件夹里的作品会被跳过；v3.3.1 起会遍历全部画廊文件夹。同时网络请求失败
不再被误判为"下载完毕"，会明确报错并在下次运行时自动重试。

**Q: pip 安装后运行 `devart-dl` 报 ModuleNotFoundError？**
A: 请升级到 **v3.3.1+**（`pip install -U devart-dl`），安装入口已修复。

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
