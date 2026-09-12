# Releasing

发版由 [release-please](https://github.com/googleapis/release-please) 驱动，不需要 PAT 或任何
token：`main` 上合入 release-worthy 提交后自动开/更新发版 PR，合并后由
[releasegraph](https://github.com/redtidev1918/releasegraph) 的可复用工作流在同一个
workflow run 内完成打标签、构建、GitHub Release 与 PyPI 发布。

Releases are driven by release-please and the releasegraph reusable workflow: merging a
release PR makes releasegraph tag, build, create the GitHub Release and publish to
PyPI — no PAT or token required.

本文档面向有仓库权限的维护者。人工职责是写对提交信息、合并发版 PR，并在发布后核对产物。

## 版本与事实源

| 事实 | 位置 | 谁负责 |
| --- | --- | --- |
| 版本号 | `pyproject.toml` 的 `project.version` | release-please 通过发版 PR 更新 |
| 发版配置 | `release-please-config.json`、`.release-please-manifest.json` | 手工维护（`release-type: python`、`include-v-in-tag: true`、`skip-github-release: true`） |
| 变更日志 | `CHANGELOG.md` | release-please 生成，不要手写 |
| Git tag、GitHub Release、PyPI | `v<版本号>` 标签与 Releases | releasegraph 的可复用工作流 |
| 源码运行回退版本值 | `da_downloader/__init__.py` 的 `__version__`、`da_downloader/cli.py` 的 `_version()` | 手工同步（不在自动化范围内） |

`skip-github-release: true` 表示 release-please 只负责版本号与 CHANGELOG，Release 对象由
releasegraph 在发布成功后创建，避免同一版本被两个执行者创建两次。

## 日常流程

1. **用 Conventional Commits 提交并合并到 `main`。** 提交前缀决定 bump 与 CHANGELOG 段落：
   `fix:` 进 Bug Fixes、`feat:` 进 Features，两者都会触发发版；`refactor:`/`chore:` 默认既不出现在
   CHANGELOG 也不参与 bump。希望变更对用户可见时，选 `fix`/`feat` 而不是 `refactor`。

2. **等待 release-please 打开发版 PR。** [release.yml](.github/workflows/release.yml)（名称 Release）
   在 push 到 `main`、每小时 cron（`11 * * * *`）、对 PR（`dry_run`）以及手动 `workflow_dispatch`
   时运行，转调 `redtidev1918/releasegraph/.github/workflows/reusable-release.yml`。其中
   release-please 作业只在默认分支的 push 上运行，它会打开发版 PR `chore(main): release X.Y.Z`，
   同时更新 `CHANGELOG.md`、`pyproject.toml` 的 `version` 和 `.release-please-manifest.json`。

3. **合并发版 PR。** 这次 push 触发正式发布，releasegraph 依次执行：

   | 阶段 | 动作 |
   | --- | --- |
   | Provider pre-reconcile | 对齐 registry 与已有 Release 的实际状态 |
   | Policy and release plan | 读 `.release-policy.yml`，判定 `release_health` 与本次版本 |
   | Test / Build | 执行 policy 中的测试命令（`ruff check .` 与 `pytest -m "not integration"`）与 `scripts/build-release`，并校验 wheel 名包含 `RELEASE_VERSION`；产物落在 `dist/pypi` |
   | Asset gate and draft transaction | 校验 `assets.required`（`*.whl`、`*.tar.gz`）并创建草稿 |
   | Required registry publication | 发布 GitHub Release 与 PyPI（Trusted Publishing，OIDC，免 token） |
   | Required registry verification | 回读两个 registry 确认版本可查 |
   | Publish, set Latest, audit, then prune Release objects | 创建正式 Release、设为 Latest，并按 `retention` 清理旧 Release（稳定版与预发布各保留 1 个，失败草稿保留 2 个） |

4. **发布后核对。** PyPI 能查到新版本、Release 附件齐全、`SHA256SUMS` 与实际产物的校验和一致。

`version`、`tag`、`release_health`、`run_release`、`tag_drift` 等输出由 releasegraph 返回，
含义见[如何调用发布工作流](https://github.com/redtidev1918/releasegraph/blob/main/docs/callers.md)。

## 手动恢复入口

需要重跑或修复时用 [release.yml](.github/workflows/release.yml) 的 `workflow_dispatch`：

| 输入 | 用途 |
| --- | --- |
| `version` | 指定已存在的版本；留空则读 manifest |
| `dry_run` | 只计划与构建，不发布任何东西 |
| `force` | 对已健康的版本重跑 |
| `repair` | 修复**同一个**版本的不完整发布 |
| `stage` | 只跑指定阶段 |

`release_health` 取值 `healthy` / `tag-drift` / `repair` / `missing`：不是 `healthy` 就说明实际
状态不满足 policy，此时用 `repair` 或 `force`，不要手工 `git tag -f`、`gh release create` 或
`twine upload`——那会绕开编排器维持的 exactly-once 不变量。

## 源码运行回退版本值

`da_downloader/__init__.py` 的 `__version__` 与 `da_downloader/cli.py` 中 `_version()` 的源码
运行回退值**不在自动化范围内**：它们只在未安装包元数据（直接从源码运行）时生效，发版时需
手工同步。当前 `__init__.py` 仍为 `4.0.1`，落后于 `pyproject.toml`。

## 配置 PyPI Trusted Publishing（一次性 / one-time setup）

PyPI 发布阶段使用 PyPI 的 Trusted Publisher（OIDC）认证，**不需要在 GitHub 存放任何
API token**。项目所有者只需在 PyPI 网站上做一次登记：

1. 用拥有 `devart-dl` 项目的 PyPI 账号登录
   [pypi.org](https://pypi.org/)
   （已有项目直达：
   [Manage → Publishing](https://pypi.org/manage/project/devart-dl/settings/publishing/)
   ，即 Trusted Publisher Management 页面）；
2. **Add a Trusted Publisher**（已有项目选 "Add trusted publisher"；
   全新项目在 Publishing 页添加 "pending publisher"），按以下内容填写：

   | 字段 | 值 |
   |------|------|
   | PyPI project name | `devart-dl` |
   | Owner | `redtidev1918` |
   | Repository | `deviantart-downloader` |
   | Workflow name | `release.yml` |
   | Environment name | `pypi` |

3. 保存。之后每次发版，PyPI 发布阶段会用 OIDC 换取短时上传凭据并自动发布。

> 注意：在 PyPI 上完成登记之前，发版时 PyPI 发布阶段会因 OIDC
> 校验失败而报错（GitHub Release 部分不受影响，正常发布）。登记完成
> 后即恢复，无需改仓库。

### 备选：API token / Alternative: API token

不便使用 Trusted Publishing 时，可退回传统方式：在
[PyPI API tokens](https://pypi.org/account/manage/api-tokens/) 创建
scope 限定为 `devart-dl` 的 token，在 仓库 → Settings → Secrets and
variables → Actions 添加 secret `PYPI_API_TOKEN`，并把 PyPI 渠道改成显式的
twine + token 上传方式。

## 生产分支约定

`.release-policy.yml` 的 `repository.git.productionOperations` 要求 `chore/cutover-*`、
`ops/*`、`release/*`、`hotfix/*` 这类操作分支必须基于最新 `default` 分支
（`requireLatestBase: true`），由 [branch-contract.yml](.github/workflows/branch-contract.yml)
转调 releasegraph 的分支契约门禁校验：普通功能 PR 跳过，违规的操作分支 PR 直接失败。

## 常见问题 / Notes

- 标签必须与 `pyproject.toml` 中的版本一致，否则发布失败
  （防止发错版本）/ the tag must match the package version or the publish fails;
- 主分支的 CI（[ci.yml](.github/workflows/ci.yml)）在每次 push/PR 时运行
  pytest 3.10–3.13 矩阵、ruff 检查与构建冒烟测试（`twine check`）；
- GitHub 会为最新标签自动显示 Source code (zip/tar.gz)，这两个自动源码包
  不能从 Release 页面隐藏；
- 联网集成测试默认不跑，需要时执行 `pytest -m integration`；
- 发布后几分钟内 PyPI 页面或 `pip index versions` 查不到新版本属正常传播延迟，
  不要以几分钟内的 404 判定发布失败。
