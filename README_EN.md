# DeviantArt Downloader

A reliable, focused DeviantArt downloader and archival CLI.

[中文文档](README.md) | **English Documentation**

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
- **Reliable downloads** — HTTP Range resume, automatic retry, 429 backoff, HTML/empty-file validation, atomic finalize.
- **Download archive** — `--archive` remembers what you've downloaded in SQLite, skipping it across sessions.
- **Path templates** — `--directory` / `--filename` support `{id}` `{title}` `{author}` `{published}` `{ext}` and more, with safe sanitization.
- **Metadata sidecars** — `--write-info-json` writes a `.json` next to each file.
- **Proxy & fallback** — `--proxy` or proxy environment variables; falls back to cookies when not logged in via OAuth.

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
```

### Login (OAuth recommended)

```bash
devart-dl login oauth --client-id YOUR_PUBLIC_CLIENT_ID
devart-dl whoami     # verify login
devart-dl logout     # revoke the token
```

Register a **Public** OAuth app at [deviantart.com/developers](https://www.deviantart.com/developers/) and whitelist `http://127.0.0.1:8765/callback`. Login happens in the browser — no password or `client_secret` is ever given to the CLI.

---

## Main Features

### Download Modes

URL-first is the simplest entry; explicit subcommands are also kept:

```bash
# URL-first
devart-dl https://www.deviantart.com/username/art/title-123456
devart-dl https://www.deviantart.com/username/gallery
devart-dl https://www.deviantart.com/username/gallery/12345   # specific folder
devart-dl https://www.deviantart.com/username/favourites
devart-dl https://www.deviantart.com/tag/landscape

# Explicit subcommands
devart-dl url https://www.deviantart.com/username/art/title-123456
devart-dl artist username
devart-dl gallery username [gallery_id]
devart-dl search all "digital art"
devart-dl fav username folder_id
```

> Note: explicit subcommands keep the old usage for compatibility. The official API has no search endpoint, so `search` uses the cookie fallback.

### Authentication

**Official API (OAuth) first**, cookies as the fallback.

1. **OAuth login (recommended)**

   ```bash
   devart-dl login oauth --client-id YOUR_PUBLIC_CLIENT_ID
   ```

   - Register a **Public** OAuth app and whitelist `http://127.0.0.1:8765/callback` exactly.
   - Login completes in the browser; tokens are stored at `~/.deviantart_dl/oauth.json` (0600) and auto-refresh.
   - Download commands then use the official API automatically; originals come from the official download endpoint.

2. **Cookie login — one-click browser (recommended for cookies)**

   ```bash
   devart-dl login browser
   ```

   A Chrome window opens to the DeviantArt login page; just log in there. The
   helper drives your **real** Chrome via the DevTools Protocol and captures the
   web cookies (`auth` / `auth_secure` / `userinfo`) automatically — no F12 copy.
   It needs Node.js (>= 22) and Chrome, and saves the session to
   `~/.deviantart_dl/session.json` (0600). Logging in on the real domain is
   required because the DeviantArt login page is behind an AWS WAF bot check that
   blocks headless/proxied browsers; this is also the only way to capture the
   HttpOnly `auth_secure` cookie.

3. **Cookie login — manual paste (fallback)**

   ```bash
   devart-dl login interactive   # paste a cookie interactively
   ```

   Or create a `cookies.txt`, or set the `DEVIANTART_COOKIES` environment variable. The session is saved at `~/.deviantart_dl/session.json`.

### Download Archive & Resume

```bash
# SQLite archive: skip already-downloaded items across sessions and directories
devart-dl https://www.deviantart.com/username/gallery --archive ~/.devart-dl/archive.sqlite

# Interrupted downloads resume from the .part file — no full re-download
```

### Filename / Directory Templates

```bash
devart-dl URL \
  --directory "{author}/{published:%Y-%m}" \
  --filename "{id}_{title}.{ext}"
```

Fields: `{id}` `{title}` `{author}` `{username}` `{published}` `{filename}` `{ext}` `{index}`. Paths are sanitized (illegal characters, Windows reserved names, `..` traversal, overly long names) so results always stay inside the download root.

### Metadata Sidecar

```bash
devart-dl URL --write-info-json
# produces artwork.jpg plus artwork.json (title, author, URL, published, mature, media URL, …)
```

---

## Configuration Options

### Common Options

| Option | Description | Default |
|--------|-------------|---------|
| `-d, --dest` | Download root directory | `./Downloads` |
| `--directory` | Directory template (e.g. `{author}/{published:%Y}`) | `{author}` |
| `--filename` | Filename template (e.g. `{id}_{title}.{ext}`) | `{id}_{title}.{ext}` |
| `--quality` | `original` (login) / `best` (default) / `preview`; legacy `o/f/p` still accepted | `best` |
| `--archive` | SQLite download archive path | none |
| `--write-info-json` | Write a metadata sidecar | off |
| `--overwrite` | Replace existing files | off (skip) |
| `--cookies` | Cookie file path | auto-load session |
| `--proxy` | Proxy URL | auto from environment |
| `--timeout` | Request timeout (seconds) | `60` |
| `--retries` | Max retries | `3` |
| `--limit` | Items per page | `24` |

### Output Options

- `-v, --verbose`: show details (including skip reasons).
- `-q, --quiet`: only the summary and errors.

---

## Command Reference

```bash
# URL-first (recommended)
devart-dl <URL>

# Explicit subcommands
devart-dl url <artwork_url>
devart-dl artist <username>
devart-dl gallery <username> [gallery_id]
devart-dl search <username|all> <query>
devart-dl fav <username> <folder_id>

# Login / session
devart-dl login oauth --client-id <ID>   # OAuth login (recommended)
devart-dl login browser                 # one-click cookie via your Chrome
devart-dl login interactive             # cookie login (manual paste)
devart-dl whoami                        # show login status
devart-dl logout                        # revoke token and clear local session

# Other
devart-dl version
```

---

## Advanced Usage

### Proxy

```bash
# Command-line
devart-dl URL --proxy http://127.0.0.1:7890

# Environment variables (HTTP/HTTPS)
export HTTP_PROXY=http://127.0.0.1:7890
export HTTPS_PROXY=http://127.0.0.1:7890
export ALL_PROXY=http://127.0.0.1:7890
```

### Python API

```python
from pathlib import Path
from da_downloader import Downloader
from da_downloader.download import build_downloader

downloader = build_downloader(
    destination=Path('downloads'),
    archive=Path('archive.sqlite'),   # optional: skip already-downloaded
    quality='best',                   # original / best / preview
    write_info_json=True,             # write a metadata .json next to each file
)

results = downloader.download('https://www.deviantart.com/username/gallery')
for r in results:
    print(r.status, r.path)
```

When logged in via `devart-dl login oauth`, the official API is used automatically; otherwise it falls back to cookies.

---

## FAQ

**Q: Downloads are incomplete / skip some artworks?**
**A:** Upgrade to **v3.4.0+**. Older versions fetched only the Featured folder;
v3.3.1 walks all gallery folders, and v3.4.0 reports parsing/network failures
loudly and resumes interrupted downloads via Range.

**Q: ModuleNotFoundError after pip install?**
**A:** Upgrade to **v3.4.0+** (`pip install -U devart-dl`); the console entry point is fixed.

**Q: Got a 403 Forbidden error?**
**A:** Usually not logged in or an expired cookie. Prefer `devart-dl login oauth`
(official API); otherwise `devart-dl login browser` for a one-click cookie
(`devart-dl login interactive` to paste one manually).

**Q: Got a 429 Too Many Requests?**
**A:** The official API (OAuth) usually avoids this; the cookie path retries with
backoff. If it persists, pause for a while.

**Q: Downloads are slow?**
**A:** Use a proxy (`--proxy`), or lower the quality (`--quality preview`).

**Q: How do I export a cookie?**
**A:** Easiest is `devart-dl login browser` — it opens your own Chrome and
captures the cookie automatically. Otherwise open Chrome/Edge DevTools (F12) →
Application → Cookies, copy the `auth` and `auth_secure` fields, and paste them
via `devart-dl login interactive`.

---

## License

MIT License — see [LICENSE](LICENSE).

**Important disclaimer:** this tool is for personal learning and research only.
Respect DeviantArt's terms of service and copyright. Do not use it commercially
or to overload their servers. The author is not responsible for any misuse.
