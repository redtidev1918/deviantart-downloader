# deviantart-downloader 重构最终报告

> 参考权重：gallery-dl（下载器工程）> dakit（DeviantArt API/OAuth 边界）> PixivFlow（下载编排经验）。
> 原则：只学设计与行为，未复制任何受 GPL 约束的 gallery-dl 实现代码。

---

## 1. 当前真实架构

重构采用 **strangler migration**：新的可靠下载管线是主路径，旧实现保留为兼容层。

```
CLI (da_downloader/cli.py)
  ├─ devart-dl URL            → URL-first 新管线
  ├─ devart-dl login oauth    → OAuth PKCE 登录（本地回调 + 0600 存储）
  ├─ devart-dl whoami/logout  → 官方 API 会话管理
  └─ devart-dl url/artist/... → 旧子命令（subprocess 兼容层，已标记废弃）

新管线（da_downloader/ 内的模块）：
  TargetParser  ──► DownloadTarget
        │
        ▼
  Provider（二选一）
  ├─ OfficialProvider（存在 OAuth 会话，优先）
  └─ WebProvider（Cookie 降级）
        │
        ▼
  DownloadItem（冻结 dataclass，DTO 隔离边界）
        │
        ▼
  DownloadManager（薄编排）
  ├─ DownloadArchive（SQLite 去重）
  ├─ PathFormatter（安全文件名/目录模板）
  └─ HttpDownloader（流式 / .part / Range 续传 / 429 / 校验）
        │
        ▼
  .part → 原子 rename → 最终文件
```

新模块（11 个，全部 mypy/ruff 干净）：`errors` `http` `archive` `path` `targets` `manager` `provider` `download` `official_api` `oauth` `cli`（+`models` 新增 `DownloadItem`）。

## 2. 发现的问题（审计结论）

1. **四层平行实现**：`da_downloader/`（同步，真身）、`deviantart_dl/`（异步半成品）、`legacy/`、`tools/`。2×`Config`、2×`Deviation`、2×`DeviantArtAPI`、2×`DeviantArtDownloader`（其中一个 `return []` 空壳）。
2. **README 指向坏的空壳**：「Python 脚本调用」示例导入 `deviantart_dl.DeviantArtDownloader`，其 `download_gallery()` 是空实现。
3. **内存反模式**：`legacy/deviantart_downloader.py` 和 `api.download_file()` 用 `.content` 全量载入内存。
4. **ad-hoc 错误处理**：`da_downloader`/`tools`/`legacy` 共 **54 处** `except Exception`/`sys.exit(1)`，靠字符串匹配判错。
5. **subprocess CLI 分发**：15 处 `python -m` 子进程转发，无法共享会话/配置，历史上出过 `ModuleNotFoundError`。
6. **测试没覆盖真实运行代码**：`tools/`、`legacy/` 完全没测。
7. **认证/原图靠抓取**：Cookie 抓取 + HTML 抠 CSRF + 抓 `/download/` 原图链接。

## 3. 从 gallery-dl 借鉴了什么（设计，非代码）

- **HTTP Range 续传**：`Range: bytes=N-`，处理 200/206/416，解析 `Content-Range`，服务器忽略 Range 时从头重写。
- **重试/429**：指数退避 + 封顶；429 优先 `Retry-After`，其次退避。
- **响应校验**：`Content-Type: text/html` 伪装成图片 → 拒绝；空文件拒绝；`Content-Length` 大小核对。
- **扩展名处理**：从下载 URL / 文件名提取，回退到媒体字段，不盲信 URL。
- **下载档案**：SQLite 单表 `archive(entry PRIMARY KEY)`，成功后才写入。
- **路径安全**：非法字符替换、控制字符剔除、去尾部点/空格、Windows 保留名、长度截断、路径穿越中和。
- **流式 + `.part` + 原子 rename**（`iter_content` 逐块写盘）。

## 4. 从 dakit 借鉴了什么

- **官方 OAuth API + PKCE**：Public 客户端、无 `client_secret`、系统浏览器 + 本地回调、令牌 0600 存储、自动续期。
- **数字 id → UUID**：官方 API 拒绝数字 id，唯一抓取是公开的 `_puppy/dadeviation/init`（先读首页 CSRF，再取 `deviation.extended.deviationUuid`）。
- **原图走官方接口**：`deviation/download/{uuid}`，绝不把 preview 冒充 original。
- **DTO 隔离**：`DownloadItem` 是唯一跨界契约；downloader/manager 看不到 CSRF/`_puppy`/API DTO。
- **脱敏**：令牌/Cookie 不进日志。
- **画质语义**：`original / best / preview`（旧 `o/f/p` 兼容映射）。

## 5. 从 PixivFlow 借鉴了什么

- **小类型化错误集**：7 个异常（`AuthenticationError`/`NetworkError`/`RateLimitError`/`ParseError`/`MediaUnavailableError`/`DownloadError`/`FilesystemError`）。
- **retry/backoff**：指数退避 + 封顶（`2.0 ** n`）。
- **去重 archive**：SQLite 而非 txt。
- **task/result 模型**：`DownloadOutcome(status/path/reason/size/resumed)` 供 CLI 汇总。
- **编排与传输解耦**：`DownloadManager`（编排）与 `HttpDownloader`（传输）分离。

## 6. 明确没有借鉴的东西（及原因）

| 不借鉴 | 原因 |
|--------|------|
| gallery-dl 的多站 extractor registry / Message 系统 / postprocessor 框架 | 本项目只服务 DeviantArt，不需要通用站点框架 |
| PixivFlow 的 Scheduler / WebUI / Express / Socket.IO / DeliveryOutbox / Telegram / topic pipeline | 本项目是 CLI 下载器，不是常驻自动化平台 |
| dakit 的 Flutter / platform 层 | 与 Python CLI 无关 |
| Clean Architecture 的 Controller/UseCase/Repository/Facade 层层套娃 | 抽象以解决真实变化为准；本项目 `Provider → Manager → HttpDownloader` 已够 |

## 7. 修改的代码

**新增（11 个核心模块 + 8 个测试文件）**：
`da_downloader/{errors,http,archive,path,targets,manager,provider,download,official_api,oauth}.py` + `da_downloader/cli.py`（重写为 URL-first + OAuth 命令）。
**修改**：`da_downloader/api.py`（移除下载方法，纯化 provider）、`da_downloader/downloader.py`（接入 HttpDownloader）、`da_downloader/models.py`（加 `DownloadItem`）、`README.md`（OAuth + 新 facade）、`CHANGELOG.md`（Unreleased）、`deviantart_dl/__init__.py`（弃用 shim）、`test_stable_downloader.py`（删过时测试）。

## 8. 修复的 bugs

1. README「Python 脚本调用」指向空壳 downloader → 改为新 `Downloader` facade。
2. 下载不再把整个文件读进内存（`legacy` 与 `api.download_file` 的 `.content` 反模式已从主路径消除）。
3. 下载中断后可 **Range 续传**（原先只能整文件重下）。
4. HTML 错误页/空文件不再被保存成图片（原先会存成 `.jpg`）。
5. 429 限流不再无限/立即失败，而是 `Retry-After`/退避重试。
6. 解析失败不再静默当作「下载完毕」（WebProvider/OfficialProvider 显式抛 `ParseError`）。
7. 跨会话去重从「按 session 的 JSON」改为 SQLite archive。
8. 路径穿越 / Windows 保留名 / 超长文件名在 `PathFormatter` 中中和。
9. 旧 subprocess 分发的 `ModuleNotFoundError` 风险（#1）已被 URL-first 在进程内路径规避。

## 9. 新增测试

**113 通过**（原 38 → 新增 76、删 1 个过时）。新增：
`test_http_downloader`(16) `test_archive`(5) `test_path`(12) `test_targets`(15) `test_manager`(7) `test_provider`(6) `test_download`(4) `test_cli`(6) `test_official_provider`(5)。
覆盖：200/206/416 续传、超时重试、429 Retry-After、500 后成功、404/401、HTML 伪装、零字节、Content-Length 不符、服务器忽略 Range、退避封顶、archive 幂等/持久化、路径穿越、各 URL 类型、Provider 分页/降级、facade 端到端、CLI 路由与 OAuth 命令。

## 10. CLI 兼容情况

- **保留**：`url` `artist` `gallery` `search` `fav` `login` `anti-ban` `test` `version` 子命令仍可用（`login interactive/browser/validate/clear` 不变）。
- **新增**：`devart-dl URL`（URL-first）、`login oauth`、`whoami`、`logout`。
- **新 flag**：`--dest` `--directory` `--filename` `--quality` `--archive` `--write-info-json` `--overwrite` `--cookies` `--proxy` `--timeout` `--retries` `--verbose` `--quiet`。
- **旧 flag 映射**：`--quality o|f|p` 仍被接受（等价 original/best/preview）；旧子命令里的 `--replace/--ask/--separate/--delay` 暂由其兼容层自行解析。
- **破坏性变更**：无（strangler，旧路径未删除）。

## 11. tests / ruff / mypy 结果

- **pytest**：`113 passed`（含 CI 的 `-m "not integration"` 全部离线可跑）。
- **ruff**：`ruff check .` 全绿（含 CI 的 `--select F,E9` 子集）。
- **mypy**：新增的 **11 个核心模块 + `models.py` 零错误**；遗留 33 处错误集中在旧的 `api/auth/config/downloader/progress/utils`（见第 12 条）。
- **wheel**：`python -m build` 成功，`twine check` 元数据正确，冒烟安装 `devart-dl version` 正常。

## 12. 当前剩余技术债

1. **33 处 mypy 错误**在旧文件 `api.py`/`auth.py`/`config.py`/`downloader.py`/`progress.py`/`utils.py`（缺返回注解、`no-any-return` 等）——这些是被新管线取代的旧下载器路径，未做一次性类型补全。
2. **`legacy/`、`tools/`、`deviantart_dl/` 仅标记弃用，未物理删除**（旧子命令仍经 subprocess 走它们；按「后续 major 删除」处理）。
3. **fav.me 短链**在官方路径尚未解析（需先跟随重定向拿到数字 id）；**search 目标**官方 API 无端点，仅 web 支持。
4. **无并发**：当前顺序下载（符合「先正确可靠，再谈并发」；官方 API 场景并发收益有限）。
5. **live 集成测试**未跑（需真实 OAuth 应用与测试素材；普通 CI 离线可跑已满足）。

## 13. 下一步最值得做的三个事项

1. **旧子命令改走新管线 + 物理删除 legacy/tools**：把 `url/artist/gallery/search/fav` 在进程内路由到 `TargetParser → provider → manager`，随后删除 `legacy/`、`tools/`（下载相关脚本）与 `deviantart_dl/`，彻底消除双实现；顺带清掉那 33 处 mypy 债。
2. **官方路径补 fav.me 与 search**：fav.me 跟随重定向解析数字 id；search 用 web `_puppy` 回退或标注仅 cookie 可用。
3. **live 契约测试**：把官方 API 各端点的真实响应存成 fixture，做 provider 契约测试（离线跑），避免上游改版时静默漏下载。
