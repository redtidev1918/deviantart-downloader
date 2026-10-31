## 环境要求

- Python 3.10 或更高版本

## 安装（PyPI）

```bash
python -m pip install -U devart-dl
```

验证安装：

```bash
devart-dl --help
```

PyPI 项目页：<https://pypi.org/project/devart-dl/>

## 首次使用

首次下载前需要登录。最简单的方式是浏览器一键登录（本机需装 Chrome 与 Node.js 22+）：

```bash
devart-dl login browser
```

完整步骤（OAuth、Cookie 与常见问题）见 [登录与认证教程](/LOGIN.md)。

## 离线安装与历史版本

高级用户可从 [GitHub Releases](https://github.com/redtidev1918/deviantart-downloader/releases) 获取 `.whl` 或源码发行包离线安装：

```bash
python -m pip install ./devart_dl-<版本>-py3-none-any.whl
```

## 更新日志

见 [CHANGELOG](https://github.com/redtidev1918/deviantart-downloader/blob/main/CHANGELOG.md)。
