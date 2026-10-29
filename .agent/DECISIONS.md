# 技术决策记录

> 长期有效的架构与工程决策。一条决策一个事实，简短、带来源；详细论证在来源文档，不在此复制。状态：`Accepted` / `Superseded by D-XXXX`。

## D-0001 外部协议解析必须基于真实证据（源自 2026-10-13 DAViewer 事故，Accepted）

任何消费外部 API、网页协议、配置格式或第三方数据结构的解析逻辑，必须先对照独立获取的真实证据验证结构；fixture 从真实证据构建并记录来源与时间，禁止从实现反推。规则全文见 `AGENTS.md`；教训见 [LESSONS.md](LESSONS.md) L-01。

## D-0002 会话判定三态：signed_in / anonymous / unavailable（Accepted）

网页会话验证必须区分服务端确认登录（含用户名）、服务端明确未登录、网络/结构失败三态；网络错误绝不当作登出，`isLoggedIn: true` 无用户名保持 unknown。来源：`AGENTS.md` 会话判定语义。

## D-0003 OAuth 与 Cookie 是能力，不是全局模式（Accepted）

官方 API（OAuth）优先用于它能覆盖的一切；网页会话（Cookie）补足官方 API 没有的能力（如搜索、网页附加页），两者可共存组合（`CompositeProvider`）。来源：`da_downloader/download.py` build_downloader 注释。

## D-0004 原文件优先，播放源与封面严格区分（Accepted）

quality=original 且 `is_downloadable` 时走 `deviation/download/{uuid}` 原文件端点，绝不从预览 URL 重构原文件；官方 DTO 的 `content.src` 对视频只是海报，可播放地址只取 `videos[].src`；附加页视频按质量排序取最佳。来源：`da_downloader/official_api.py`、`da_downloader/provider.py`。

## D-0005 尺寸受限签名选 fullview 并显式标注（2026-10-29 随 4.4.3，Accepted）

静态图片的 Wix token 可能把尺寸约束绑定到精确重采样路径，裸 `baseUri` 因此 403：网页主图与附加页共用 `wix_media.bounded_fullview_url`（当前仅验证 token index 0）选响应提供的 fullview；展示版本在日志、元数据与 `resolve` 输出中标识，不冒充原文件；`append_media_token` 保证不重复拼接签名参数。未知签名、GIF、视频保留原选择方式。来源：`da_downloader/wix_media.py`、`tests/fixtures/deviantart-bounded-media-evidence.md`。

## D-0006 发布链：release-please + ReleaseGraph + PyPI Trusted Publishing（Accepted）

合并版本 PR 即发布（GitHub Release + PyPI OIDC，免 token）。注意两点：本仓库 `docs:` 提交也会触发维护版本（4.4.4 即纯文档触发，与 DeviantDrop 行为相反）；自动生成的 Release 说明需发布后按 AGENTS.md 双语规范人工核对修整。源码回退版本值（`__init__.py` / `cli.py`）不在自动化范围内，发版时手工同步。来源：`RELEASING.md`、`.release-policy.yml`、`.github/workflows/release.yml`。

## D-0007 `.agent/` 工程体系与权威划分（2026-10-29，Accepted）

任务进度权威是 `.agent/TASKS.md`，工程状态摘要是 `.agent/STATUS.md`，单会话交接是 `.agent/HANDOFF.md`；GitHub issues 管用户可见跟踪，CI/Release/PyPI 事实以平台为准；工程细节在 `docs/` 与仓库文档，本目录只引用不复制。参照 DAViewer D-0008、DeviantDrop D-0007 同构体系。
