# DeviantArt Downloader

一个功能强大、特性丰富的 DeviantArt 作品下载工具，支持智能文件组织、多种身份验证方式和防封IP保护。

A powerful, feature-rich DeviantArt artwork downloader with intelligent file organization, multiple authentication methods, and anti-ban protection.

**中文文档** | [English Documentation](README_EN.md)

[![PyPI](https://img.shields.io/pypi/v/devart-dl.svg)](https://pypi.org/project/devart-dl/)
[![Python](https://img.shields.io/pypi/pyversions/devart-dl.svg)](https://pypi.org/project/devart-dl/)
[![Downloads](https://img.shields.io/pypi/dm/devart-dl.svg)](https://pypi.org/project/devart-dl/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![i18n](https://img.shields.io/badge/i18n-中文%20%7C%20English-orange.svg)](#国际化)

---

## ✨ 核心特性 | Core Features

-  **统一CLI** - 单一命令 `devart-dl` 访问所有功能
-  **5种登录方式** - Cookie文件、交互输入、会话保存、环境变量、浏览器
-  **智能防封**   - 4种预设模式、自动延迟、速率限制
-  **灵活下载**   - URL单图、作者全集、画廊批量、搜索过滤
-  **断点续传**   - 中断后自动继续，智能跳过已下载
-  **失败重试**   - 网络错误自动重试3次
-  **1080p视频**   - 自动选择最高质量视频
-  **自动代理**   - 自动从环境变量加载代理
-  **增强日志**   - 彩色输出、文件日志、登录状态显示
-  **国际化**   - 中文/英文双语支持，自动检测
-  **高性能**   - 异步下载架构，快速跳过已存在文件
-  **零配置**   - 开箱即用，渐进式增强
-  **模块化**   - 清晰的项目结构，易于维护


---

## 🚀 快速开始 | Quick Start

### 安装 | Installation

**方式1: 从 PyPI 安装（推荐）⭐**

```bash
# 基础安装
pip install devart-dl

# 或带浏览器登录支持
pip install devart-dl[browser]
```

**方式2: 从源码安装**

```bash
# 克隆仓库
git clone https://github.com/zoidberg-xgd/deviantart-downloader.git
cd deviantart-downloader

# 安装依赖
pip install -r requirements.txt

# 安装统一命令（可选）
./bin/install.sh
```

### 基本使用 | Basic Usage

```bash
# 下载单个作品
devart-dl url https://www.deviantart.com/username/art/title-123456

# 下载作者所有作品
devart-dl artist username

# 下载画廊
devart-dl gallery username

# 搜索并下载
devart-dl search username "keyword"
```

### ⭐ v3.2.4 新功能快速开始

```bash
# 1. 自动代理 + 自动登录（推荐设置）
export ALL_PROXY=http://127.0.0.1:7890  # 设置代理
devart-dl login interactive              # 一次性登录
devart-dl artist username                # 自动加载代理和Cookie

# 2. 断点续传（中断后继续）
devart-dl artist username --ask=0        # 开始下载
# 按 Ctrl+C 中断
devart-dl artist username --ask=0        # 重新运行，自动跳过已下载

# 3. 1080p 高清视频下载
devart-dl artist username --ask=0        # 自动下载1080p视频

# 4. 登录状态显示
# 启动时自动显示：
# 🔓 登录状态: ✅ 已登录
#    您可以下载原图质量和成熟内容

# 5. 高性能批量下载
devart-dl artist username --ask=0 --proxy=http://127.0.0.1:7890
# ✓ 自动跳过已存在文件
# ✓ 失败自动重试3次
# ✓ 实时进度显示
# ✓ 1080p视频质量
```

---

## 📥 主要功能 | Main Features

### 单个URL下载 | Single URL Download

```bash
# 下载全图质量（默认）
devart-dl url <artwork_url>

# 下载原图质量（需要登录）
devart-dl url <artwork_url> --quality=o

# 自定义文件名
devart-dl url <artwork_url> --filename=my_artwork

# 按作者组织
devart-dl url <artwork_url> --organize=by_author
```

### 批量下载 | Batch Downloads

```bash
# 下载作者所有作品
devart-dl artist username

# 下载特定画廊
devart-dl gallery username gallery_id

# 防封保护下载
devart-dl gallery username --delay=2 --limit=24

# 下载收藏夹
devart-dl fav username folder_id
```

### 搜索下载 | Search Downloads

```bash
# 搜索用户作品
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

### 方式4: 交互式输入（推荐 ⭐）

```bash
# 运行交互式登录
devart-dl login interactive

# 按提示粘贴 Cookie
# 选择保存为会话文件 (y)
```

**自动加载机制：**
- ✅ 保存后，所有命令**自动**从会话文件加载 Cookie
- ✅ 无需手动创建 `cookies.txt`
- ✅ 无需每次指定 Cookie 路径
- ✅ 有效期 30 天

### 方式5: 会话管理

```bash
# 查看会话状态
devart-dl login validate

# 清除会话
devart-dl login clear

# 会话文件位置
~/.deviantart_dl/session.json
```

### 验证 Cookie 是否有效

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

### Cookie 加载优先级

系统会按以下顺序查找 Cookie：

**下载命令（gallery, artist, url 等）：**
1. 📁 会话文件 `~/.deviantart_dl/session.json` ⭐ **优先**
2. 📄 Cookie 文件 `cookies.txt`
3. 🌍 环境变量 `DEVIANTART_COOKIES`
4. 📋 .env 文件

**推荐工作流：**
```bash
# 一次性设置
devart-dl login interactive  # 保存到会话文件

# 以后所有命令自动使用
devart-dl artist username    # ✅ 自动加载会话
devart-dl gallery username   # ✅ 自动加载会话
devart-dl url <URL>          # ✅ 自动加载会话
```

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

✅ **必须做：**
- 延迟 ≥ 2秒 (`--delay=2`)
- 限制批次大小 (`--limit=24`)
- 遇到 429 错误立即停止
- 将大量下载分散到多天

❌ **绝不能做：**
- 无延迟或非常短的延迟
- 一次下载数百个
- 忽略限速错误
- IP被封后继续下载

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
|-------|-------|------|
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

## 📁 文件组织 | File Organization

智能管理下载的文件，自动分类整理：

### 组织模式 | Organization Modes

| 模式 | 说明 | 目录结构示例 |
|------|------|-------------|
| `by_author` | 按作者分类（推荐） | `downloads/artist_name/artwork.jpg` |
| `by_date` | 按日期分类 | `downloads/2025/01/15/artwork.jpg` |
| `by_type` | 按文件类型分类 | `downloads/images/artwork.jpg` |
| `by_gallery` | 按画廊分类 | `downloads/artist/gallery_name/artwork.jpg` |
| `mixed` | 混合模式（作者+日期） | `downloads/artist/2025-01/artwork.jpg` |
| `flat` | 扁平结构（无分类） | `downloads/artwork.jpg` |

### 使用示例 | Usage Examples

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

### 元数据保存 | Metadata Saving

每个下载的文件都会保存元数据到 `.metadata/` 目录：
- 作品标题、作者、URL
- 下载时间、文件大小
- 质量设置、deviation ID
- JSON 格式，易于查询和管理

### 查看目录结构 | View Directory Structure

```bash
python tools/file_organizer.py --mode=by_author --show-structure
python tools/file_organizer.py --mode=by_date --show-structure
```

---

## ⚙️ 配置选项 | Configuration Options

### 通用选项

| 选项 | 说明 | 默认值 |
|------|------|--------|
| `--quality=<o\|f\|p>` | 质量：o=原图, f=全图, p=预览 | `f` |
| `--dest=<path>` | 下载目录 | `./downloads` |
| `--delay=<seconds>` | 延迟时间（防封） | `1` |
| `--limit=<number>` | 每批数量 | `24` |
| `--organize=<mode>` | 文件组织模式 | `by_author` |
| `--cookies=<path>` | Cookie文件路径 | `cookies.txt` |
| `--proxy=<url>` | 代理服务器 | - |

### 全局选项

| 选项 | 说明 |
|------|------|
| `--debug, -d` | 调试模式，启用文件日志 |
| `--verbose, -v` | 详细输出 |
| `--quiet, -q` | 安静模式（仅错误） |

### 示例

```bash
# 下载原图，延迟3秒
devart-dl gallery user --quality=o --delay=3

# 使用代理
devart-dl url <URL> --proxy=http://127.0.0.1:7890

# 调试模式与文件组织
devart-dl --debug artist username --organize=mixed

# 安静模式，按日期组织
devart-dl --quiet gallery username --organize=by_date
```

---

## 📚 命令参考 | Command Reference

### 下载命令 | Download Commands

```bash
# 单个作品下载
devart-dl url <artwork_url> [options]

# 作者所有作品
devart-dl artist <username> [options]

# 画廊下载
devart-dl gallery <username> [gallery_id] [options]

# 搜索下载
devart-dl search <username|all> <query> [options]

# 收藏夹下载
devart-dl fav <username> <folder_id> [options]
```

### 工具命令 | Tool Commands

```bash
# 登录管理
devart-dl login interactive    # 交互式登录
devart-dl login browser        # 浏览器登录
devart-dl login validate       # 验证Cookie
devart-dl login clear          # 清除会话

# 防封指南
devart-dl anti-ban

# 测试下载
devart-dl test <username>

# 配置管理
devart-dl config
```

### 信息命令 | Info Commands

```bash
# 帮助
devart-dl help                 # 主要帮助
devart-dl help <command>       # 命令具体帮助

# 版本
devart-dl version

# 文档
devart-dl docs
```

---

## 🔧 高级用法 | Advanced Usage

### 使用代理

```bash
# HTTP代理
export HTTP_PROXY=http://127.0.0.1:7890
export HTTPS_PROXY=http://127.0.0.1:7890

# SOCKS代理
export ALL_PROXY=socks5://127.0.0.1:1080

# 命令行代理
devart-dl url <URL> --proxy=http://127.0.0.1:7890
```

### 批处理

```bash
# 批量下载多个用户
for user in artist1 artist2 artist3; do
    devart-dl artist $user --delay=3 --organize=by_author
    sleep 60  # 用户间休息1分钟
done

# 从URL列表下载
cat urls.txt | while read url; do
    devart-dl url "$url" --delay=2
done
```

### 自定义下载脚本

```python
from deviantart_dl import DeviantArtDownloader

# 创建下载器实例
dl = DeviantArtDownloader(
    cookies_file='cookies.txt',
    quality='f',
    delay=2
)

# 下载单个作品
dl.download_url('https://www.deviantart.com/...')

# 批量下载
artworks = dl.search_user('username', 'keyword')
for art in artworks:
    dl.download(art)
```

---

## ❓ 常见问题 | FAQ

### Q: 下载非常慢？
**A:** 尝试这些解决方法：
1. 使用代理：`--proxy=http://...`
2. 降低质量：`--quality=p`
3. 检查网络连接
4. 增加延迟：`--delay=3`

### Q: 遇到 403 Forbidden 错误？
**A:** 需要登录：
1. 运行 `devart-dl login interactive`
2. 或提供 Cookie 文件
3. 检查 Cookie 是否过期

### Q: 遇到 429 Too Many Requests？
**A:** IP 被限速：
1. 立即停止下载
2. 等待几小时
3. 使用更长延迟：`--delay=5`
4. 减少批次大小：`--limit=10`

### Q: Cookie 能用多久？
**A:** 通常几天到几周。过期后重新导出。

### Q: 可以在多台电脑使用同一个 Cookie 吗？
**A:** 可以，但 DeviantArt 可能会检测异常登录。

### Q: 浏览器登录有效吗？
**A:** 可能被反自动化检测阻止。推荐手动导出 Cookie。

### Q: 如何组织下载的文件？
**A:** 使用 `--organize` 选项：
- `by_author`: 按作者（推荐）
- `by_date`: 按日期
- `mixed`: 作者 + 日期

### Q: 元数据文件保存在哪里？
**A:** 在下载目录下的 `.metadata/` 目录中，JSON 格式。


---

## 🤝 贡献 | Contributing

欢迎贡献代码、报告问题或提出建议！

```bash
# Fork项目 → 创建分支 → 提交代码 → Pull Request
```

---

## 📄 许可证 | License

MIT License - 查看 [LICENSE](LICENSE) 文件


---

- 感谢开源社区

---

## 📮 联系方式 | Contact

- Issues: [GitHub Issues](https://github.com/zoidberg-xgd/deviantart-downloader/issues)
- Discussions: [GitHub Discussions](https://github.com/zoidberg-xgd/deviantart-downloader/discussions)

---

## 🌟 Star History

如果觉得这个项目有帮助，请给个 Star！⭐

---

**Happy Downloading! 🎨**

