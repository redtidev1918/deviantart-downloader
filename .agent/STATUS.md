# 工程状态

> 当前工程状态的摘要快照，每次重要任务结束或发布后更新。任务进度的权威是 [TASKS.md](TASKS.md)；CI、Release、PR 的平台事实以 GitHub / PyPI 为准，本文件不复制它们。

- 更新时间：2026-10-29
- 当前版本：v4.4.4（2026-10-29 发布，GitHub Release 与 PyPI 均已核验）。同日 v4.4.3 为尺寸受限签名 403 修复版；v4.4.4 为纯文档维护版（release PR #51）。
- 分支：`main` 与远端同步；工作区干净（`.agent/` 为本日新增，随 `docs:` 提交入库）。
- 开发阶段：常规开发。近期主线：bounded-media 403 修复——网页主图与附加页改用响应提供的 fullview，并在元数据中标识展示版本。
- 生态：DeviantDrop v1.16.2 已同步同类修复并部署；DAKit / DAViewer 是 Wix 描述符解析的参照实现（AGENTS.md 生态复用规则）。

## 开放事项

- 源码回退版本号过期：`da_downloader/__init__.py` 的 `__version__ = "4.3.0"` 落后于 `pyproject.toml` 的 4.4.4；按 `RELEASING.md` 约定在下次发版时手工同步。
- 4.4.3 修复的验证边界是 150 项测试、ruff、打包与已发布包的 fixture 冒烟；未执行登录态 CLI 真实下载验收（[TASKS.md](TASKS.md) T-002）。

## 当前无阻塞

无开放 PR / issue；main 最新 CI 全绿（以 GitHub 为准）。

## 更新纪律

- 只记录可核实的事实并注明来源；不把计划写成已完成，不把测试通过写成真实下载验证。
- 与 [HANDOFF.md](HANDOFF.md) 分工：本文件管跨会话状态，HANDOFF 管单次会话交接。
