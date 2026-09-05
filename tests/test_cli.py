"""Tests for CLI URL-first routing."""

from __future__ import annotations

from da_downloader import cli


def test_looks_like_target() -> None:
    assert cli._looks_like_target("https://www.deviantart.com/alice/gallery") is True
    assert cli._looks_like_target("https://fav.me/abc123") is True
    assert cli._looks_like_target("123456") is True
    assert cli._looks_like_target("a0367442-a7cf-4b5e-9b2a-585e6d98ce8d") is True
    assert cli._looks_like_target("gallery") is False
    assert cli._looks_like_target("help") is False
    assert cli._looks_like_target("login") is False


def test_url_first_routes_to_download(monkeypatch) -> None:
    calls: list = []
    monkeypatch.setattr(cli, "_run_download", lambda args: calls.append(list(args)) or 0)
    assert cli.main(["https://www.deviantart.com/alice/gallery"]) == 0
    assert calls == [["https://www.deviantart.com/alice/gallery"]]


def test_known_command_routes_to_subcommand(monkeypatch) -> None:
    calls: list = []
    monkeypatch.setattr(cli, "_run_subcommand", lambda cmd, args: calls.append((cmd, list(args))) or 0)
    assert cli.main(["gallery", "alice"]) == 0
    assert calls == [("gallery", ["alice"])]


def test_cli_version_is_importable(capsys) -> None:
    assert cli.main(["--version"]) == 0
    assert "devart-dl" in capsys.readouterr().out


def test_run_download_summary_and_flags(monkeypatch, capsys, tmp_path) -> None:
    from da_downloader.manager import DownloadOutcome

    class FakeDownloader:
        def download(self, target):
            return [
                DownloadOutcome("1", "downloaded", path=tmp_path / "x.jpg", size=4),
                DownloadOutcome("2", "skipped", reason="archived"),
            ]

    built: dict = {}
    monkeypatch.setattr(cli, "build_downloader", lambda **kw: built.update(kw) or FakeDownloader())
    monkeypatch.setattr(cli, "_load_cookies", lambda p: "")

    rc = cli._run_download(
        ["https://www.deviantart.com/alice/gallery", "--dest", str(tmp_path), "--quality", "best"]
    )

    assert rc == 0
    assert "downloaded: 1, skipped: 1, failed: 0" in capsys.readouterr().out
    assert built["quality"] == "best"
    assert str(built["destination"]) == str(tmp_path)


def test_oauth_login_requires_client_id(monkeypatch, capsys) -> None:
    monkeypatch.delenv("DEVIANTART_CLIENT_ID", raising=False)
    monkeypatch.delenv("DA_CLIENT_ID", raising=False)
    assert cli._oauth_login([]) == 64
    assert "client-id" in capsys.readouterr().err


def test_load_cookies_from_environment(monkeypatch) -> None:
    monkeypatch.setenv("DEVIANTART_COOKIES", " auth=token; auth_secure=secret ")
    assert cli._load_cookies(None) == "auth=token; auth_secure=secret"


def test_oauth_whoami_without_session(monkeypatch, capsys) -> None:
    monkeypatch.setattr(cli.OAuthSession, "from_store", classmethod(lambda cls: None))
    assert cli._oauth_whoami([]) == 1
    assert "not logged in" in capsys.readouterr().err
