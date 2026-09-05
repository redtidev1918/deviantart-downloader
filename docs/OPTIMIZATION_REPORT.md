# deviantart-downloader 优化诊断报告

> 参考仓库：[PixivFlow](https://github.com/redtidev1918/PixivFlow)（TypeScript，你的成熟 Pixiv 下载器）
> 与 [DAKit](https://github.com/redtidev1918/dakit)（Dart，DeviantArt 官方 API SDK）。
> 本文是**诊断报告**：只做现状盘点 + 对齐建议 + 优先级/风险，不改代码（除非你确认后我再动手）。

---

## 0. 结论速览

| # | 建议 | 参考来源 | 优先级 | 工作量 | 风险 |
|---|------|---------|--------|--------|------|
| A1 | 官方 OAuth API + PKCE 登录（保留 cookie 降级） | DAKit | **P0** | 大 | 中 |
| A2 | 数字 ID → UUID 解析（`_puppy/dadeviation/init`） | DAKit | **P0** | 小 | 低 |
| B1 | 合并四层重复实现（2×Config、2×Deviation、2×API client、1 个空壳 downloader） | PixivFlow | **P1** | 中 | 中 |
| B2 | 类型化错误体系 + 恢复策略（替代 54 处 `except Exception`/`sys.exit`） | PixivFlow | **P1** | 中 | 低 |
| B3 | 命令注册表替换 subprocess 分发（15 处） | PixivFlow | **P1** | 中 | 中 |
| B4 | 单一配置源 + 分层加载 + 校验 | PixivFlow | P2 | 中 | 中 |
| B5 | 日志/诊断脱敏（令牌、Cookie 永不出现在日志） | DAKit | P2 | 小 | 低 |
| B6 | 测试覆盖真实运行代码（现在漏测 tools/legacy） | PixivFlow | P2 | 中 | 低 |
| C1 | **明确不做**：WebUI、DI 容器、调度器、SQLite 迁移、delivery outbox | 两者 | — | — | — |

一句话结论：**价值最高的是 A（官方 API 对齐 DAKit），债最深的是 B1（同一套东西写了四遍）。先做 A2 + B2 + B6（小、低风险、立即见效），再做 A1 与 B1/B3。**

---

## 1. 现状盘点（target 的问题）

`deviantart-downloader` 是一个约 7.8k 行 Python 的项目，但实际结构是**四个互相平行的实现**：

```
da_downloader/    # 同步 requests，真正被 CLI 使用 + 有测试
deviantart_dl/    # 异步 httpx，「v3 架构」——半成品，未接入 CLI
legacy/           # 旧主程序（gallery/search/fav）
tools/            # 各命令的独立脚本（download_url、download_artist、auth_manager…）
```

### 1.1 同一套东西重复实现（B1 的核心证据）

| 概念 | 实现 A（在用） | 实现 B（半成品/空壳） |
|------|---------------|----------------------|
| 配置 | `da_downloader/config.py` `Config`（dataclass） | `deviantart_dl/models/config.py` `AppConfig`（pydantic） |
| 作品模型 | `da_downloader/models.py` `Deviation`（dataclass） | `deviantart_dl/models/deviation.py` `Deviation`（pydantic） |
| API 客户端 | `da_downloader/api.py` `DeviantArtAPI`（requests，同步） | `deviantart_dl/core/api_client.py` `DeviantArtAPI`（httpx，异步） |
| 下载器 | `da_downloader/downloader.py` `DeviantArtDownloader`（**真实实现**） | `deviantart_dl/core/downloader.py` `DeviantArtDownloader`（**占位，返回 `[]`**） |

**严重问题**：README「Python 脚本调用」一节让用户写
`from deviantart_dl import DeviantArtDownloader, AppConfig`——但 `deviantart_dl` 的
`DeviantArtDownloader.download_gallery()` 是空实现（`return []`）。也就是说**文档公开的 Python API 是坏的**，真正的实现藏在未文档化的 `da_downloader` 里。两个包都被 `pyproject.toml` 打进 PyPI。

### 1.2 认证与下载依赖抓取（A 的核心问题）

- 登录靠 Cookie 抓取：`document.cookie` 导出、`auth`/`auth_secure` 字段、30 天过期。
- CSRF 令牌从 HTML 里正则抠：`window.__CSRF_TOKEN__ = '...'`。
- 画廊/收藏/搜索走私有接口 `_puppy/dashared/gallection/*`。
- **原图靠抓 HTML**：请求作品页，正则匹配 `https://www.deviantart.com/download/...`。
- 依赖「防封」延时（`--delay`）来避免触发反爬。

这套做法脆弱：Cookie 过期要重导、页面改版就失效、需要人工维护反封节奏。
对比 DAKit：**官方 OAuth API + PKCE**，原图走官方 `deviation/download/{uuid}`，不做 cookie 抓取、不做防封、不把 preview 冒充 original。

### 1.3 错误处理是 ad-hoc 的（B2 的证据）

`da_downloader` + `tools` + `legacy` 里共 **54 处** `except Exception` / `except:` / `sys.exit(1)`。
典型问题：

- `download_url.py` 里 `except:` 吞掉一切再走「备用方案」；
- 用字符串匹配判错（`if '404' in html`、`'Page Not Found' in title`）；
- 失败直接 `sys.exit(1)`，没有结构化错误码，调用方无法区分「可跳过 / 需重试 / 致命」。

对比 PixivFlow：`utils/errors.ts` 有完整类型化错误层级（`PixivFlowError` 基类带 `code`/`statusCode`/`cause`，子类 `ConfigError`/`AuthenticationError`/`NetworkError`/`DownloadError`…），外加
`isSkipableError()` / `getErrorRecoveryStrategy()` / `safeAsync()` 统一重试。

### 1.4 CLI 靠 subprocess 分发（B3 的证据）

`da_downloader/cli.py` 用 **15 处** `subprocess.run([sys.executable, "-m", module, ...])` 把命令
转发到 `tools.*` / `legacy.main`。问题：

- 每个命令是独立进程，无法共享已加载的配置/会话/日志；
- 依赖 `python -m` 能找到模块（CHANGELOG 里「pip 安装后 ModuleNotFoundError」就是这条路径炸过）；
- 命令、别名、帮助、参数校验散落在各个脚本里，没有统一的注册表。

对比 PixivFlow：`CommandRegistry` + `BaseCommand`（每个命令实现 `name`/`description`/`execute`，可选 `validate`/`aliases`/`metadata`），`bootstrap()` 统一解析参数 → 加载配置 → 校验 → 执行。

### 1.5 测试没有覆盖真正运行的代码（B6 的证据）

现有测试在 `deviantart_dl/tests/`：

- `test_models.py` 测的是 pydantic 模型（半成品那套）；
- `test_stable_downloader.py` / `test_gallery_completeness.py` 测的是 `da_downloader`（真身）——**这点比想象好**；
- 但 `tools/`（download_url、download_artist、auth_manager、file_organizer…）和 `legacy/` **完全没测**，而它们正是 CLI 实际调用的路径。

对比 PixivFlow：41 个测试文件，按命令/下载/存储/工具分目录，真实行为基本全覆盖。

---

## 2. 两个参考仓库的可用模式

### PixivFlow（TS）→ 偏「工程结构 / 质量」
- **命令模式**：`CommandRegistry` + `BaseCommand`（别名、分类、编辑距离建议、`validate`、`longRunning` 标记）。
- **类型化错误 + 恢复策略**：`errors.ts` 的错误层级 + `SKIP / WAIT_AND_RETRY / RETRY / FAIL` 四态 + `safeAsync` 重试 + `getDetailedErrorInfo` 带「建议下一步」。
- **分层配置**：`defaults → env → JSON → CLI`，单一校验入口，路径解析/占位符/自动修复。
- **仓储模式**：`BaseRepository` + facade（`DownloadRepository` 内拆 Query/Write/Stats）。
- **管线模式**：`plan → execute → 落盘 → 记录 → 恢复`（下载规划器、worker 池、错误恢复策略）。
- **令牌维护**：refresh token 轮换同步写入三处，`getBestAvailableToken` 统一读取。
- **日志**：级别阈值 + 结构化 meta + 文件追加。
- **安全**：WebUI 所有文件端点保留 `startsWith(baseDir)` 路径穿越检查。

### DAKit（Dart）→ 偏「DeviantArt 领域正确性」
- **官方 OAuth API + PKCE**：Public 客户端，无 `client_secret`，`Authorization Code + PKCE`，系统浏览器 + 本地回调。
- **数字 ID → UUID**：官方 API 拒绝数字 ID，唯一抓取是公开的 `_puppy/dadeviation/init`（先读首页 CSRF，再传 `deviationid` 拿 `deviation.extended.deviationUuid`）。
- **原图走官方接口**：`deviation/download/{uuid}` 返回 `{src, filename, filesize, width, height}`，**绝不把 preview 冒充 original**。
- **集中式路由**：`ApiRoutes` 单一事实来源，一个 contract test 钉死全部路径。
- **类型化领域模型**：隐藏上游 DTO，不把上游字段透传成公共 API。
- **脱敏诊断**：令牌/授权码/Cookie/PKCE verifier 永不进日志。
- **原子下载**：`.part` 临时文件 → 校验字节数 → `os.replace`，失败清理。
- **下载档案**：`--archive` 一行一个已下载 ID，重复运行自动跳过。
- **文件名模板 + info-json**：`{id}`/`{title}`/`{username}`/`{published}`/`{filename}`/`{ext}`，每个作品旁写 `.json` 元数据。

---

## 3. 逐项建议

### A1（P0）官方 OAuth API + PKCE 登录，保留 cookie 降级

- **现状**：Cookie 抓取 + HTML 抠 CSRF + 抓 `/download/` 原图。
- **对齐 DAKit**：
  1. `login oauth --client-id XXX`：PKCE 登录，系统浏览器 + 本地回调 `http://127.0.0.1:8765/callback`，令牌存 `~/.deviantart_dl/oauth.json`（0600），自动续期。
  2. 官方 API 客户端：`user/whoami`、`deviation/{uuid}`、`deviation/download/{uuid}`（原图）、`gallery/all`、`gallery/folders`、`gallery/{folderId}`、`collections/*`、`browse/tags`。
  3. `whoami` / `logout`（撤销远端令牌）子命令。
- **保留 cookie 降级**：官方 API 拿不到的（未登录的某些私有内容）仍可走现有 cookie 路径，不破坏向后兼容。
- **工作量**：大；**风险**：中（新登录流程、需用户注册 Public 应用、要处理 refresh token 失效清理）。
- **状态**：我已新建 `da_downloader/oauth.py`（PKCE + 令牌存储 + 本地回调）和
  `da_downloader/official_api.py`（官方客户端 + UUID 解析 + 原子下载），**尚未提交、尚未接入 CLI、未测试**，等你确认方向后再继续或调整。

### A2（P0）数字 ID → UUID 解析

- **现状**：直接拿数字 `deviationId` 当 ID 用，官方 API 会拒绝。
- **对齐 DAKit**：`resolve_uuid(id, username?)`——UUID 直通，数字 ID 走 `_puppy/dadeviation/init`。
- **工作量**：小；**风险**：低。已包含在 `da_downloader/official_api.py` 里。

### B1（P1）合并四层重复实现

- **现状**：2×Config、2×Deviation、2×API client、1 个空壳 downloader；README 文档指向坏的空壳。
- **对齐 PixivFlow**：一个包、一套模型、一个客户端、一个 downloader。
  - 建议以 **`deviantart_dl` 为唯一对外包名**（README 已指向它），把 `da_downloader` 的真身实现并进去、删掉空壳；`da_downloader` 作为内部别名或直接废弃。
  - 或反过来：保留 `da_downloader` 为唯一实现，让 `deviantart_dl` 变成薄兼容层（re-export）。
- **工作量**：中；**风险**：中（涉及 import 与打包，但有测试兜底）。
- 至少先做两件低风险动作：① 修 README 的 Python API 示例指向真实实现；② 删掉 `deviantart_dl/core/downloader.py` 的空壳或让它转发到真身。

### B2（P1）类型化错误体系 + 恢复策略

- **对齐 PixivFlow**：建一个 `errors.py`（`DeviantArtError` 基类带 `code`，子类 `ConfigError`/`AuthenticationError`/`NetworkError`/`DownloadError`/`NotFoundError`），加
  `is_skipable()` / `recovery_strategy()` / `safe_call()`（带重试）。逐步替换 54 处 `except Exception`/`sys.exit(1)`。
- **工作量**：中；**风险**：低（增量替换，行为可逐处验证）。

### B3（P1）命令注册表替换 subprocess 分发

- **对齐 PixivFlow**：`Command` 抽象 + `CommandRegistry`，`bootstrap()` 统一「解析参数 → 加载配置 → 校验 → 执行」。命令的别名/帮助/参数校验集中管理，消除 subprocess 分发。
- **工作量**：中；**风险**：中（CLI 行为要回归，但命令集合小，可控）。

### B4（P2）单一配置源 + 分层加载 + 校验

- **对齐 PixivFlow**：一个 `Config`，加载链 `默认值 → 环境变量 → 配置文件 → CLI`，集中校验 + 路径解析。现在 `Config.from_args` 是一堆 `'--ask'→lambda` 的字符串映射，脆弱。
- **工作量**：中；**风险**：中。

### B5（P2）日志/诊断脱敏

- **对齐 DAKit**：确保 access/refresh token、授权码、Cookie、PKCE verifier **永不进日志**。现在 `download_url.py` 会打印 Cookie 长度（不算泄漏，但整串 Cookie 进了 HTTP header），加一条明确的脱敏纪律即可。
- **工作量**：小；**风险**：低。

### B6（P2）测试覆盖真实运行代码

- **对齐 PixivFlow**：给 `tools/download_url.py`、`tools/download_artist.py`、`tools/auth_manager.py`、`tools/file_organizer.py`、`legacy/main.py` 补测试（mock 网络层）；现有测试只覆盖 `da_downloader` 与 pydantic 模型。
- **工作量**：中；**风险**：低（纯增量）。

### C1（不做）不要移植 PixivFlow 的重型设施

deviantart-downloader 是个**命令行批量下载器**，没有常驻服务、没有持久化调度、没有 Web 界面。
PixivFlow 的 WebUI、DI 容器（其 ARCHITECTURE.md 自述「可选基础设施」）、SQLite 迁移、delivery outbox、调度器**都不该搬过来**——那是它作为常驻服务才需要的，搬来只会增加维护面。YAGNI。

---

## 4. 建议落地顺序

1. **第一批（小、低风险、立即见效）**：A2（UUID 解析，已写）+ B2（错误体系）+ B6（补测试）+ B5（脱敏纪律）。
2. **第二批（核心价值）**：A1（OAuth 登录 + 官方下载，保留 cookie 降级，接入 CLI）。
3. **第三批（还债）**：B1（合并重复）+ B3（命令注册表）+ B4（配置分层）。

每一步都可独立提交、独立验证，不必一次做完。

---

## 5. 已产生的未提交文件（等你确认）

- `da_downloader/oauth.py` —— PKCE OAuth 客户端、令牌存储、本地回调登录。
- `da_downloader/official_api.py` —— 官方 API 客户端、数字 ID→UUID 解析、原子下载。

这两个文件是 A1/A2 的初稿，**未提交、未接入 CLI、未测试**。你可以：
- 让我继续完成 A1（接入 CLI + 测试 + 文档）；
- 或先做 B2/B6（错误体系 + 测试）再回来做 A；
- 或调整这份报告的分级后我再动手。
