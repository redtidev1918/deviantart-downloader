# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [4.0.0] - 2026-09-05

### Added
- `fav.me` 短链现在可直接下载（自动跟随跳转解析作品）。

### Changed
- 显式子命令（`url` / `artist` / `gallery` / `search` / `fav`）现在走同一套可靠下载管线（Range 续传、下载档案、响应校验）。
- 依赖更精简：只保留 `requests`，不再安装浏览器自动化等额外组件。

### Removed
- 移除旧的 `devart-dl anti-ban`、`devart-dl test`、`devart-dl login browser`、`devart-dl login validate` 命令（改用 `devart-dl URL` 与 `login oauth` / `whoami`）。
- 移除旧的 `deviantart_dl` Python 包（改用 `da_downloader`）。

## [3.4.0] - 2026-09-05

### Added
- **官方 API（OAuth）登录**：`devart-dl login oauth --client-id …` 在浏览器中完成授权，无需导出 Cookie 或填写密码。登录后下载自动走官方 API，原图来自官方下载接口，也不再需要防封延时。
- **URL 优先**：`devart-dl URL` 直接下载（作品 / 画廊 / 收藏夹 / 标签 / fav.me 短链），无需子命令。
- **下载档案**：`--archive 文件` 用 SQLite 记住已下载内容，跨会话自动跳过。
- **文件名 / 目录模板**：`--filename`、`--directory` 支持 `{id}` `{title}` `{author}` `{published}` `{filename}` `{ext}` 等字段。
- **元数据 sidecar**：`--write-info-json` 在每个作品旁写一份 `*.json` 元数据。
- **断点续传**：中断的下载从 `.part` 文件续传，不重新下载。
- **`devart-dl whoami` / `devart-dl logout`**：查看登录状态、撤销令牌。
- **下载校验**：HTML 错误页、空文件不再被当作图片保存；遇到 429 会自动退避重试。

### Changed
- 画质参数改为 `--quality original|best|preview`（旧的 `o|f|p` 仍可用）。
- 下载改为边下边写盘，不再把整个文件读进内存。
- 解析失败、网络失败现在会明确报错，而不是被当成「下载完毕」。

## [3.3.1] - 2026-04-24

### Fixed
- **Gallery downloads only fetched the Featured folder** (`#2`): the gallection
  request now sends `all_folder=true`, so works stored in other gallery folders
  are downloaded too. Verified against the live API, which no longer rejects
  the parameter with HTTP 400.
- **Broken `pip` entry point** (`#1`): installing from PyPI produced a
  `devart-dl` launcher that crashed with `ModuleNotFoundError: No module named
  'deviantart_downloader_cli'`. The console script now points to the packaged
  `da_downloader.cli:main`, and the source-tree `bin/devart-dl` is a thin
  wrapper around the same module.
- A failed pagination request no longer silently truncates a download run:
  API/pagination errors raise `APIError` instead of being reported as
  "end of gallery", so incomplete runs are visible and resumable.
- Pagination loops detect non-advancing offsets/cursors and abort with a
  clear error instead of downloading the same page forever.
- Downloads are streamed to an atomic `.part` file and size-verified against
  `Content-Length` before replacing the target, preventing truncated files
  from being recorded as complete.
- Resume records now store output paths; a downloaded flag only counts when
  the file still exists on disk, and failed items are retried on the next run.
- Progress file writes are atomic (temp file + `os.replace`).
- Missing deviation IDs raise a parse error instead of colliding under an
  empty-string ID; filenames fall back to `title_<id>` to avoid overwrites.
- `deviantart_dl` async client compatibility with httpx >= 0.28 (`proxy=`).

### Changed
- Unified CLI (`da_downloader/cli.py`) dispatches all subcommands via
  `python -m` module execution, so installed packages no longer depend on
  source-tree script paths.
- Packaging consolidated in `pyproject.toml` (`setup.py` is a shim); tests are
  excluded from the installed wheel/sdist.

### Added
- CI workflow (pytest matrix 3.10–3.13, ruff, build check) and tag-driven
  release automation (build → GitHub Release → optional PyPI publish).
- This changelog, issue templates, and `RELEASING.md`.

## [3.3.0] - 2026-03-21

### Changed
- Default quality switched from `original` to `full`, so anonymous users get
  working downloads without a Core membership.

## [3.2.6] - 2026-03-01

### Changed
- Progress display frequency reduced to avoid log spam.

## [3.2.5] - 2026-02-20

### Added
- Per-file download progress display.

## [3.2.4] - 2026-02-10

### Changed
- Existing files are skipped by default (`--replace=1` restores old behavior).

## [3.2.3] - 2026-02-01

### Changed
- File existence check moved to the outer loop (performance).

## [3.2.2] - 2026-01-20

### Added
- Login status display before downloads.

## [3.2.1] - 2026-01-15

### Fixed
- Original-quality failures no longer block downloads; the downloader falls
  back to full quality automatically.

## [3.2.0] - 2026-01-10

### Added
- Resume support with progress tracking (`.deviantart_dl/progress`).

## [3.1.6] - 2025-12-20

### Fixed
- Video downloads select the highest available quality (1080p).

## [3.1.5] - 2025-12-10

### Added
- Video download support.

[4.0.0]: https://github.com/redtidev1918/deviantart-downloader/compare/v3.4.0...v4.0.0
[3.4.0]: https://github.com/redtidev1918/deviantart-downloader/compare/v3.3.1...v3.4.0
[3.3.1]: https://github.com/redtidev1918/deviantart-downloader/compare/v3.3.0...v3.3.1
[3.3.0]: https://github.com/redtidev1918/deviantart-downloader/compare/v3.2.6...v3.3.0
[3.2.6]: https://github.com/redtidev1918/deviantart-downloader/compare/v3.2.5...v3.2.6
[3.2.5]: https://github.com/redtidev1918/deviantart-downloader/compare/v3.2.4...v3.2.5
[3.2.4]: https://github.com/redtidev1918/deviantart-downloader/compare/v3.2.3...v3.2.4
[3.2.3]: https://github.com/redtidev1918/deviantart-downloader/compare/v3.2.2...v3.2.3
[3.2.2]: https://github.com/redtidev1918/deviantart-downloader/compare/v3.2.1...v3.2.2
[3.2.1]: https://github.com/redtidev1918/deviantart-downloader/compare/v3.2.0...v3.2.1
[3.2.0]: https://github.com/redtidev1918/deviantart-downloader/compare/v3.1.6...v3.2.0
[3.1.6]: https://github.com/redtidev1918/deviantart-downloader/compare/v3.1.5...v3.1.6
[3.1.5]: https://github.com/redtidev1918/deviantart-downloader/tag/v3.1.5
