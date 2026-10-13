"""认证和 Cookie 管理模块

网页会话验证逻辑移植自 DAViewer `lib/core/auth/web_session_verifier.dart`
（生产首页证据验证，2026-10 DAViewer 会话恢复工程）：首页
``window.__INITIAL_STATE__`` 的 redux 风格键 ``@@publicSession`` 声明
``isLoggedIn`` 与 ``user.username``。三态判定：

- ``SIGNED_IN``：服务端确认登录且给出用户名；
- ``ANONYMOUS``：服务端明确声明未登录（``isLoggedIn: false`` 或
  ``anonymous`` 身份）；
- ``UNAVAILABLE``：网络失败 / 页面结构变化 / 证据缺失——绝不能与
  "未登录"混为一谈。

``isLoggedIn: true`` 但读不到用户名时保持未验证，不猜测。
"""

import enum
import json
import logging
import os
from dataclasses import dataclass
from typing import Optional

import requests

logger = logging.getLogger(__name__)

# 与 download.py 的 web provider 使用同一浏览器 UA（会话验证请求的 UA
# 必须与实际带 Cookie 抓取的请求一致，否则验证的不是同一个会话）。
_WEB_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
)
_HOME_URL = "https://www.deviantart.com/"
_INITIAL_STATE_MARKER = "window.__INITIAL_STATE__ = JSON.parse("


class WebSessionState(enum.Enum):
    """首页对当前 Cookie 会话的三态判定（服务端答案，不是本地猜测）。"""

    SIGNED_IN = "signed_in"
    ANONYMOUS = "anonymous"
    UNAVAILABLE = "unavailable"


@dataclass(frozen=True)
class WebSessionVerification:
    state: WebSessionState
    username: str = ""

    @property
    def is_signed_in(self) -> bool:
        return self.state == WebSessionState.SIGNED_IN


_JS_ESCAPES = {
    '"': '"',
    "'": "'",
    "\\": "\\",
    "/": "/",
    "b": "\b",
    "f": "\f",
    "n": "\n",
    "r": "\r",
    "t": "\t",
}


def _json_parse_assignment(html: str, marker: str) -> Optional[object]:
    """解析 ``JSON.parse('<json>')`` 形式的 JS 赋值，返回解析后的对象。

    引号内是 JS 字符串字面量（含 ``\\"`` 等 JS 转义），先做 JS 反转义再
    ``json.loads``。找不到 marker 或无法解析时返回 ``None``。
    """
    idx = html.find(marker)
    if idx == -1:
        return None
    rest = html[idx + len(marker) :].lstrip()
    if not rest or rest[0] not in ("'", '"'):
        return None
    quote = rest[0]
    out: list[str] = []
    i = 1
    length = len(rest)
    while i < length:
        ch = rest[i]
        if ch == "\\" and i + 1 < length:
            nxt = rest[i + 1]
            if nxt == "u" and i + 6 <= length:
                hex4 = rest[i + 2 : i + 6]
                try:
                    out.append(chr(int(hex4, 16)))
                    i += 6
                    continue
                except ValueError:
                    pass
            out.append(_JS_ESCAPES.get(nxt, nxt))
            i += 2
            continue
        if ch == quote:
            try:
                value: object = json.loads("".join(out))
                return value
            except json.JSONDecodeError:
                return None
        out.append(ch)
        i += 1
    return None


class AuthManager:
    """认证管理器 - 处理 Cookie 和登录状态"""

    def __init__(self, cookies_path: str = "cookies.txt"):
        self.cookies_path = cookies_path
        self.cookies: str = ""
        self.is_logged_in: bool = False

    def load_cookies(self) -> str:
        """加载 Cookie 文件（支持 cookies.txt 和会话文件）"""
        import json
        from pathlib import Path

        # 1. 尝试从会话文件加载
        session_file = Path.home() / ".deviantart_dl" / "session.json"
        if session_file.exists():
            try:
                with open(session_file, "r", encoding="utf-8") as f:
                    session_data = json.load(f)
                    cookies = str(session_data.get("cookies", ""))
                    if cookies:
                        logger.info(f"✓ Loaded cookies from session file: {session_file}")
                        self.cookies = cookies
                        return cookies
            except Exception as e:
                logger.debug(f"Failed to load session file: {e}")

        # 2. 尝试从 cookies.txt 加载
        if not os.path.isfile(self.cookies_path):
            logger.info(
                f"No cookie file found at {self.cookies_path} (optional for public content)"
            )
            return ""

        try:
            with open(self.cookies_path, "r", encoding="utf-8") as f:
                cookies = f.read().strip()

            # 移除注释行
            lines = [
                line.strip()
                for line in cookies.split("\n")
                if line.strip() and not line.strip().startswith("#")
            ]
            cookies = " ".join(lines)

            if cookies:
                logger.info(f"✓ Loaded cookies from: {self.cookies_path}")
                self.cookies = cookies
                return cookies
            else:
                logger.warning(f"Cookie file is empty: {self.cookies_path}")
                return ""
        except Exception as e:
            logger.error(f"Error loading cookies: {e}")
            return ""

    def validate_cookies(self, cookies: Optional[str] = None) -> bool:
        """验证 Cookie 是否包含认证信息"""
        if cookies is None:
            cookies = self.cookies

        if not cookies:
            return False

        # 检查关键的认证 Cookie
        auth_indicators = ["auth=", "auth_secure=", "userinfo="]
        has_auth = any(indicator in cookies for indicator in auth_indicators)

        if has_auth:
            logger.info("✓ Cookies appear valid (contains auth tokens)")
        else:
            logger.warning("⚠ Cookies may be invalid or incomplete")

        return has_auth

    def verify_web_session(
        self,
        cookies: Optional[str] = None,
        proxies: Optional[dict] = None,
        timeout: float = 10.0,
    ) -> WebSessionVerification:
        """向 DeviantArt 首页确认当前 Cookie 会话（服务端答案，三态）。

        网络失败、非 200、页面结构变化一律 ``UNAVAILABLE``，绝不误判为
        未登录。仅在服务端明确声明未登录时返回 ``ANONYMOUS``。
        """
        if cookies is None:
            cookies = self.cookies
        headers = {
            "Accept": "text/html,application/xhtml+xml",
            "User-Agent": _WEB_USER_AGENT,
        }
        if cookies:
            headers["Cookie"] = cookies
        try:
            response = requests.get(_HOME_URL, headers=headers, proxies=proxies, timeout=timeout)
        except requests.RequestException as exc:
            logger.debug(f"web session verify network failure: {exc}")
            return WebSessionVerification(WebSessionState.UNAVAILABLE)
        if response.status_code != 200:
            logger.info("web session verify: HTTP %d -> unavailable", response.status_code)
            return WebSessionVerification(WebSessionState.UNAVAILABLE)
        username = self.page_username_from_initial_state(response.text)
        if username == "anonymous":
            verdict = WebSessionVerification(WebSessionState.ANONYMOUS)
        elif username:
            verdict = WebSessionVerification(WebSessionState.SIGNED_IN, username)
        else:
            verdict = WebSessionVerification(WebSessionState.UNAVAILABLE)
        self.is_logged_in = verdict.is_signed_in
        logger.info("web session verify: %s", verdict.state.value)
        return verdict

    @staticmethod
    def page_username_from_initial_state(html: str) -> Optional[str]:
        """从首页 ``__INITIAL_STATE__`` 读取服务端渲染的用户名。

        返回 ``None`` 表示证据缺失或无法解析；``'anonymous'`` 表示服务端
        明确声明未登录（``isLoggedIn: false`` 或匿名身份）；其余为已登录
        用户名。``isLoggedIn: true`` 但无用户名保持 ``None``，不猜测。
        """
        state = _json_parse_assignment(html, _INITIAL_STATE_MARKER)
        if not isinstance(state, dict):
            return None
        session = state.get("@@publicSession") or state.get("@publicSession")
        if not isinstance(session, dict):
            return None
        user = session.get("user")
        raw_username = user.get("username") if isinstance(user, dict) else None
        username = raw_username.strip() if isinstance(raw_username, str) else None
        if session.get("isLoggedIn") is False:
            return "anonymous"
        return username

    def reload_cookies(self) -> str:
        """重新加载 Cookie"""
        logger.info("Reloading cookies...")
        return self.load_cookies()

    @staticmethod
    def show_login_guide() -> None:
        """显示登录指南"""
        guide = """
╔══════════════════════════════════════════════════════════════════════╗
║                    HOW TO GET DEVIANTART COOKIES                     ║
╚══════════════════════════════════════════════════════════════════════╝

1. Open DeviantArt in your browser and LOGIN to your account
   → https://www.deviantart.com

2. Open Browser Developer Tools:
   • Chrome/Edge: Press F12 or Ctrl+Shift+I (Cmd+Option+I on Mac)
   • Firefox: Press F12 or Ctrl+Shift+I (Cmd+Option+I on Mac)

3. Go to "Application" tab (Chrome) or "Storage" tab (Firefox)

4. In the left sidebar, expand "Cookies" and click on:
   → https://www.deviantart.com

5. Copy ALL cookie values in this format:
   cookie1=value1; cookie2=value2; cookie3=value3

   Important cookies to include:
   • auth
   • auth_secure
   • userinfo

6. Paste the copied cookies into a file named "cookies.txt"
   in the same folder as this script

Alternatively, you can use browser extensions like:
• "EditThisCookie" (Chrome)
• "Cookie-Editor" (Firefox/Chrome)

"""
        print(guide)

    def prompt_for_cookies(self, require_auth: bool = False) -> bool:
        """提示用户配置 Cookie"""
        if not self.cookies:
            print("! Running without cookies - only public content accessible")

            if require_auth:
                print("\n⚠ WARNING: This operation requires login!")
                answer = input("Show login guide? (y/n): ").lower()
                if answer in ["y", "yes"]:
                    self.show_login_guide()
                    input("\nPress Enter after setting up cookies, or Ctrl+C to exit...")
                    self.cookies = self.reload_cookies()
                    return bool(self.cookies)

        elif not self.validate_cookies():
            answer = input("Do you want to see the cookie setup guide? (y/n): ").lower()
            if answer in ["y", "yes"]:
                self.show_login_guide()

        return bool(self.cookies)


def diagnose_authentication_failure(
    cookies: str,
    proxy: Optional[str] = None,
    timeout: float = 10.0,
) -> Optional[str]:
    """401/403 之后的会话诊断：给出明确原因，而不是让用户猜。

    返回面向用户的英文提示（与 CLI 其余错误文案一致），无法诊断时返回
    ``None``。绝不静默发起额外网络请求重试下载本身。
    """
    proxies = {"http": proxy, "https": proxy} if proxy else {}
    if not cookies:
        return (
            "hint: no cookies were provided; mature/NSFW works need a login "
            "session - run `devart-dl login browser`"
        )
    verdict = AuthManager().verify_web_session(cookies=cookies, proxies=proxies, timeout=timeout)
    if verdict.state == WebSessionState.ANONYMOUS:
        return (
            "hint: the DeviantArt session has expired - run "
            "`devart-dl login browser` to refresh it"
        )
    if verdict.state == WebSessionState.UNAVAILABLE:
        return (
            "hint: could not confirm the session state (network or page "
            "change); if downloads keep failing, run `devart-dl login browser`"
        )
    return (
        f"hint: the session is valid (signed in as {verdict.username}); "
        "the server denied this item (mature/premium content or permission)"
    )
