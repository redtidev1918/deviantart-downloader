# 会话交接

### 2026-10-31 文档站迁移

- 从最新远端新克隆接入 VitePress 1.6.4，Node 22 构建；static.yml 重命名备份停用，新增 docs.yml 与独立 PR 文档构建检查。
- 原9份 Markdown、旧 index/vendor 均保留；语言切换使用主题菜单。下载页通过真实 v4.4.5 JSON 本地回放，保留 pip 安装说明，提交后由 docs.yml 重建。
- 应用源码、Python 依赖和版本未改，不发布新包。备份位于工作区外 backups/deviantart-downloader-4af109136801；PR CI及合并后 Pages 上线另行验收。

> 每次 Coding Agent 会话结束时追加一节，只记本会话发生的事实与下一步入口。跨会话状态在 [STATUS.md](STATUS.md)，任务在 [TASKS.md](TASKS.md)。

## 条目模板

```
### <日期> <分支 / PR>
- 本会话改动：
- 验证情况（含未跑的检查）：
- 未提交内容与风险：
- 下一步入口：
```

### 2026-10-29 main（`.agent/` 六件套入库）

- 本会话改动：本地 `main` 从落后 2 提交拉平，期间核实到 v4.4.4 维护版已由 release PR #51 合并并发布（GitHub Release 08:30 UTC，PyPI 同步，下载页已刷新）；新建本 `.agent/` 六件套（STATUS / PLAN / TASKS / DECISIONS / HANDOFF / LESSONS），并以 `docs:` 提交推送。
- 验证情况：工作区干净、与 origin 同步；无开放 PR / issue；main CI 全绿；PyPI latest = 4.4.4 实测；`__init__.py` 回退版本 4.3.0 落后已核实。未跑测试套件（无代码改动，CI 在 push 上全量执行）。
- 未提交内容与风险：无。注意：本仓库 `docs:` 提交会触发 release-please 开维护版本 PR（参见 4.4.4 先例），本次推送可能生成 4.4.5 版本 PR，合并与否由用户决定。
- 下一步入口：媒体 403 复发先看 [LESSONS.md](LESSONS.md) L-02；下次发版同步 `__init__.py` 版本号（[TASKS.md](TASKS.md) T-003）；真实下载验收随使用顺带（T-002）。
