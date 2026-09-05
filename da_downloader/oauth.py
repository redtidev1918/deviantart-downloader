"""OAuth 2.0 Authorization Code + PKCE client for DeviantArt.

Mirrors DAKit's design: a *public* client (no ``client_secret``) logs in through
the system browser and receives the callback on a local loopback server. Tokens
are stored with 0600 permissions and never written to logs or the console.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import secrets
import webbrowser
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Optional, cast
from urllib.parse import parse_qs, urlencode, urlsplit

import requests

AUTHORIZE_URL = "https://www.deviantart.com/oauth2/authorize"
TOKEN_URL = "https://www.deviantart.com/oauth2/token"
REVOKE_URL = "https://www.deviantart.com/oauth2/revoke"
DEFAULT_REDIRECT_URI = "http://127.0.0.1:8765/callback"
DEFAULT_SCOPES = ("basic", "browse")

_PKCE_ALPHABET = (
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~"
)


class OAuthError(RuntimeError):
    """An OAuth flow or token-endpoint error."""


class InvalidRefreshToken(OAuthError):
    """The refresh token was rejected; the stored session must be cleared."""


@dataclass(frozen=True)
class OAuthConfig:
    """OAuth client configuration for a public (PKCE) DeviantArt app."""

    client_id: str
    redirect_uri: str = DEFAULT_REDIRECT_URI
    scopes: tuple[str, ...] = DEFAULT_SCOPES
    authorize_url: str = AUTHORIZE_URL
    token_url: str = TOKEN_URL
    revoke_url: str = REVOKE_URL

    def __post_init__(self) -> None:
        if not self.client_id.strip():
            raise ValueError("OAuth client_id must not be empty")
        if not urlsplit(self.redirect_uri).scheme:
            raise ValueError("OAuth redirect_uri must include a scheme")


@dataclass
class OAuthTokens:
    """A bearer token set returned by the token endpoint."""

    access_token: str
    token_type: str
    expires_at: datetime
    refresh_token: Optional[str] = None
    scopes: tuple[str, ...] = ()

    def is_expired(self, leeway: timedelta = timedelta(minutes=1)) -> bool:
        return self.expires_at <= datetime.now(timezone.utc) + leeway

    def to_dict(self) -> dict:
        return {
            "access_token": self.access_token,
            "token_type": self.token_type,
            "expires_at": self.expires_at.isoformat(),
            "refresh_token": self.refresh_token,
            "scopes": list(self.scopes),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "OAuthTokens":
        raw_expires = data.get("expires_at")
        expires_at = (
            datetime.fromisoformat(raw_expires)
            if isinstance(raw_expires, str)
            else cast(datetime, raw_expires)
        )
        return cls(
            access_token=str(data["access_token"]),
            token_type=str(data.get("token_type") or "Bearer"),
            expires_at=expires_at,
            refresh_token=data.get("refresh_token"),
            scopes=tuple(data.get("scopes") or ()),
        )


def _random_string(length: int) -> str:
    return "".join(secrets.choice(_PKCE_ALPHABET) for _ in range(length))


def generate_pkce() -> tuple[str, str]:
    """Return a ``(code_verifier, code_challenge)`` pair for the S256 method."""
    verifier = _random_string(64)
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return verifier, challenge


def build_authorize_url(
    config: OAuthConfig, verifier: str, state: str
) -> str:
    """Build the browser URL that starts the authorization flow."""
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    params = {
        "response_type": "code",
        "client_id": config.client_id,
        "redirect_uri": config.redirect_uri,
        "scope": " ".join(config.scopes),
        "state": state,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
    }
    return f"{config.authorize_url}?{urlencode(params)}"


class OAuthTokenClient:
    """Exchanges codes and refreshes/revokes tokens against the OAuth endpoint."""

    def __init__(self, session: Optional[requests.Session] = None) -> None:
        self._session = session or requests.Session()

    def exchange_code(
        self, config: OAuthConfig, code: str, verifier: str
    ) -> OAuthTokens:
        data = self._post_form(
            config.token_url,
            {
                "grant_type": "authorization_code",
                "client_id": config.client_id,
                "redirect_uri": config.redirect_uri,
                "code": code,
                "code_verifier": verifier,
            },
        )
        return _parse_tokens(data)

    def refresh(self, config: OAuthConfig, current: OAuthTokens) -> OAuthTokens:
        if not current.refresh_token:
            raise OAuthError(
                "The session cannot be refreshed and requires re-authorization."
            )
        try:
            data = self._post_form(
                config.token_url,
                {
                    "grant_type": "refresh_token",
                    "client_id": config.client_id,
                    "refresh_token": current.refresh_token,
                },
            )
        except OAuthError as error:
            if _is_invalid_refresh_token(error):
                raise InvalidRefreshToken(str(error)) from error
            raise
        return _parse_tokens(
            data,
            fallback_refresh_token=current.refresh_token,
            fallback_scopes=current.scopes,
        )

    def revoke(self, config: OAuthConfig, current: OAuthTokens) -> None:
        token = current.refresh_token or current.access_token
        self._post_form(
            config.revoke_url,
            {"token": token, "revoke_refresh_only": "true"},
        )

    def _post_form(self, url: str, form: dict) -> dict:
        try:
            response = self._session.post(url, data=form, timeout=30)
        except requests.RequestException as error:
            raise OAuthError(f"Could not reach the OAuth endpoint: {error}") from error
        try:
            data = response.json()
        except ValueError as error:
            raise OAuthError("The OAuth endpoint returned a non-JSON response.") from error
        if response.status_code >= 400 or "error" in data:
            provider = data.get("error", "")
            description = data.get("error_description", "")
            raise OAuthError(
                description
                or provider
                or f"The OAuth endpoint returned HTTP {response.status_code}."
            )
        return cast(dict, data)


def _parse_tokens(
    data: dict,
    fallback_refresh_token: Optional[str] = None,
    fallback_scopes: tuple[str, ...] = (),
) -> OAuthTokens:
    access_token = data.get("access_token")
    token_type = data.get("token_type")
    raw_expires = data.get("expires_in")
    if not access_token or not token_type or raw_expires is None:
        raise OAuthError("The token response is missing required fields.")
    try:
        expires_in = int(raw_expires)
    except (TypeError, ValueError) as error:
        raise OAuthError("The token response has an invalid expiry.") from error
    if expires_in <= 0:
        raise OAuthError("The token response has an invalid expiry.")
    scopes = tuple((data.get("scope") or "").split())
    if not scopes:
        scopes = fallback_scopes
    return OAuthTokens(
        access_token=access_token,
        token_type=token_type,
        expires_at=datetime.now(timezone.utc) + timedelta(seconds=expires_in),
        refresh_token=data.get("refresh_token") or fallback_refresh_token,
        scopes=scopes,
    )


def _is_invalid_refresh_token(error: OAuthError) -> bool:
    # DeviantArt reports an expired/revoked refresh token as `invalid_request`
    # with "The refresh_token is invalid" instead of the RFC-standard
    # `invalid_grant`. Normalize both so hosts can clear unusable credentials.
    message = error.args[0] if error.args else ""
    normalized = message.replace("_", " ").lower()
    return "invalid_grant" in normalized or (
        "refresh" in normalized and "invalid" in normalized
    )


@dataclass
class StoredSession:
    """A persisted OAuth session: the client id plus its tokens."""

    client_id: str
    tokens: OAuthTokens


class OAuthTokenStore:
    """Persists an OAuth session to ``~/.deviantart_dl/oauth.json`` (0600)."""

    def __init__(self, path: Optional[Path] = None) -> None:
        self.path = path or (
            Path.home() / ".deviantart_dl" / "oauth.json"
        )

    def load(self) -> Optional[StoredSession]:
        if not self.path.exists():
            return None
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            client_id = data.get("client_id")
            if not client_id:
                return None
            return StoredSession(client_id=client_id, tokens=OAuthTokens.from_dict(data))
        except (OSError, ValueError, KeyError, TypeError):
            return None

    def write(self, client_id: str, tokens: OAuthTokens) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"client_id": client_id, **tokens.to_dict()}
        self.path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        try:
            os.chmod(self.path, 0o600)
        except OSError:
            pass

    def clear(self) -> None:
        try:
            self.path.unlink(missing_ok=True)
        except OSError:
            pass


class OAuthSession:
    """Supplies a valid access token, transparently refreshing when expired."""

    def __init__(
        self,
        config: OAuthConfig,
        tokens: OAuthTokens,
        token_client: Optional[OAuthTokenClient] = None,
        store: Optional[OAuthTokenStore] = None,
    ) -> None:
        self.config = config
        self.tokens = tokens
        self._token_client = token_client or OAuthTokenClient()
        self._store = store

    @classmethod
    def from_store(
        cls,
        client_id: Optional[str] = None,
        redirect_uri: str = DEFAULT_REDIRECT_URI,
        scopes: tuple[str, ...] = DEFAULT_SCOPES,
        store: Optional[OAuthTokenStore] = None,
    ) -> Optional["OAuthSession"]:
        resolved_store = store or OAuthTokenStore()
        stored = resolved_store.load()
        if stored is None:
            return None
        config = OAuthConfig(
            client_id or stored.client_id, redirect_uri, scopes
        )
        return cls(config, stored.tokens, store=resolved_store)

    def valid_access_token(self, force: bool = False) -> str:
        if force or self.tokens.is_expired():
            self.tokens = self._token_client.refresh(self.config, self.tokens)
            if self._store:
                self._store.write(self.config.client_id, self.tokens)
        return self.tokens.access_token

    def authorization_header(self, force: bool = False) -> str:
        access_token = self.valid_access_token(force=force)
        return f"{self.tokens.token_type} {access_token}"


class _CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802 (stdlib signature)
        query = parse_qs(urlsplit(self.path).query)
        self.server.callback = {  # type: ignore[attr-defined]
            key: values[0] if values else ""
            for key, values in query.items()
        }
        body = (
            b"<html><body><h3>Authorization complete.</h3>"
            b"<p>You may close this tab and return to the terminal.</p></body></html>"
        )
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
        return


def _callback_host_port(redirect_uri: str) -> tuple[str, int]:
    parts = urlsplit(redirect_uri)
    return parts.hostname or "127.0.0.1", parts.port or 8765


def login(
    config: OAuthConfig,
    no_open: bool = False,
    manual: bool = False,
    store: Optional[OAuthTokenStore] = None,
) -> OAuthTokens:
    """Run the interactive PKCE login and persist the resulting tokens."""
    verifier, state = generate_pkce()
    authorize_url = build_authorize_url(config, verifier, state)

    print("Open this URL in your browser to authorize devart-dl:")
    print()
    print(f"  {authorize_url}")
    print()

    if not no_open and not manual:
        webbrowser.open(authorize_url)

    host, port = _callback_host_port(config.redirect_uri)
    server = HTTPServer((host, port), _CallbackHandler)
    server.callback = {}  # type: ignore[attr-defined]
    try:
        print(f"Waiting for the callback on http://{host}:{port}/ ...")
        server.handle_request()
    finally:
        server.server_close()

    callback = getattr(server, "callback", {})
    if callback.get("state") != state:
        raise OAuthError("The OAuth callback state is missing or invalid.")
    provider_error = callback.get("error")
    if provider_error:
        raise OAuthError(
            callback.get("error_description") or f"Authorization rejected: {provider_error}"
        )
    code = callback.get("code")
    if not code:
        raise OAuthError("The OAuth callback did not contain an authorization code.")

    tokens = OAuthTokenClient().exchange_code(config, code, verifier)
    resolved_store = store or OAuthTokenStore()
    resolved_store.write(config.client_id, tokens)
    return tokens
