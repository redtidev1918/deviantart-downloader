# 当前阶段计划

> 本阶段的目标、步骤与验收门槛。完成或方向变化时更新；功能开发计划以 GitHub issues / PR 为准，不在此复制。

## 阶段：bounded-media 403 修复收尾（2026-10-29）

**目标**：网页路径的媒体选择在真实 Wix 签名形态下不因裸 `baseUri` 403 而丢文件，且不把展示版本伪装成原文件。

**已完成**：

1. [x] 根因取证：裸 `baseUri` 403、同签名请求响应提供的 `fullview` 200（真实样本留存在 `tests/fixtures/`）。
2. [x] 网页主图与附加页共用 `wix_media.bounded_fullview_url` 选择规则（仅验证 token index 0），原文件下载端点优先级不变，`append_media_token` 防止重复拼接签名参数。
3. [x] 展示版本在日志、下载元数据与 `resolve` 输出中显式标识。
4. [x] 验证与发布：150 项测试 + ruff + 打包/安装冒烟；v4.4.3 发布（PR #49 / #50），PyPI 安装与 fixture 冒烟通过；v4.4.4 文档维护版随后发布。

**验收门槛**：pytest（非 integration）全绿 + ruff + wheel/sdist 构建与 twine 校验；真实下载验收顺带进行，不单独立项（[TASKS.md](TASKS.md) T-002）。

## 下一步

- 无排定大项；候选以 GitHub issues 为准。
- 媒体 403 复发先看 [LESSONS.md](LESSONS.md) L-02，确认 token 形态后再动选择逻辑。
- 下次发版时同步 `__init__.py` 源码回退版本号（`RELEASING.md`）。
