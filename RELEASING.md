# Releasing

发版完全由 git 标签驱动，GitHub Actions 自动完成构建、GitHub Release 与 PyPI 发布。

Releases are fully tag-driven: GitHub Actions builds the distributions, creates
the GitHub Release, and publishes to PyPI.

## 发版步骤 / Release steps

1. **更新版本号 / Bump the version** — 三处保持一致 / keep all three in sync:

   - `pyproject.toml` → `project.version`
   - `da_downloader/__init__.py` → `__version__`
   - `da_downloader/cli.py` → `_version()` 的源码运行回退值

2. **更新 CHANGELOG.md** — 在顶部新增 `## [X.Y.Z] - YYYY-MM-DD` 小节，
   Release 的说明文字会自动从这里提取 / the GitHub Release body is extracted
   from this section.

3. **提交并打标签 / Commit and tag**:

   ```bash
   git commit -am "chore: release v4.0.1"
   git tag v4.0.1
   git push origin main v4.0.1
   ```

4. **自动流程 / What runs automatically** — [release.yml](.github/workflows/release.yml):

   1. `build`: 先运行 ruff 与 pytest，再构建 sdist + wheel、执行
      `twine check`、校验标签与版本一致，并在干净 venv 里安装 wheel；
   2. `github-release`: 从 CHANGELOG 提取对应小节，创建 GitHub Release
      并附上 `dist/*` 产物；
   3. `pypi-publish`: 通过 PyPI Trusted Publishing（OIDC，免 token）
      发布到 PyPI；
   4. `cleanup-releases`: 前两项成功后删除旧 Release；历史 git 标签不会删除。

## 配置 PyPI Trusted Publishing（一次性 / one-time setup）

`pypi-publish` 使用 PyPI 的 Trusted Publisher（OIDC）认证，**不需要在
GitHub 存放任何 API token**。项目所有者只需在 PyPI 网站上做一次登记：

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

3. 保存。之后每次推送 `v*` 标签，`pypi-publish` job 会用 OIDC 换取
   短时上传凭据并自动发布。

> 注意：在 PyPI 上完成登记之前，发版时 `pypi-publish` job 会因 OIDC
> 校验失败而报错（GitHub Release 部分不受影响，正常发布）。登记完成
> 后即恢复，无需改仓库。

### 备选：API token / Alternative: API token

不便使用 Trusted Publishing 时，可退回传统方式：在
[PyPI API tokens](https://pypi.org/account/manage/api-tokens/) 创建
scope 限定为 `devart-dl` 的 token，在 仓库 → Settings → Secrets and
variables → Actions 添加 secret `PYPI_API_TOKEN`，并把
`release.yml` 里的 `pypi-publish` job 换成 twine + token 的上传方式。

## 常见问题 / Notes

- 标签必须与 `pyproject.toml` 中的版本一致，否则 build job 直接失败
  （防止发错版本）/ the tag must match the package version or the build fails;
- 主分支的 CI（`.github/workflows/ci.yml`）在每次 push/PR 时运行
  pytest 3.10–3.13 矩阵、ruff 检查与构建冒烟测试；
- GitHub 会为最新标签自动显示 Source code (zip/tar.gz)，这两个自动源码包
  不能从 Release 页面隐藏；
- 联网集成测试默认不跑，需要时执行 `pytest -m integration`。
