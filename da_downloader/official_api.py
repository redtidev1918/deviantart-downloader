"""Official DeviantArt API client (OAuth bearer) plus numeric-ID→UUID resolution.

The official API rejects numeric deviation IDs, so ``resolve_uuid`` converts a
numeric id (from a web URL) to a UUID through the website's public
``_puppy/dadeviation/init`` endpoint — the only scraping this module does,
matching DAKit. Original files come from ``deviation/download/{uuid}`` and are
never reconstructed from preview URLs.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any, Optional

import requests

from .errors import (
    AuthenticationError,
    DeviantArtError,
    MediaUnavailableError,
    NetworkError,
    ParseError,
)
from .oauth import OAuthSession

logger = logging.getLogger(__name__)

API_BASE = "https://www.deviantart.com/api/v1/oauth2/"
WEB_BASE = "https://www.deviantart.com"
USER_AGENT = (
    "devart-dl/3.3 (DeviantArt downloader; "
    "+https://github.com/redtidev1918/deviantart-downloader)"
)
MINOR_VERSION = "20240701"

_UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class OriginalDownload:
    """Metadata for an original file served by ``deviation/download/{uuid}``."""

    url: str
    filename: str
    filesize: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None


class OfficialApiClient:
    """Thin bearer-authenticated transport over the official API."""

    def __init__(self, session: OAuthSession, timeout: float = 30.0) -> None:
        self._session = session
        self._timeout = timeout
        self._http = requests.Session()

    def _request(self, path: str, params: Optional[dict] = None) -> dict:
        params = {**(params or {}), "mature_content": True}
        url = f"{API_BASE}{path}"
        refreshed = False
        while True:
            headers = {
                "Authorization": self._session.authorization_header(force=refreshed),
                "User-Agent": USER_AGENT,
                "dA-minor-version": MINOR_VERSION,
            }
            try:
                response = self._http.get(url, params=params, headers=headers, timeout=self._timeout)
            except requests.RequestException as error:
                raise NetworkError(f"could not reach the DeviantArt API: {error}") from error

            if response.status_code == 401 and not refreshed:
                refreshed = True
                continue
            if response.status_code in (401, 403):
                raise AuthenticationError(
                    f"authentication failed for {path} (HTTP {response.status_code})"
                )
            if response.status_code == 404:
                raise MediaUnavailableError(f"not found: {path}")
            if response.status_code >= 400:
                raise DeviantArtError(f"API returned HTTP {response.status_code} for {path}")

            try:
                data = response.json()
            except ValueError as error:
                raise ParseError("the API returned a non-JSON response") from error
            if not isinstance(data, dict):
                raise ParseError("the API returned an unexpected response")
            return data

    def whoami(self) -> dict:
        return self._request("user/whoami")

    def deviation(self, uuid: str) -> dict:
        return self._request(f"deviation/{uuid}")

    def original_download(self, uuid: str) -> OriginalDownload:
        data = self._request(f"deviation/download/{uuid}")
        src = data.get("src")
        filename = data.get("filename")
        if not src or not filename:
            raise ParseError("the download endpoint returned no source URL and filename")
        return OriginalDownload(
            url=src,
            filename=filename,
            filesize=_as_int(data.get("filesize")),
            width=_as_int(data.get("width")),
            height=_as_int(data.get("height")),
        )

    def gallery_all(self, username: str, offset: int = 0, limit: int = 24) -> dict:
        return self._request(
            "gallery/all",
            {"username": username, "offset": offset, "limit": min(limit, 24)},
        )

    def gallery_folders(self, username: str, offset: int = 0, limit: int = 24) -> dict:
        return self._request(
            "gallery/folders",
            {"username": username, "offset": offset, "limit": min(limit, 24)},
        )

    def gallery(self, username: str, folder_id: str, offset: int = 0, limit: int = 24) -> dict:
        return self._request(
            f"gallery/{folder_id}",
            {"username": username, "offset": offset, "limit": min(limit, 24)},
        )

    def collections_all(self, username: str, offset: int = 0, limit: int = 24) -> dict:
        return self._request(
            "collections/all",
            {"username": username, "offset": offset, "limit": min(limit, 24)},
        )

    def collections_folders(self, username: str, offset: int = 0, limit: int = 24) -> dict:
        return self._request(
            "collections/folders",
            {"username": username, "offset": offset, "limit": min(limit, 24)},
        )

    def collections(self, username: str, folder_id: str, offset: int = 0, limit: int = 24) -> dict:
        return self._request(
            f"collections/{folder_id}",
            {"username": username, "offset": offset, "limit": min(limit, 24)},
        )

    def browse_tags(self, tag: str, offset: int = 0, limit: int = 24) -> dict:
        return self._request(
            "browse/tags", {"tag": tag, "offset": offset, "limit": min(limit, 24)}
        )


def _as_int(value: Any) -> Optional[int]:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _resolve_short_id(code: str, http: requests.Session, timeout: float) -> str:
    """Follow a fav.me short link to its numeric artwork id."""
    try:
        response = http.get(
            f"https://fav.me/{code}",
            allow_redirects=True,
            timeout=timeout,
            stream=True,
        )
    except requests.RequestException as error:
        raise NetworkError(f"could not reach fav.me: {error}") from error
    final_url = response.url
    response.close()
    numeric_id = _extract_numeric_id(final_url)
    if numeric_id is None:
        raise MediaUnavailableError(f"could not resolve fav.me/{code} to an artwork id")
    return numeric_id


def _extract_numeric_id(url: str) -> Optional[str]:
    leaf = url.split("?")[0].rstrip("/").rsplit("/", 1)[-1]
    if leaf.isdigit():
        return leaf
    match = re.search(r"-(\d+)$", leaf)
    return match.group(1) if match else None


def resolve_uuid(
    identifier: str,
    username: Optional[str] = None,
    timeout: int = 30,
    session: Optional[requests.Session] = None,
) -> str:
    """Resolve a numeric deviation id to its UUID; UUIDs pass through unchanged."""
    identifier = identifier.strip()
    if not identifier:
        raise ParseError("the URL does not contain an artwork id")
    if _UUID_RE.match(identifier):
        return identifier

    http = session or requests.Session()
    if not identifier.isdigit():
        # A fav.me (or similar short) code: follow the redirect to the numeric id.
        identifier = _resolve_short_id(identifier, http, timeout)
    try:
        home = http.get(
            WEB_BASE,
            headers={"User-Agent": USER_AGENT, "Accept": "text/html"},
            timeout=timeout,
        )
        home.raise_for_status()
        match = re.search(r"window\.__CSRF_TOKEN__ = '([^']*)'", home.text)
        if not match or not match.group(1):
            raise ParseError("could not read the DeviantArt CSRF token")
        csrf = match.group(1)

        query = {
            "deviationid": identifier,
            # 该接口自 2026 年起把 type 列为必填枚举（art/journal），缺失返回 400。
            "type": "art",
            "include_session": "false",
            "csrf_token": csrf,
            "mature_content": True,
        }
        if username:
            query["username"] = username
        response = http.get(
            f"{WEB_BASE}/_puppy/dadeviation/init",
            params=query,
            headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
            timeout=timeout,
        )
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as error:
        raise NetworkError(f"could not reach the resolution endpoint: {error}") from error
    except ValueError as error:
        raise ParseError("the resolution endpoint returned invalid JSON") from error

    deviation = data.get("deviation") if isinstance(data, dict) else None
    extended = deviation.get("extended") if isinstance(deviation, dict) else None
    uuid = extended.get("deviationUuid") if isinstance(extended, dict) else None
    if not isinstance(uuid, str) or not uuid:
        raise MediaUnavailableError(f"could not resolve artwork {identifier} to a UUID")
    return uuid



def deviation_init(
    identifier: str,
    username: Optional[str] = None,
    timeout: int = 30,
    session: Optional[requests.Session] = None,
) -> dict:
    """Fetch the full public ``_puppy/dadeviation/init`` payload (numeric or
    fav.me ids). Mirrors DAKit/DAViewer: multimedia pages surface under
    ``deviation.extended.additionalMedia`` here, which the official API no
    longer returns.
    """
    identifier = identifier.strip()
    if not identifier:
        raise ParseError("the URL does not contain an artwork id")
    http = session or requests.Session()
    if not identifier.isdigit():
        identifier = _resolve_short_id(identifier, http, timeout)
    try:
        home = http.get(
            WEB_BASE,
            headers={"User-Agent": USER_AGENT, "Accept": "text/html"},
            timeout=timeout,
        )
        home.raise_for_status()
        match = re.search(r"window\.__CSRF_TOKEN__ = '([^']*)'", home.text)
        if not match or not match.group(1):
            raise ParseError("could not read the DeviantArt CSRF token")
        csrf = match.group(1)
        query = {
            "deviationid": identifier,
            # 该接口自 2026 年起把 type 列为必填枚举（art/journal），缺失返回 400。
            "type": "art",
            "include_session": "false",
            "csrf_token": csrf,
            "mature_content": True,
        }
        if username:
            query["username"] = username
        response = http.get(
            f"{WEB_BASE}/_puppy/dadeviation/init",
            params=query,
            headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
            timeout=timeout,
        )
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as error:
        raise NetworkError(f"could not reach the resolution endpoint: {error}") from error
    except ValueError as error:
        raise ParseError("the resolution endpoint returned invalid JSON") from error
    if not isinstance(data, dict) or not isinstance(data.get("deviation"), dict):
        raise ParseError("the resolution endpoint returned an unexpected payload")
    return data


def deviation_uuid(init_data: dict) -> str:
    """Read the UUID out of an init payload."""
    extended = init_data.get("deviation", {}).get("extended") or {}
    uuid = extended.get("deviationUuid")
    if not isinstance(uuid, str) or not uuid:
        raise MediaUnavailableError("could not resolve the artwork to a UUID")
    return uuid


def additional_media_urls(init_data: dict) -> list:
    """Original-file URLs of a multimedia deviation's extra pages
    (``deviation.extended.additionalMedia``, each entry nests its Wix
    descriptor under ``media``). Prefers the raw ``baseUri`` file + token.
    """
    extended = init_data.get("deviation", {}).get("extended") or {}
    entries = extended.get("additionalMedia") or []
    urls: list = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        media = entry.get("media")
        if not isinstance(media, dict):
            continue
        base = media.get("baseUri")
        if not isinstance(base, str) or not base:
            continue
        raw_token = media.get("token")
        token = raw_token[0] if isinstance(raw_token, list) and raw_token else raw_token
        if token:
            urls.append(f"{base}{'&' if '?' in base else '?'}token={token}")
        else:
            urls.append(base)
    return urls


__all__ = ["OfficialApiClient", "OriginalDownload", "resolve_uuid", "deviation_init", "deviation_uuid", "additional_media_urls"]
