# DeviantArt Downloader Documentation

**Language / 语言:** [中文](/) · English

> A reliable, focused DeviantArt downloader and archival CLI. Installed from PyPI as
> `devart-dl`.

## Start here

| Document | Content |
| :-- | :-- |
| [Download](download.md) | PyPI install and release artifacts, auto-updated on every release |
| [README (English)](https://github.com/redtidev1918/deviantart-downloader/blob/main/README.en.md) | Overview, install and usage |
| [Login and authentication](LOGIN.md) | OAuth and cookie sign-in flows, mature-content handling, security notes |

## Media download 403

Media CDN 403 does not by itself mean the login expired. A dimension-bounded
Wix signature may authorize the supplied fullview transform but reject the bare
baseUri. The downloader selects that fullview with an explicit warning that it
is a DA display version, not the uploaded original. It does not alter quality
parameters, re-encode bytes, or silently substitute a small preview. Original
download endpoints retain priority; GIF and video selection is unchanged.
Sidecars record `representation: fullview` and `original_available: false`;
resolve JSON includes `representation: fullview`. Both web main images and extra
pages share `da_downloader/wix_media.py`, covered by the real-response fixtures
documented in `tests/fixtures/deviantart-bounded-media-evidence.md`.

## Links

- PyPI: <https://pypi.org/project/devart-dl/>
- Repository: <https://github.com/redtidev1918/deviantart-downloader>
- Releases: <https://github.com/redtidev1918/deviantart-downloader/releases>
- Changelog: <https://github.com/redtidev1918/deviantart-downloader/blob/main/CHANGELOG.md>
