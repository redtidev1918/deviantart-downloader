# 故障教训

> 已确认故障的根因与防复发规则，每条带证据来源。详细经过在回归记录与归档，不在此复制；新教训在重大问题解决后追加，沿用编号。

## L-01 未验证的协议假设能穿透整条绿色流水线

实现、测试与重构共用同一个未验证协议假设时，全绿的测试套件发现不了最基础的兼容断裂（DAViewer v0.5.14 `@publicSession` 事故；本仓库 AGENTS.md 据此固化永久规则）。
**防复发**：[DECISIONS.md](DECISIONS.md) D-0001——真实证据先行，fixture 记录来源与时间。
**来源**：`AGENTS.md` 外部协议验证规则。

## L-02 媒体 403 先解码 token 形态；两条旧经验各有适用条件（2026-10-29）

**发生了什么**：`api.py` 里 2026-09 的经验写明「fullview 的 /v1/fit|fill 模板带 token 也可能 400/404，直接用 baseUri」；而 2026-10-29 取证发现尺寸受限 token 恰好相反——裸 `baseUri` 403、响应提供的 `fullview` 200。两条经验都真实，但适用条件取决于本次响应的 token 是否带尺寸约束。
**防复发**：媒体 403 时先解码 token payload（约束写在里面）再选地址；改动选择逻辑前必须先拿到当次响应的真实样本（D-0001），不用历史经验替代当次证据；`wix_media.bounded_fullview_url` 只覆盖已验证的 token index 0 形态。
**来源**：`da_downloader/wix_media.py`、`tests/fixtures/deviantart-bounded-media-evidence.md`、`da_downloader/api.py` 2026-09 注释。

## L-03 fixture 冒烟 ≠ 真实下载验收

150 项测试、ruff、wheel 构建、PyPI 安装与 `bounded_fullview_url` 对已捕获样本的冒烟，都不能证明登录态 CLI 真实下载成功；验收边界必须如实记录（[TASKS.md](TASKS.md) T-002）。
**来源**：v4.4.3 发布验证记录（工作区归档 `2026-10-29-media-403-handoff.md`）。

## L-04 自动 Release 说明需发布后人工核对修整

releasegraph 生成的说明是原始 commit 标题，不符合 AGENTS.md 双语用户向规范（v4.4.3 曾手工重写；维护版也需确认措辞，如 4.4.4 的「本次为维护版本」）。
**防复发**：每次发布后 `gh release edit` 核对/修整（[DECISIONS.md](DECISIONS.md) D-0006）。
**来源**：v4.4.3 说明修整记录、`RELEASING.md` 发布后核对节。
