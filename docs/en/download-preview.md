## Requirements

- Python 3.10 or newer

## Install (PyPI)

```bash
python -m pip install -U devart-dl
```

Verify the install:

```bash
devart-dl --help
```

PyPI project page: <https://pypi.org/project/devart-dl/>

## First run

Signing in is required before downloading. The simplest way is one-shot browser login (needs a local Chrome and Node.js 22 or newer):

```bash
devart-dl login browser
```

For the full walkthrough (OAuth, cookies and troubleshooting), see the [login and authentication guide](/en/LOGIN.md).

## Offline install and past versions

Advanced users can grab the `.whl` or source distribution from [GitHub Releases](https://github.com/redtidev1918/deviantart-downloader/releases) for offline installs:

```bash
python -m pip install ./devart_dl-<version>-py3-none-any.whl
```

## Changelog

See [CHANGELOG](https://github.com/redtidev1918/deviantart-downloader/blob/main/CHANGELOG.md).
