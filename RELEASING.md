# Releasing

发版完全由 git 标签驱动，GitHub Actions 自动完成构建、GitHub Release 与 PyPI 发布。

Releases are fully tag-driven: GitHub Actions builds the distributions, creates
the GitHub Release, and publishes to PyPI.

## 发版步骤 / Release steps

1. **更新版本号 / Bump the version** — 三处保持一致 / keep all three in sync:

   - `pyproject.toml` → `project.version`
   - `da_downloader/__init__.py` → `__version__`
   - `deviantart_dl/__init__.py` → `__version__`

2. **更新 CHANGELOG.md** — 在顶部新增 `## [X.Y.Z] - YYYY-MM-DD` 小节，
   Release 的说明文字会自动从这里提取 / the GitHub Release body is extracted
   from this section.

3. **提交并打标签 / Commit and tag**:

   ```bash
   git commit -am "chore: release v3.3.1"
   git tag v3.3.1
   git push origin main v3.3.1
   ```

4. **自动流程 / What runs automatically** — [release.yml](.github/workflows/release.yml):

   1. `build`: 构建 sdist + wheel，`twine check`，校验标签与版本一致，
      在干净 venv 里安装 wheel 并运行 `devart-dl version` 冒烟测试；
   2. `github-release`: 从 CHANGELOG 提取对应小节，创建 GitHub Release
      并附上 `dist/*` 产物；
   3. `pypi-publish`: 若配置了 PyPI token，则发布到 PyPI（未配置则跳过）。

## 配置 PyPI 发布（可选 / one-time setup)

1. 在 [PyPI](https://pypi.org/account/manage/api-tokens/) 创建 API token
   （scope 限定为 `devart-dl` 项目）；
2. 仓库 → Settings → Secrets and variables → Actions →
   New repository secret，名称 `PYPI_API_TOKEN`，值为 token；
3. （可选）Settings → Environments 创建 `pypi` 环境并配置保护规则。

未配置该 secret 时，`pypi-publish` job 会自动跳过，只发布 GitHub Release。

If `PYPI_API_TOKEN` is not set, the PyPI job is skipped and only the GitHub
Release is published.

## 常见问题 / Notes

- 标签必须与 `pyproject.toml` 中的版本一致，否则 build job 直接失败
  （防止发错版本）/ the tag must match the package version or the build fails;
- 主分支的 CI（`.github/workflows/ci.yml`）在每次 push/PR 时运行
  pytest 3.10–3.13 矩阵、ruff 检查与构建冒烟测试；
- 联网集成测试默认不跑，需要时执行 `pytest -m integration`。
