# 任务队列

> 任务进度的唯一权威，会话结束时更新。状态：`TODO / IN_PROGRESS / BLOCKED / DONE / DEFERRED`。用户可见的功能与缺陷跟踪以 GitHub issues 为准，本表只跟踪 Agent 工程任务，不互相复制条目。

| Id | 任务 | 状态 | 说明 / 入口 |
| --- | --- | --- | --- |
| T-001 | 建立 `.agent/` 六件套 | DONE | 2026-10-29 建立，参照 DAViewer / PixivFlow / DeviantDrop 同名体系；同日经用户确认以 `docs:` 提交入库。 |
| T-002 | 登录态 CLI 真实下载验收（bounded 作品） | DEFERRED | 4.4.3 修复只做了测试与 fixture 冒烟；随真实使用顺带验证，不单独立项。 |
| T-003 | 同步 `__init__.py` 源码回退版本号 | DEFERRED | 当前 `4.3.0` 落后 pyproject；按 `RELEASING.md` 约定随下次发版顺带同步。 |
| T-005 | 下载入口 PyPI 优先（英文下载页补安装指引、命令统一） | DONE | PR #54；docs/en/download-preview.md + previewFiles；v4.4.5 双语页重新生成；Release 正文改 PyPI 优先（标记保留） |
| T-006 | 下载页生成器停用资产表（showAssetTable），双语页精简为安装指引 | DONE | docsite#15 b82126b0；PR #57 合并 f650a7c；pin d4915deb→b82126b0/生成器/flag/preview/重新生成；本地幂等+--check+构建全过 |
| T-004 | VitePress 文档站迁移 | IN_PROGRESS | Node 22 构建、原文档保留与下载页离线回放；PR CI和合并后的Pages验收待完成，不发布应用。 |

## 更新规则

- 新任务先入表再动手；`BLOCKED` 必须写原因与解锁条件。
- `DONE` 需要证据（PR、release、测试日志）；证据不足只能保持 `IN_PROGRESS`。
