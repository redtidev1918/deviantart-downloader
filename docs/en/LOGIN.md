# Login and authentication

**Language / 语言:** [中文](/LOGIN.md) · English

`devart-dl` supports two authentication methods: OAuth and cookies. On first use, pick OAuth —
it goes through DeviantArt's official API and never hands your password or cookies to the tool.

## Pick a method first

| Method | Fits | Coverage | Caveats |
|------|----------|----------|----------|
| OAuth (recommended) | Single works, galleries, favourites, tags, original files | Everything except search | Requires registering a free Public application |
| Cookie | You cannot register an application, or you need search | Artist/gallery, favourites, search | Does not support single works or tags; cookies expire |

> The official API currently has no search endpoint. To use search, run
> `devart-dl login clear` first to drop the OAuth session, then use cookies.

---

## Method 1: OAuth login (recommended)

OAuth uses Authorization Code + PKCE. Your password is only ever entered on
`deviantart.com`'s own page; the CLI stores just the access and refresh tokens and does not
need a `client_secret`.

### Step 1: register a Public application

1. Open <https://www.deviantart.com/developers/> and sign in to DeviantArt.
2. Click **Register Application**.
3. Fill in the name and description, for example `devart-dl` for both.
4. Choose **Public** as the application type.
5. In **OAuth2 Redirect URI Whitelist**, enter this character for character:

   ```text
   http://127.0.0.1:8765/callback
   ```

6. After saving, copy the **client_id** shown on the page. It is usually a numeric string and
   may be public; never give `client_secret` to this tool.

### Step 2: run the login command

```bash
devart-dl login oauth --client-id YOUR_CLIENT_ID
```

The command prints the authorisation URL and opens a browser:

1. Confirm the address bar shows a `deviantart.com` domain;
2. click **Authorize**;
3. the browser returns to `http://127.0.0.1:8765/callback`;
4. the terminal prints `logged in via OAuth` and you are done.

If you do not want the command to open a browser automatically, copy the URL from the terminal
by hand. The browser and the CLI must still be on the same computer:

```bash
devart-dl login oauth --client-id YOUR_CLIENT_ID --no-open
```

You can also store the client_id so later logins do not ask for it again:

```bash
# macOS / Linux
export DEVIANTART_CLIENT_ID='YOUR_CLIENT_ID'
devart-dl login oauth

# Windows PowerShell
$env:DEVIANTART_CLIENT_ID = 'YOUR_CLIENT_ID'
devart-dl login oauth
```

### Step 3: verify and download

```bash
devart-dl whoami
devart-dl https://www.deviantart.com/loish/art/underwater-913624585 --dest ./Downloads
```

`whoami` should print your username. To download the original file where the artist allows it:

```bash
devart-dl <work url> --quality original
```

### Token storage and logout

- Tokens are stored in `~/.deviantart_dl/oauth.json` with `0600` permissions.
- Once the access token expires, the refresh token renews it automatically.
- `devart-dl logout`: revoke the remote token and delete the local OAuth session.
- `devart-dl logout --local`: delete only the local OAuth session.

### OAuth troubleshooting

| Symptom | What to do |
|------|------|
| The browser did not open | Use `--no-open` and copy the URL printed in the terminal |
| Browser shows a redirect URI error | Confirm the whitelist entry is exactly `http://127.0.0.1:8765/callback` |
| The terminal keeps waiting for the callback | Confirm the browser and CLI are on the same computer, and that port 8765 is free |
| `error=access_denied` | Confirm the application type is Public and grant `basic browse` on the authorisation page |
| Refresh token expired | Run `devart-dl login oauth` again |
| Still using cookies after login | Run `devart-dl whoami`; if it fails, sign in with OAuth again |

---

## Method 2: cookie login

Cookie login uses DeviantArt's website endpoints. It suits artist/gallery, favourites and
search; single works and tags still require OAuth.

### Option A (recommended): one-click browser login, no manual copying

Requires Google Chrome / Edge on the machine, plus Node.js (≥ 22).

```bash
devart-dl login browser
```

The command opens a Chrome window at the DeviantArt login page and you simply
**sign in there normally**. Through the Chrome DevTools Protocol, the script reads the
post-login website cookies (`auth` / `auth_secure` / `userinfo`) at the network layer and saves
them to `~/.deviantart_dl/session.json` (permissions `0600`) — no developer tools, no
copy-paste.

> Why you must sign in in your own browser: DeviantArt's login page has an AWS WAF human check,
> and headless browsers run from a server or proxy get blocked, while a real browser on the real
> domain passes naturally. This is also the easiest way to obtain `auth_secure` (HttpOnly, so
> `document.cookie` cannot see it).

If Node is unavailable or you are on a GUI-less server, use the manual options below.

### Option B: copy cookies from the browser manually

Sign in to <https://www.deviantart.com/> in your browser first, then:

**Chrome / Edge**

1. Press `F12` (macOS: `⌥⌘I`).
2. Open **Application** → **Storage** → **Cookies**.
3. Select `https://www.deviantart.com`.
4. Find `auth` and `auth_secure` and copy each Value.

**Firefox**

1. Press `F12` (macOS: `⌥⌘I`).
2. Open **Storage** → **Cookies** → `https://www.deviantart.com`.
3. Find `auth` and `auth_secure` and copy each Value.

Combine the two values into a single line:

```text
auth=<first value>; auth_secure=<second value>
```

Never send this line to anyone and never commit it to a git repository. `auth_secure` is
usually an HttpOnly cookie, so do not rely on `document.cookie` to read it.

### B-1: interactive saving (simplest)

```bash
devart-dl login interactive
```

Paste the whole line at the prompt and press Enter. The cookies are saved to
`~/.deviantart_dl/session.json` with `0600` permissions.

### B-2: temporary environment variable

Usable only in the current terminal session, never written to a config file:

```bash
# macOS / Linux
export DEVIANTART_COOKIES='auth=<first value>; auth_secure=<second value>'
devart-dl https://www.deviantart.com/<username>/gallery

# Windows PowerShell
$env:DEVIANTART_COOKIES = 'auth=<first value>; auth_secure=<second value>'
devart-dl https://www.deviantart.com/<username>/gallery
```

The variable usually disappears when you close the terminal. Do not write real cookies into a
repository `.env` file.

### B-3: cookie file

Create a text file, for example `cookies.txt`, containing exactly one line:

```text
auth=<first value>; auth_secure=<second value>
```

Placed in the current directory it is picked up automatically; you can also point at it
explicitly:

```bash
devart-dl https://www.deviantart.com/<username>/gallery --cookies /secure/path/cookies.txt
```

Cookie read priority: the file given to `--cookies` → `DEVIANTART_COOKIES` → the saved
interactive session → `cookies.txt` in the current directory.

### Clearing cookie login

```bash
devart-dl login clear
```

This clears the OAuth and cookie sessions the tool saved, but does not delete a `cookies.txt`
you created yourself, nor the `DEVIANTART_COOKIES` variable in the current terminal.

### Cookie troubleshooting

| Symptom | What to do |
|------|------|
| 403 Forbidden | The cookie expired or was copied incompletely — copy `auth` and `auth_secure` again |
| 429 Too Many Requests | Wait a while and retry; prefer OAuth for bulk downloads |
| A single work or tag asks for the official API | That is the boundary of cookie mode; switch to OAuth |
| Old values are still read after changing cookies | Check the read priority above; run `devart-dl login clear` if needed |

---

## Mature / NSFW content and free quota

- Anonymous access to mature works only yields a **censored preview** (Wix's `blur_*`
  variants); the uncensored original requires being **signed in** (either cookies or OAuth).
- Originals go through the official `deviation/download/{uuid}` and are subject to the
  **free account's daily download quota**; exceeding it is refused (surfaced as
  `Free download limit reached` in daviewer/dakit). When the quota runs out, degrade to the
  preview/display image first, or subscribe to Core.
- To tell whether the signed-in state has lapsed: if the `preview`/`fullview` variants in the
  `init` response carry `blur_`, the request is being treated as anonymous;
  `isDownloadable=false` also often accompanies anonymous access or an unset mature-content
  preference.

## Security notes

- OAuth only ever enters your password on `deviantart.com`'s own page.
- Cookies are equivalent to login credentials: do not screenshot them, share them, write them
  into command output, or commit them to a repository.
- If you suspect a leak, immediately sign out of other sessions or change your password on
  DeviantArt, then delete the local authentication files.
