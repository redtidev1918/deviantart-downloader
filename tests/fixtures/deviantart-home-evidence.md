# DeviantArt home session evidence

Source: https://www.deviantart.com/
Captured: 2026-10-13T11:24:58.059Z (2026-10-13 Asia/Shanghai).
Method: one unauthenticated curl fetch through the local HTTP proxy; HTTP 200.
Raw response SHA256: c6c4e5b9a81cc88ba6bfd13afcf1b451ecce6f2d7a728b263f1e369bb75ddb68

The page assigns window.__INITIAL_STATE__ using JSON.parse of a double-quoted
JavaScript string; @@publicSession.isLoggedIn is false. The fixture keeps only
that session field and an existing username if present. Cookies, CSRF, personal
metadata and unrelated page state are omitted. The raw capture stays outside Git.

Signed-in and malformed fixtures in tests are synthetic mutations of this
verified structure. They exercise policy and robustness; they do not prove live
authenticated access. Earlier signed-in shape is independently documented in
DAViewer PR #101 (2026-10-13), but no signed-in fetch was performed here.
