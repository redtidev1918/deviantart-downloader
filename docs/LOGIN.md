# 登录与认证 / Login & Authentication

`devart-dl` 支持两种登录方式：**官方 API（OAuth，推荐）** 与 **Cookie（降级）**。

---

## OAuth 登录（推荐）

OAuth 走的是标准 **Authorization Code + PKCE**（Public 客户端），登录在**系统浏览器**里完成，CLI 只在本机 `127.0.0.1:8765` 接收回调，**不会**接触你的 DeviantArt 密码，也**不保存 `client_secret`**。

### 1. 注册 Public 应用

1. 打开 <https://www.deviantart.com/developers/> 并登录你的 DeviantArt 账号。
2. 点击 **Register Application**（注册应用）。
3. 填写应用信息：
   - **Application Name**：任意，例如 `devart-dl`
   - **Description**：任意
   - **OAuth2 Redirect URI Whitelist**（回调地址白名单）：**精确**填写这一行（一行一个）：
     ```
     http://127.0.0.1:8765/callback
     ```
4. 提交后，记录生成的 **`client_id`**（一串数字）。

> **两个关键点：**
> - 应用类型必须是 **Public**。Public 应用**只需要 `client_id`**，不要生成或保存 `client_secret`——CLI 的登录流程不接收 secret。
> - 回调地址必须与上面**逐字符一致**（含 `http://`、端口 `8765`、路径 `/callback`），否则登录后浏览器回跳时 CLI 收不到回调。

### 2. 登录

```bash
devart-dl login oauth --client-id 你的_client_id
```

运行后会发生：

1. 终端打印一个授权 URL，并在默认浏览器打开它；
2. 在 DeviantArt 页面点击 **Authorize**（授权）；
3. 浏览器跳回 `http://127.0.0.1:8765/callback`，CLI 在本机接收回调并换取访问/刷新令牌。

无浏览器或远程/无界面环境：

```bash
# 不自动打开浏览器：手动复制终端打印的 URL 到任意浏览器打开
devart-dl login oauth --client-id 你的_client_id --no-open

# 仅打印授权 URL、不等待回调（适合把 URL 转发到别的设备，用 dakit 的
# dakit://oauth/callback 之外的自定义回传流程）
devart-dl login oauth --client-id 你的_client_id --manual
```

也可以把 `client_id` 放到环境变量里，省去每次传参：

```bash
export DEVIANTART_CLIENT_ID=你的_client_id
devart-dl login oauth
```

### 3. 验证与退出

```bash
devart-dl whoami          # 显示当前登录的用户名
devart-dl logout          # 撤销远端令牌 + 清除本地会话
devart-dl logout --local  # 只清除本地令牌，不撤销远端
```

### 令牌存储与续期

- 令牌保存在 `~/.deviantart_dl/oauth.json`，权限 `0600`（仅当前用户可读写）。
- 访问令牌过期后会自动用 refresh token 续期，无需重复登录。
- 令牌、授权码、Cookie 等敏感信息**永远不会写入日志**（脱敏）。

### 真实登录验证清单（建议首次跑一遍）

```bash
# 1) 登录
devart-dl login oauth --client-id 你的_client_id

# 2) 验证身份（应打印你的用户名）
devart-dl whoami

# 3) 下载一个公开作品（应走官方 API，无需 Cookie/防封）
devart-dl https://www.deviantart.com/loish/art/underwater-913624585 --dest ./tmp

# 4) 下载原图（需该作品允许下载）
devart-dl https://www.deviantart.com/loish/art/underwater-913624585 --quality original --dest ./tmp

# 5) 退出并确认令牌被撤销
devart-dl logout
devart-dl whoami   # 此时应提示未登录
```

### 常见问题

| 现象 | 处理 |
|------|------|
| 浏览器没跳转 / CLI 一直等回调 | 检查回调地址是否**精确**写进了 whitelist；检查本机 `8765` 端口是否被占用 |
| 授权被拒 / `error=access_denied` | 确认应用是 **Public** 类型；确认 scope 未被改动（默认 `basic browse`） |
| refresh token 失效、提示需重新授权 | 重新运行 `devart-dl login oauth` 即可 |
| 登录后仍提示走 Cookie 路径 | 确认 `~/.deviantart_dl/oauth.json` 存在（`devart-dl whoami` 应能打印用户名） |

---

## Cookie 登录（降级方案）

当没有 OAuth 会话时，下载命令会自动回退到 Cookie 方式（走网页私有接口）。

```bash
# 交互式输入 Cookie（保存到 ~/.deviantart_dl/session.json）
devart-dl login interactive

# 或创建 cookies.txt / 设置环境变量
# DEVIANTART_COOKIES="auth=xxx; auth_secure=xxx; ..."
```

> **获取 Cookie**：浏览器登录 DeviantArt 后，F12 → Application（或 Storage）→ Cookies，复制 `auth` 与 `auth_secure` 字段；或在 Console 里输入 `document.cookie`。

Cookie 方式需要 Cookie 不过期；过期后重新导出。若频繁遇到 403/429，优先改用 OAuth。
