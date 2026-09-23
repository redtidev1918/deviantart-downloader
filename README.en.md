# DeviantArt Downloader

**Language / 语言:** [中文](README.md) · English

> **A reliable, focused DeviantArt downloader and archival CLI.**

📖 [Full documentation](https://redtidev1918.github.io/deviantart-downloader/) · [Changelog](CHANGELOG.md)

[![CI](https://github.com/redtidev1918/deviantart-downloader/actions/workflows/ci.yml/badge.svg)](https://github.com/redtidev1918/deviantart-downloader/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/devart-dl.svg)](https://pypi.org/project/devart-dl/)
[![Python](https://img.shields.io/pypi/pyversions/devart-dl.svg)](https://pypi.org/project/devart-dl/)
[![Downloads](https://img.shields.io/pypi/dm/devart-dl.svg)](https://pypi.org/project/devart-dl/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

See [CHANGELOG.md](CHANGELOG.md) for release notes.

---

## Core Features

- **Official API first (OAuth)** — log in once to download originals; no cookie export, no anti-ban delays.
- **URL-first** — `devart-dl URL` downloads artworks / galleries / favourites / tags / fav.me links directly.
- **Literature support** — extracts inline literature/journal bodies and saves them as UTF-8 `.txt`, with media and text handled by the same pipeline.
- **Reliable downloads** — HTTP Range resume, automatic retry, 429 backoff, HTML/empty-file validation, atomic finalize.
- **Download archive** — `--archive` remembers what you've downloaded in SQLite, skipping it across sessions.
- **Path templates** — `--directory` / `--filename` support `{id}` `{title}` `{author}` `{published}` `{ext}` and more, with safe sanitization.
- **Metadata sidecars** — `--write-info-json` writes a `.json` next to each file.
- **Proxy & fallback** — `--proxy` or proxy environment variables; falls back to cookies when not logged in via OAuth.
- **Paid / subscription-lock detection** — official API `premium_folder_data` / `tier_access`, or a blurred (`blur_`) non-mature main on the web path, is recognised as subscription/purchase-gated: the web path skips it and the official path fails with a clear message instead of saving a censored placeholder.

---

## Quick Start

### Installation

Requires Python 3.10 or newer.

```bash
pip install devart-dl
```

### Basic Usage (URL-first)

```bash
# Single artwork (also fav.me links and bare artwork ids)
devart-dl https://www.deviantart.com/username/art/title-123456

# Gallery / all works by an artist
devart-dl https://www.deviantart.com/username/gallery

# Favourites
devart-dl https://www.deviantart.com/username/favourites

# Tag
devart-dl https://www.deviantart.com/tag/landscape

# Resolve to JSON descriptors (download nothing)
devart-dl resolve https://www.deviantart.com/username/art/title-123456
```

### Login (OAuth recommended)

```bash
devart-dl login oauth --client-id YOUR_PUBLIC_CLIENT_ID
devart-dl whoami     # verify login
devart-dl logout     # revoke the token
```

Register a **Public** OAuth app at [deviantart.com/developers](https://www.deviantart.com/developers/) and whitelist `http://127.0.0.1:8765/callback`. Login happens in the browser — no password or `client_secret` is ever given to the CLI.

---

## Documentation

The full install, sign-in, download modes, configuration, command reference, Python API and FAQ live on the [docs site](https://redtidev1918.github.io/deviantart-downloader/).

## Acknowledgements

- [requests](https://github.com/psf/requests) — the HTTP client.
- DevTools-free login and archive layout were cross-checked against [gallery-dl](https://github.com/mikf/gallery-dl).

## License

MIT License — see [LICENSE](LICENSE).

**Important disclaimer:** this tool is for personal learning and research only.
Respect DeviantArt's terms of service and copyright. Do not use it commercially
or to overload their servers. The author is not responsible for any misuse.
