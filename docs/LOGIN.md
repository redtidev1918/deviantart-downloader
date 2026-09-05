# 登录与认证

`devart-dl` 支持 OAuth 和 Cookie 两种认证方式。第一次使用建议选 OAuth：它走 DeviantArt 官方 API，不需要把密码或 Cookie 交给程序。

## 先选登录方式

| 方式 | 适合场景 | 支持范围 | 注意事项 |
|------|----------|----------|----------|
| OAuth（推荐） | 单张作品、画廊、收藏夹、标签、原图 | 除搜索外的下载 | 需注册一个免费的 Public 应用 |
| Cookie | 不方便注册应用，或需要搜索 | 作者/画廊、收藏夹、搜索 | 不支持单张作品和标签；Cookie 会过期 |

> 当前官方 API 没有搜索端点。使用搜索时请先运行 `devart-dl login clear` 清除 OAuth 会话，再使用 Cookie。

---

## 方法一：OAuth 登录（推荐）

OAuth 使用 Authorization Code + PKCE。你的密码只会输入在 `deviantart.com` 官方页面；CLI 只保存访问令牌和刷新令牌，不需要 `client_secret`。

### 第一步：注册 Public 应用

1. 打开 <https://www.deviantart.com/developers/> 并登录 DeviantArt。
2. 点击 **Register Application**。
3. 填写应用名称和描述，例如都填写 `devart-dl`。
4. 应用类型选择 **Public**。
5. 在 **OAuth2 Redirect URI Whitelist** 中逐字符填写：

   ```text
   http://127.0.0.1:8765/callback
   ```

6. 保存后复制页面显示的 **client_id**。它通常是一串数字，可以公开；不要把 `client_secret` 交给本工具。

### 第二步：运行登录命令

```bash
devart-dl login oauth --client-id 你的_client_id
```

命令会打印授权地址并打开浏览器：

1. 确认地址栏域名是 `deviantart.com`；
2. 点击 **Authorize**；
3. 浏览器跳回 `http://127.0.0.1:8765/callback`；
4. 终端显示 `logged in via OAuth` 即完成。

不想让命令自动打开浏览器时，可手动复制终端里的地址。浏览器和 CLI 仍需在同一台电脑上：

```bash
devart-dl login oauth --client-id 你的_client_id --no-open
```

也可以保存 client_id，之后登录时不用重复输入：

```bash
# macOS / Linux
export DEVIANTART_CLIENT_ID='你的_client_id'
devart-dl login oauth

# Windows PowerShell
$env:DEVIANTART_CLIENT_ID = '你的_client_id'
devart-dl login oauth
```

### 第三步：验证并下载

```bash
devart-dl whoami
devart-dl https://www.deviantart.com/loish/art/underwater-913624585 --dest ./Downloads
```

`whoami` 应显示你的用户名。下载作者允许提供的原始文件时使用：

```bash
devart-dl 作品链接 --quality original
```

### 令牌保存与退出

- 令牌保存在 `~/.deviantart_dl/oauth.json`，权限为 `0600`。
- 访问令牌过期后会使用 refresh token 自动续期。
- `devart-dl logout`：撤销远端令牌并删除本地 OAuth 会话。
- `devart-dl logout --local`：只删除本地 OAuth 会话。

### OAuth 常见问题

| 现象 | 处理 |
|------|------|
| 浏览器没有打开 | 使用 `--no-open`，手动复制终端打印的地址 |
| 浏览器显示 redirect URI 错误 | 确认白名单精确为 `http://127.0.0.1:8765/callback` |
| 终端一直等待回调 | 确认浏览器与 CLI 在同一台电脑，并检查 8765 端口是否被占用 |
| `error=access_denied` | 确认应用类型是 Public，并在授权页允许 `basic browse` 权限 |
| refresh token 失效 | 重新运行 `devart-dl login oauth` |
| 登录后仍走 Cookie | 运行 `devart-dl whoami`；若失败，重新登录 OAuth |

---

## 方法二：Cookie 登录

Cookie 登录走 DeviantArt 网页接口。它适合作者/画廊、收藏夹和搜索；单张作品与标签仍需 OAuth。

### 第一步：从浏览器复制 Cookie

先在浏览器正常登录 <https://www.deviantart.com/>，然后：

**Chrome / Edge**

1. 按 `F12`（macOS：`⌥⌘I`）。
2. 打开 **Application** → **Storage** → **Cookies**。
3. 选择 `https://www.deviantart.com`。
4. 找到 `auth` 和 `auth_secure`，分别复制它们的 Value。

**Firefox**

1. 按 `F12`（macOS：`⌥⌘I`）。
2. 打开 **Storage** → **Cookies** → `https://www.deviantart.com`。
3. 找到 `auth` 和 `auth_secure`，分别复制它们的 Value。

把两个值组成一行：

```text
auth=第一个值; auth_secure=第二个值
```

不要把这行内容发给任何人，也不要提交到 Git 仓库。`auth_secure` 通常是 HttpOnly Cookie，不能依赖 `document.cookie` 获取。

### 方式 A：交互式保存（最简单）

```bash
devart-dl login interactive
```

看到提示后粘贴上面的完整一行并按回车。Cookie 会保存到 `~/.deviantart_dl/session.json`，权限为 `0600`。

### 方式 B：临时环境变量

只在当前终端会话中使用，不写入配置文件：

```bash
# macOS / Linux
export DEVIANTART_COOKIES='auth=第一个值; auth_secure=第二个值'
devart-dl https://www.deviantart.com/用户名/gallery

# Windows PowerShell
$env:DEVIANTART_COOKIES = 'auth=第一个值; auth_secure=第二个值'
devart-dl https://www.deviantart.com/用户名/gallery
```

关闭终端后环境变量通常会消失。不要把真实 Cookie 写进仓库里的 `.env` 文件。

### 方式 C：Cookie 文件

创建一个文本文件，例如 `cookies.txt`，内容只有一行：

```text
auth=第一个值; auth_secure=第二个值
```

放在当前目录时会自动读取；也可以明确指定路径：

```bash
devart-dl https://www.deviantart.com/用户名/gallery --cookies /安全路径/cookies.txt
```

Cookie 读取优先级是：`--cookies` 指定文件 → `DEVIANTART_COOKIES` → 已保存的交互式会话 → 当前目录 `cookies.txt`。

### 清除 Cookie 登录

```bash
devart-dl login clear
```

这会清除工具保存的 OAuth 和 Cookie 会话，但不会删除你自己创建的 `cookies.txt`，也不会清除当前终端里的 `DEVIANTART_COOKIES`。

### Cookie 常见问题

| 现象 | 处理 |
|------|------|
| 403 Forbidden | Cookie 已过期或复制不完整，重新复制 `auth` 与 `auth_secure` |
| 429 Too Many Requests | 暂停一段时间再试；批量下载优先使用 OAuth |
| 单张作品或标签提示需要官方 API | 这是当前 Cookie 模式的能力边界，请改用 OAuth |
| 修改 Cookie 后仍读取旧值 | 检查上面的读取优先级，必要时运行 `devart-dl login clear` |

---

## 安全提醒

- OAuth 只在 `deviantart.com` 官方页面输入密码。
- Cookie 等同于登录凭据；不要截图、分享、写进命令输出或提交到仓库。
- 怀疑泄露时，立即在 DeviantArt 退出其他会话或修改密码，再删除本地认证文件。
