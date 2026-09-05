# DeviantArt Downloader

一个可靠、聚焦的 DeviantArt 下载 / 归档命令行工具。

[English Documentation](https://github.com/redtidev1918/deviantart-downloader/blob/main/README_EN.md)

[![CI](https://github.com/redtidev1918/deviantart-downloader/actions/workflows/ci.yml/badge.svg)](https://github.com/redtidev1918/deviantart-downloader/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/devart-dl.svg)](https://pypi.org/project/devart-dl/)
[![Python](https://img.shields.io/pypi/pyversions/devart-dl.svg)](https://pypi.org/project/devart-dl/)
[![Downloads](https://img.shields.io/pypi/dm/devart-dl.svg)](https://pypi.org/project/devart-dl/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](https://github.com/redtidev1918/deviantart-downloader/blob/main/LICENSE)

更新日志见 [CHANGELOG.md](https://github.com/redtidev1918/deviantart-downloader/blob/main/CHANGELOG.md)。

---

## 核心特性

- **官方 API（OAuth）优先**：登录一次即可下载原图，无需导出 Cookie，也无需防封延时。
- **URL 优先**：`devart-dl URL` 直接下载作品 / 画廊 / 收藏夹 / 标签 / fav.me 短链。
- **下载可靠**：HTTP Range 断点续传、自动重试、429 退避、HTML/空文件校验、原子落盘。
- **下载档案**：`--archive` 用 SQLite 记住已下载内容，跨会话自动跳过。
- **路径模板**：`--directory` / `--filename` 支持 `{id}` `{title}` `{author}` `{published}` `{ext}` 等字段，并做路径安全清洗。
- **元数据**：`--write-info-json` 在每个作品旁写一份 `.json` 元数据。
- **代理与降级**：支持 `--proxy` 与代理环境变量；未登录 OAuth 时自动回退 Cookie。

---

## 快速开始

### 安装

需要 Python 3.10 或更高版本。

```bash
python -m pip install -U devart-dl
```

### GitHub Release 里的文件是什么

**普通用户不用手动下载这些文件**，运行 `python -m pip install -U devart-dl` 即可。`pip` 会自动选择正确的包。

以 `devart_dl-4.0.1-py3-none-any.whl` 为例：

- `devart_dl`：Python 包名；
- `4.0.1`：版本号；
- `py3`：适用于 Python 3；
- `none-any`：不依赖特定 Python ABI 或操作系统。

Release 页面中的文件用途如下：

| 文件 | 是什么 | 谁需要它 |
|------|--------|----------|
| `devart_dl-X.Y.Z-py3-none-any.whl` | 已构建的 Python wheel，可用 `python -m pip install 文件名.whl` 安装 | 离线安装用户 |
| `devart_dl-X.Y.Z.tar.gz` | 发布到 PyPI 的 Python 源码发行包（sdist） | 打包工具或需要从源码构建的用户 |
| `Source code (zip)` / `Source code (tar.gz)` | GitHub 根据 git 标签自动生成的仓库快照 | 开发者阅读源码；不是普通安装包 |
| `sha256:...` | 文件内容的校验指纹，不是密码或下载链接 | 需要确认文件完整、未被替换时使用 |

校验下载文件：

```bash
# macOS / Linux
shasum -a 256 devart_dl-X.Y.Z-py3-none-any.whl

# Windows PowerShell
Get-FileHash devart_dl-X.Y.Z-py3-none-any.whl -Algorithm SHA256
```

输出应与 Release 页面显示的 SHA256 完全一致。GitHub 自动附加的两个 Source code 压缩包无法从 Release 页面隐藏。

### 基本用法（URL 优先）

```bash
# 单张作品（也支持 fav.me 短链、裸 artwork id）
devart-dl https://www.deviantart.com/username/art/title-123456

# 画廊 / 作者全集
devart-dl https://www.deviantart.com/username/gallery

# 收藏夹
devart-dl https://www.deviantart.com/username/favourites

# 标签
devart-dl https://www.deviantart.com/tag/landscape
```

### 登录（推荐 OAuth）

```bash
devart-dl login oauth --client-id 你的_PUBLIC_CLIENT_ID
devart-dl whoami     # 验证登录状态
devart-dl logout     # 撤销令牌
```

在 [deviantart.com/developers](https://www.deviantart.com/developers/) 注册一个 **Public** OAuth 应用，把 `http://127.0.0.1:8765/callback` 加入白名单。登录在浏览器中完成，无需把密码或 `client_secret` 交给 CLI。不会注册应用、需要 Cookie 登录或遇到报错时，请按[登录与认证教程](LOGIN.md)逐步操作。

---

## 主要功能

### 下载模式

URL 优先是最简单的方式；也保留显式子命令：

```bash
# URL 优先
devart-dl https://www.deviantart.com/username/art/title-123456
devart-dl https://www.deviantart.com/username/gallery
devart-dl https://www.deviantart.com/username/gallery/12345   # 指定文件夹
devart-dl https://www.deviantart.com/username/favourites
devart-dl https://www.deviantart.com/tag/landscape

# 显式子命令
devart-dl url https://www.deviantart.com/username/art/title-123456
devart-dl artist username
devart-dl gallery username [gallery_id]
devart-dl search all "digital art"
devart-dl fav username folder_id
```

> 说明：显式子命令沿用旧用法、保持兼容；官方 API 暂不提供搜索端点，`search` 走 Cookie 回退路径。

### 登录认证

**官方 API（OAuth）优先**，Cookie 作为降级方案。OAuth 支持单张作品、画廊、收藏夹和标签；Cookie 支持作者/画廊、收藏夹和搜索。完整步骤及安全说明见[登录与认证教程](LOGIN.md)。

1. **OAuth 登录（推荐）**

   ```bash
   devart-dl login oauth --client-id 你的_PUBLIC_CLIENT_ID
   ```

   - 注册 **Public** OAuth 应用，白名单精确加入 `http://127.0.0.1:8765/callback`。
   - 登录会在浏览器中完成，令牌保存到 `~/.deviantart_dl/oauth.json`（0600），自动续期。
   - 登录后下载命令自动走官方 API，原图来自官方下载接口。

2. **Cookie 登录（降级方案）**

   ```bash
   devart-dl login interactive   # 交互式输入 Cookie
   ```

   或创建 `cookies.txt`、设置 `DEVIANTART_COOKIES` 环境变量。会话保存于 `~/.deviantart_dl/session.json`。Cookie 模式不支持单张作品和标签。

### 下载档案与断点续传

```bash
# 用 SQLite 记住已下载内容，下次运行自动跳过（跨会话、跨目录都有效）
devart-dl https://www.deviantart.com/username/gallery --archive ~/.devart-dl/archive.sqlite

# 中断的下载从 .part 文件续传，无需重新下载整个文件
```

### 文件名 / 目录模板

```bash
devart-dl URL \
  --directory "{author}/{published:%Y-%m}" \
  --filename "{id}_{title}.{ext}"
```

可用字段：`{id}` `{title}` `{author}` `{username}` `{published}` `{filename}` `{ext}` `{index}`。路径会自动清洗（去除非法字符、Windows 保留名、`..` 穿越、超长名），确保结果在下载目录之内。

### 元数据 sidecar

```bash
devart-dl URL --write-info-json
# 生成 artwork.jpg 与 artwork.json（标题、作者、URL、发布时间、mature、媒体地址等）
```

---

## 配置参数

### 常用选项

| 选项 | 说明 | 默认值 |
|------|------|--------|
| `-d, --dest` | 下载根目录 | `./Downloads` |
| `--directory` | 目录模板（如 `{author}/{published:%Y}`） | `{author}` |
| `--filename` | 文件名模板（如 `{id}_{title}.{ext}`） | `{id}_{title}.{ext}` |
| `--quality` | `original`（原图，需登录）/ `best`（默认）/ `preview`；旧 `o/f/p` 仍可用 | `best` |
| `--archive` | SQLite 下载档案路径 | 无 |
| `--write-info-json` | 写元数据 sidecar | 关 |
| `--overwrite` | 覆盖已存在文件 | 关（跳过） |
| `--cookies` | Cookie 文件路径 | 环境变量/会话/`cookies.txt` |
| `--proxy` | 代理地址 | 自动读环境变量 |
| `--timeout` | 请求超时（秒） | `60` |
| `--retries` | 最大重试次数 | `3` |
| `--limit` | 每页数量 | `24` |

### 输出选项

- `-v, --verbose`：显示详细运行信息（含跳过原因）。
- `-q, --quiet`：静默模式，仅显示汇总与错误。

---

## 常用命令速查

```bash
# URL 优先（推荐）
devart-dl <URL>

# 显式子命令
devart-dl url <artwork_url>
devart-dl artist <username>
devart-dl gallery <username> [gallery_id]
devart-dl search <username|all> <query>
devart-dl fav <username> <folder_id>

# 登录 / 会话
devart-dl login oauth --client-id <ID>   # OAuth 登录（推荐）
devart-dl login interactive             # Cookie 登录（降级）
devart-dl whoami                        # 查看登录状态
devart-dl logout                        # 撤销令牌并清除本地会话

# 其他
devart-dl version
```

---

## 高级用法

### 代理设置

```bash
# 命令行参数
devart-dl URL --proxy http://127.0.0.1:7890

# 环境变量（HTTP/HTTPS 代理）
export HTTP_PROXY=http://127.0.0.1:7890
export HTTPS_PROXY=http://127.0.0.1:7890
export ALL_PROXY=http://127.0.0.1:7890
```

### Python 脚本调用

```python
from pathlib import Path
from da_downloader import Downloader
from da_downloader.download import build_downloader

downloader = build_downloader(
    destination=Path('downloads'),
    archive=Path('archive.sqlite'),   # 可选：已下载自动跳过
    quality='best',                   # original / best / preview
    write_info_json=True,             # 每个作品旁写一份 metadata .json
)

results = downloader.download('https://www.deviantart.com/username/gallery')
for r in results:
    print(r.status, r.path)
```

已通过 `devart-dl login oauth` 登录时自动走官方 API，否则回退到 Cookie。

---

## 常见问题

**Q: 下载不完整 / 只下了一部分 / 像是跳着下？**
A: 请升级到 **v3.4.0+**。旧版本只下载 Featured（精选）文件夹；v3.3.1 起遍历全部画廊文件夹，v3.4.0 起解析失败与网络失败会明确报错，且中断可 Range 续传。

**Q: pip 安装后运行 `devart-dl` 报 ModuleNotFoundError？**
A: 请升级到 **v3.4.0+**（`pip install -U devart-dl`），安装入口已修复。

**Q: 出现 403 Forbidden？**
A: 通常是未登录或 Cookie 过期。优先 `devart-dl login oauth`（官方 API）；或 `devart-dl login interactive` 更新 Cookie。

**Q: 出现 429 Too Many Requests？**
A: 使用官方 API（OAuth 登录）通常不会触发；Cookie 路径下会自动退避重试，若仍频繁 429，请暂停一段时间再试。

**Q: 下载速度慢？**
A: 建议配置代理（`--proxy`），或降低画质（`--quality preview`）。

**Q: 如何导出 Cookie？**
A: 推荐 Chrome/Edge 开发者工具 (F12) → Application → Cookies，复制 `auth` 和 `auth_secure` 字段；或 `devart-dl login interactive` 按提示粘贴。详见[登录与认证教程](LOGIN.md)。

**Q: Release 里的 `.whl`、`.tar.gz` 和 SHA256 是什么？**
A: 普通用户直接运行 `python -m pip install -U devart-dl`，无需下载。区别和校验方法见上面的[GitHub Release 文件说明](#github-release-里的文件是什么)。

---

## 许可证与免责声明

本项目基于 [MIT License](https://github.com/redtidev1918/deviantart-downloader/blob/main/LICENSE) 开源。

**注意**：本工具仅供个人学习和研究使用。使用者应遵守 DeviantArt 服务条款及版权规定，请勿用于商业用途或大规模抓取导致服务器过载。作者不对任何滥用后果负责。

---

## 网络 / 出口要求（重要）

DeviantArt 会对「数据中心出口 IP」实施封锁（WAF 按 ASN/IP 段放行名单）：

- **实测被拦**：Cloudflare Workers（网页 403、官方 API 数据面 500）、Fly.io（网页 403）及多数云主机的网页路径；部分机场/机房 IP 访问媒体变体（`/v1/fit|fill`）也会 400/404。
- **可用的出口**：住宅网络实测全部正常；部分小型 VPS/机场（海外住宅类出口）也可用。
- **建议**：在本机/住宅网络运行；云服务器上请经 clash/mihomo 等代理走放行出口，或使用官方 OAuth API（部分数据面相对放行，但同样受限时请加代理）。

症状通常是：请求 `www.deviantart.com` 返回 403、官方 API 数据端点 500、或媒体下载 400/404 且换 UA/加 Referer 无效——先换出口排查，而不是改代码。

