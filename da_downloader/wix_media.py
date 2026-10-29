"""Bounded Wix URL selection, shared with DeviantDrop's verified 2026-10-29 fix.

See tests/fixtures/deviantart-bounded-media-evidence.md. Like DAViewer/DAKit,
keep display representations distinct from uploaded originals. Token payloads
are selection hints only, never proof of authentication or permission.
"""

import base64
import json
import re
from urllib.parse import parse_qsl, urlsplit


def append_media_token(url: str, token: str) -> str:
    if not token or any(key == "token" for key, _ in parse_qsl(urlsplit(url).query, keep_blank_values=True)):
        return url
    return f"{url}{'&' if '?' in url else '?'}token={token}"


def bounded_fullview_url(media: dict) -> str | None:
    """Return the supplied fullview only for a bounded static-image signature."""
    try:
        base = media.get("baseUri", "")
        path = urlsplit(base).path
        if not re.search(r"\.(?:png|jpe?g|webp|avif)$", path, re.I):
            return None
        tokens = media.get("token")
        token = tokens[0] if isinstance(tokens, list) else tokens
        payload = token.split(".")[1]
        claims = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
        groups = claims.get("obj")
        if not isinstance(groups, list) or not any(
            isinstance(group, list) and any(
                isinstance(rule, dict) and rule.get("path") == path and any(
                    isinstance(rule.get(key), str) and re.fullmatch(r"<=\d+", rule[key])
                    for key in ("width", "height")
                ) for rule in group
            ) for group in groups
        ):
            return None
        types = media.get("types") or []
        # Video sources take precedence over static posters.
        if any(isinstance(t, dict) and t.get("t") == "video" and t.get("b") for t in types):
            return None
        full = next((t for t in types if isinstance(t, dict) and t.get("t") == "fullview"), {})
        if full.get("r") not in (None, 0):
            return None  # Only index 0 was independently verified.
        url = full.get("b")
        if not url and full.get("c"):
            url = base + full["c"].replace("<prettyName>", media.get("prettyName") or "image")
        if not url:
            return None
        return append_media_token(url, token)
    except (ValueError, TypeError, AttributeError, IndexError, KeyError):
        return None
