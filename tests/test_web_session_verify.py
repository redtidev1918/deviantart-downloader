"""Web session verification tests (tri-state verdict).

Fixture origin (per AGENTS.md external protocol verification rule): the
``__INITIAL_STATE__`` samples are ported from DAViewer
``test/web_session_verifier_test.dart``, whose evidence was verified against
the production DeviantArt home page during the DAViewer web-session recovery
work (see DAViewer ``lib/core/auth/web_session_verifier.dart`` docstring,
2026-10). They are real-world evidence, not reverse-engineered from this
implementation.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest
import requests

from da_downloader.auth import (
    AuthManager,
    WebSessionState,
    diagnose_authentication_failure,
)

# --- page_username_from_initial_state (ported production evidence) ---


def test_parse_accepts_javascript_escapes() -> None:
    html = r"""<script>window.__INITIAL_STATE__ = JSON.parse("{\"@@publicSession\":{\"isLoggedIn\":true,\"user\":{\"username\":\"artist\"}},\"title\":\"artist\'s work\"}");</script>"""
    assert AuthManager.page_username_from_initial_state(html) == "artist"


def test_single_quoted_initializer_keeps_anonymous_distinct_from_missing() -> None:
    html = (
        """<script>window.__INITIAL_STATE__ = JSON.parse('"""
        """{"@@publicSession":{"isLoggedIn":false,"user":{"username":"anonymous"}}}"""
        """');</script>"""
    )
    assert AuthManager.page_username_from_initial_state(html) == "anonymous"
    assert AuthManager.page_username_from_initial_state("<html/>") is None


def test_legacy_single_at_spelling_still_parses() -> None:
    html = r"""<script>window.__INITIAL_STATE__ = JSON.parse("{\"@publicSession\":{\"user\":{\"username\":\"artist\"}}}");</script>"""
    assert AuthManager.page_username_from_initial_state(html) == "artist"


def test_is_logged_in_false_without_username_is_a_signed_out_statement() -> None:
    html = r"""<script>window.__INITIAL_STATE__ = JSON.parse("{\"@@publicSession\":{\"isLoggedIn\":false}}");</script>"""
    assert AuthManager.page_username_from_initial_state(html) == "anonymous"


def test_is_logged_in_true_without_username_stays_unverified() -> None:
    html = r"""<script>window.__INITIAL_STATE__ = JSON.parse("{\"@@publicSession\":{\"isLoggedIn\":true}}");</script>"""
    assert AuthManager.page_username_from_initial_state(html) is None


@pytest.mark.parametrize(
    "fixture",
    [
        'window.__INITIAL_STATE__ = JSON.parse("broken");',
        'window.__INITIAL_STATE__ = JSON.parse("{}");',
        'window.__INITIAL_STATE__ = JSON.parse("{\\"@@publicSession\\":{}}");',
    ],
)
def test_incomplete_or_malformed_state_is_none(fixture: str) -> None:
    assert AuthManager.page_username_from_initial_state(fixture) is None


# --- verify_web_session (tri-state over a mocked home page) ---


class _FakeResponse:
    def __init__(self, status_code: int, text: str) -> None:
        self.status_code = status_code
        self.text = text


def _verify(html: str = "", status: int = 200, exc: Exception | None = None):
    manager = AuthManager()

    def fake_get(url, **kwargs):
        assert url == "https://www.deviantart.com/"
        assert kwargs["headers"]["User-Agent"].startswith("Mozilla/5.0")
        assert kwargs["headers"]["Cookie"] == "auth=x"
        if exc is not None:
            raise exc
        return _FakeResponse(status, html)

    with patch("da_downloader.auth.requests.get", side_effect=fake_get):
        return manager, manager.verify_web_session(cookies="auth=x")


_SIGNED_IN_HTML = (
    r"<script>window.__INITIAL_STATE__ = JSON.parse("
    r'"{\"@@publicSession\":{\"isLoggedIn\":true,\"user\":{\"username\":\"alice\"}}}");</script>'
)
_ANONYMOUS_HTML = (
    r"<script>window.__INITIAL_STATE__ = JSON.parse("
    r'"{\"@@publicSession\":{\"isLoggedIn\":false}}");</script>'
)


def test_verify_signed_in_with_username() -> None:
    manager, verdict = _verify(_SIGNED_IN_HTML)
    assert verdict.state == WebSessionState.SIGNED_IN
    assert verdict.username == "alice"
    assert manager.is_logged_in is True


def test_verify_anonymous_is_a_server_statement() -> None:
    manager, verdict = _verify(_ANONYMOUS_HTML)
    assert verdict.state == WebSessionState.ANONYMOUS
    assert manager.is_logged_in is False


def test_verify_network_failure_is_unavailable_not_anonymous() -> None:
    manager, verdict = _verify(exc=requests.ConnectionError("boom"))
    assert verdict.state == WebSessionState.UNAVAILABLE
    assert manager.is_logged_in is False


@pytest.mark.parametrize("status", [202, 403, 500])
def test_verify_non_200_is_unavailable(status: int) -> None:
    _, verdict = _verify("challenge", status=status)
    assert verdict.state == WebSessionState.UNAVAILABLE


def test_verify_missing_marker_is_unavailable() -> None:
    _, verdict = _verify("<html>waf challenge</html>")
    assert verdict.state == WebSessionState.UNAVAILABLE


# --- diagnose_authentication_failure (401/403 hint text) ---


def test_diagnose_without_cookies_suggests_login() -> None:
    hint = diagnose_authentication_failure("")
    assert hint is not None
    assert "login browser" in hint


def test_diagnose_expired_session(monkeypatch) -> None:
    monkeypatch.setattr(
        AuthManager,
        "verify_web_session",
        lambda self, cookies, proxies, timeout: type(
            "V", (), {"state": WebSessionState.ANONYMOUS, "username": ""}
        )(),
    )
    hint = diagnose_authentication_failure("auth=old")
    assert hint is not None
    assert "expired" in hint


def test_diagnose_unavailable_session(monkeypatch) -> None:
    monkeypatch.setattr(
        AuthManager,
        "verify_web_session",
        lambda self, cookies, proxies, timeout: type(
            "V", (), {"state": WebSessionState.UNAVAILABLE, "username": ""}
        )(),
    )
    hint = diagnose_authentication_failure("auth=old")
    assert hint is not None
    assert "could not confirm" in hint


def test_diagnose_valid_session_points_at_the_item(monkeypatch) -> None:
    monkeypatch.setattr(
        AuthManager,
        "verify_web_session",
        lambda self, cookies, proxies, timeout: type(
            "V", (), {"state": WebSessionState.SIGNED_IN, "username": "alice"}
        )(),
    )
    hint = diagnose_authentication_failure("auth=ok")
    assert hint is not None
    assert "signed in as alice" in hint
    assert "denied" in hint


# --- CLI integration: AuthenticationError prints the diagnosis ---


def test_run_download_authentication_error_prints_hint(monkeypatch, capsys, tmp_path) -> None:
    from da_downloader.errors import AuthenticationError

    def boom(**kwargs):
        raise AuthenticationError("HTTP 403 forbidden: https://example/x")

    monkeypatch.setattr(cli_module(), "build_downloader", boom)
    monkeypatch.setattr(cli_module(), "_load_cookies", lambda p: "auth=x")
    hints: list = []
    monkeypatch.setattr(
        cli_module(),
        "diagnose_authentication_failure",
        lambda *a, **kw: hints.append((a, kw)) or "hint: session expired",
    )

    rc = cli_module()._run_download(
        ["https://www.deviantart.com/alice/gallery", "--dest", str(tmp_path)]
    )

    assert rc == 1
    err = capsys.readouterr().err
    assert "error: HTTP 403 forbidden" in err
    assert "hint: session expired" in err
    assert hints and hints[0][0][0] == "auth=x"


def cli_module():
    from da_downloader import cli

    return cli
