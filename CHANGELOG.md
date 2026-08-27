# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [3.3.1] - 2026-04-24

### Fixed
- **Gallery downloads only fetched the Featured folder** (`#2`): the gallection
  request now sends `all_folder=true`, so works stored in other gallery folders
  are downloaded too. Verified against the live API, which no longer rejects
  the parameter with HTTP 400.
- **Broken `pip` entry point** (`#1`): installing from PyPI produced a
  `devart-dl` launcher that crashed with `ModuleNotFoundError: No module named
  'deviantart_downloader_cli'`. The console script now points to the packaged
  `da_downloader.cli:main`, and the source-tree `bin/devart-dl` is a thin
  wrapper around the same module.
- A failed pagination request no longer silently truncates a download run:
  API/pagination errors raise `APIError` instead of being reported as
  "end of gallery", so incomplete runs are visible and resumable.
- Pagination loops detect non-advancing offsets/cursors and abort with a
  clear error instead of downloading the same page forever.
- Downloads are streamed to an atomic `.part` file and size-verified against
  `Content-Length` before replacing the target, preventing truncated files
  from being recorded as complete.
- Resume records now store output paths; a downloaded flag only counts when
  the file still exists on disk, and failed items are retried on the next run.
- Progress file writes are atomic (temp file + `os.replace`).
- Missing deviation IDs raise a parse error instead of colliding under an
  empty-string ID; filenames fall back to `title_<id>` to avoid overwrites.
- `deviantart_dl` async client compatibility with httpx >= 0.28 (`proxy=`).

### Changed
- Unified CLI (`da_downloader/cli.py`) dispatches all subcommands via
  `python -m` module execution, so installed packages no longer depend on
  source-tree script paths.
- Packaging consolidated in `pyproject.toml` (`setup.py` is a shim); tests are
  excluded from the installed wheel/sdist.

### Added
- CI workflow (pytest matrix 3.10–3.13, ruff, build check) and tag-driven
  release automation (build → GitHub Release → optional PyPI publish).
- This changelog, issue templates, and `RELEASING.md`.

## [3.3.0] - 2026-03-21

### Changed
- Default quality switched from `original` to `full`, so anonymous users get
  working downloads without a Core membership.

## [3.2.6] - 2026-03-01

### Changed
- Progress display frequency reduced to avoid log spam.

## [3.2.5] - 2026-02-20

### Added
- Per-file download progress display.

## [3.2.4] - 2026-02-10

### Changed
- Existing files are skipped by default (`--replace=1` restores old behavior).

## [3.2.3] - 2026-02-01

### Changed
- File existence check moved to the outer loop (performance).

## [3.2.2] - 2026-01-20

### Added
- Login status display before downloads.

## [3.2.1] - 2026-01-15

### Fixed
- Original-quality failures no longer block downloads; the downloader falls
  back to full quality automatically.

## [3.2.0] - 2026-01-10

### Added
- Resume support with progress tracking (`.deviantart_dl/progress`).

## [3.1.6] - 2025-12-20

### Fixed
- Video downloads select the highest available quality (1080p).

## [3.1.5] - 2025-12-10

### Added
- Video download support.

[3.3.1]: https://github.com/redtidev1918/deviantart-downloader/compare/v3.3.0...v3.3.1
[3.3.0]: https://github.com/redtidev1918/deviantart-downloader/compare/v3.2.6...v3.3.0
[3.2.6]: https://github.com/redtidev1918/deviantart-downloader/compare/v3.2.5...v3.2.6
[3.2.5]: https://github.com/redtidev1918/deviantart-downloader/compare/v3.2.4...v3.2.5
[3.2.4]: https://github.com/redtidev1918/deviantart-downloader/compare/v3.2.3...v3.2.4
[3.2.3]: https://github.com/redtidev1918/deviantart-downloader/compare/v3.2.2...v3.2.3
[3.2.2]: https://github.com/redtidev1918/deviantart-downloader/compare/v3.2.1...v3.2.2
[3.2.1]: https://github.com/redtidev1918/deviantart-downloader/compare/v3.2.0...v3.2.1
[3.2.0]: https://github.com/redtidev1918/deviantart-downloader/compare/v3.1.6...v3.2.0
[3.1.6]: https://github.com/redtidev1918/deviantart-downloader/compare/v3.1.5...v3.1.6
[3.1.5]: https://github.com/redtidev1918/deviantart-downloader/tag/v3.1.5
