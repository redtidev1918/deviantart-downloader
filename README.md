# DeviantArt Downloader

一个可靠、聚焦的 DeviantArt 下载 / 归档命令行工具。

[English Documentation](README_EN.md) · [📖 完整文档](https://redtidev1918.github.io/deviantart-downloader/) · [更新日志](CHANGELOG.md)

[![CI](https://github.com/redtidev1918/deviantart-downloader/actions/workflows/ci.yml/badge.svg)](https://github.com/redtidev1918/deviantart-downloader/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/devart-dl.svg)](https://pypi.org/project/devart-dl/)
[![Python](https://img.shields.io/pypi/pyversions/devart-dl.svg)](https://pypi.org/project/devart-dl/)
[![Downloads](https://img.shields.io/pypi/dm/devart-dl.svg)](https://pypi.org/project/devart-dl/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Docs](https://img.shields.io/badge/Docs-文档站点-6366f1?style=flat-square)](https://redtidev1918.github.io/deviantart-downloader/)

## 快速开始

需要 Python 3.10 或更高版本。

```bash
python -m pip install -U devart-dl

# 单张作品（也支持 fav.me 短链、裸 artwork id）
devart-dl https://www.deviantart.com/username/art/title-123456

# 画廊 / 作者全集
devart-dl https://www.deviantart.com/username/gallery

# 收藏夹 / 标签
devart-dl https://www.deviantart.com/username/favourites
devart-dl https://www.deviantart.com/tag/landscape
```

首次下载前建议使用 OAuth 登录：

```bash
devart-dl login oauth --client-id 你的_PUBLIC_CLIENT_ID
devart-dl whoami
```

不会注册 OAuth 应用也可以使用 Cookie。完整图文式步骤见 **[登录与认证教程](https://redtidev1918.github.io/deviantart-downloader/#/LOGIN)**。

> 普通用户无需手动下载 GitHub Release 里的 `.whl`、`.tar.gz` 或 Source code，运行上面的 `pip install` 即可。文件区别和 SHA256 校验方法见[完整文档](https://redtidev1918.github.io/deviantart-downloader/#/?id=github-release-%e9%87%8c%e7%9a%84%e6%96%87%e4%bb%b6%e6%98%af%e4%bb%80%e4%b9%88)。

## 核心特性

- **官方 API（OAuth）优先**：登录一次即可下载原图，无需导出 Cookie，也无需防封延时。
- **URL 优先**：直接粘贴作品 / 画廊 / 收藏夹 / 标签链接即可下载。
- **下载可靠**：HTTP Range 断点续传、自动重试、429 退避、原子落盘。
- **下载档案**：`--archive` 用 SQLite 记住已下载，跨会话自动跳过。
- **路径模板 + 元数据 sidecar**：`--directory`/`--filename` 模板与 `--write-info-json`。
- **代理与降级**：支持 `--proxy`；未登录 OAuth 时自动回退 Cookie。

完整的安装、登录认证、下载模式、配置参数、命令速查、Python 调用与常见问题，请看 **📖 文档站点**：

👉 https://redtidev1918.github.io/deviantart-downloader/

## 许可证与免责声明

本项目基于 [MIT License](LICENSE) 开源。

**注意**：本工具仅供个人学习和研究使用。使用者应遵守 DeviantArt 服务条款及版权规定，请勿用于商业用途或大规模抓取导致服务器过载。作者不对任何滥用后果负责。
