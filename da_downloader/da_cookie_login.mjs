#!/usr/bin/env node
// 一键获取 DeviantArt 网页登录 Cookie（成熟/NSFW 作品下载需要登录会话）。
//
// 为什么这么做：DeviantArt 登录页是 AWS WAF 人机校验 SPA，服务器端 fetch / 无头代理
// 会被挡（detectIp / validateHostname），令牌也绑定浏览器自身环境。正确做法是让你
// 本机的真实 Chrome 在「真实 DeviantArt 域」登录，脚本用 Chrome DevTools Protocol
// 从网络层读出登录后的网页 Cookie（auth / auth_secure / userinfo），写到本下载器
// 约定的 ~/.deviantart_dl/session.json，之后 `devart-dl` 下载成熟作品自动带上。
//
// 用法：
//   node scripts/da-cookie-login.mjs
//
// 依赖：本机已装 Google Chrome / Edge；Node >= 22（自带 WebSocket / fetch）。不装任何 npm 包。
// 参考：与 deviantdrop 一键登录同思路；只抓网页 Cookie，不碰 OAuth。

import { spawn } from "node:child_process";
import { setTimeout as sleep } from "node:timers/promises";
import { homedir, platform } from "node:os";
import { join } from "node:path";
import { mkdirSync, existsSync, writeFileSync, chmodSync } from "node:fs";

const SESSION_COOKIES = ["auth", "auth_secure", "userinfo"];
const DEBUG_PORT = 9334;
const TIMEOUT = Number(process.env.DA_LOGIN_TIMEOUT_MS) || 10 * 60 * 1000;
const PROFILE_DIR = join(homedir(), ".config", "da-cookie-login", "chrome-profile");

function chromePath() {
  const p = platform();
  const candidates = p === "darwin"
    ? ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
       "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
       "/Applications/Chromium.app/Contents/MacOS/Chromium"]
    : p === "win32"
      ? [join(process.env.PROGRAMFILES || "", "Google/Chrome/Application/chrome.exe"),
         join(process.env.LOCALAPPDATA || "", "Google/Chrome/Application/chrome.exe")]
      : ["/usr/bin/google-chrome", "/usr/bin/google-chrome-stable", "/usr/bin/chromium",
         "/usr/bin/microsoft-edge", "/snap/bin/chromium"];
  const found = candidates.find((c) => existsSync(c));
  if (!found) throw new Error("找不到 Chrome/Edge，请先安装 Google Chrome。");
  return found;
}

function sessionFile() {
  return join(homedir(), ".deviantart_dl", "session.json");
}

async function main() {
  mkdirSync(PROFILE_DIR, { recursive: true });
  const isWin = platform() === "win32";
  const chrome = spawn(chromePath(), [
    `--remote-debugging-port=${DEBUG_PORT}`,
    `--user-data-dir=${PROFILE_DIR}`,
    "--no-first-run", "--no-default-browser-check",
    "https://www.deviantart.com/users/login",
  ], { stdio: ["ignore", "ignore", "ignore"], detached: !isWin });

  try {
    // 等 DevTools 就绪
    let target = null;
    for (let i = 0; i < 40; i++) {
      try {
        const r = await fetch(`http://127.0.0.1:${DEBUG_PORT}/json/list`);
        const tabs = await r.json();
        target = tabs.find((t) => t.type === "page" && t.webSocketDebuggerUrl);
        if (target) break;
      } catch { /* not ready */ }
      await sleep(500);
    }
    if (!target) throw new Error("Chrome 远程调试端口未就绪。");

    const ws = new WebSocket(target.webSocketDebuggerUrl);
    await new Promise((resolve, reject) => { ws.onopen = resolve; ws.onerror = reject; });
    let msgId = 0;
    const pending = new Map();
    const send = (method, params = {}) => new Promise((resolve, reject) => {
      const id = ++msgId;
      pending.set(id, { resolve, reject });
      ws.send(JSON.stringify({ id, method, params }));
    });
    ws.onmessage = (ev) => {
      const msg = JSON.parse(ev.data);
      if (msg.id && pending.has(msg.id)) {
        const { resolve, reject } = pending.get(msg.id);
        pending.delete(msg.id);
        msg.error ? reject(new Error(msg.error.message)) : resolve(msg.result);
      }
    };
    await send("Network.enable");

    console.log("\n即将打开 Chrome 进入 DeviantArt 登录页。请在浏览器里登录你的账号。");
    console.log("登录成功后脚本自动捕获 Cookie（最多 10 分钟）。\n");

    const readSession = async () => {
      const ctx = await send("Network.getCookies", { urls: ["https://www.deviantart.com/"] });
      let jar = ctx.cookies || [];
      if (!SESSION_COOKIES.every((n) => jar.some((c) => c.name === n))) {
        const all = (await send("Network.getAllCookies")).cookies || [];
        jar = all.filter((c) => /(^|\.)deviantart\.com$/i.test(c.domain));
      }
      const map = {};
      for (const c of jar) if (SESSION_COOKIES.includes(c.name)) map[c.name] = c.value;
      const has = SESSION_COOKIES.every((n) => map[n]);
      const cookies = SESSION_COOKIES.filter((n) => map[n]).map((n) => `${n}=${map[n]}`).join("; ");
      return { has, cookies };
    };

    const t0 = Date.now();
    let lastHint = "";
    while (Date.now() - t0 < TIMEOUT) {
      await sleep(1500);
      const { has, cookies } = await readSession();
      const hint = has ? "已检测到登录 Cookie，正在保存…" : "等待你在页面里登录…";
      if (hint !== lastHint) { console.log(hint); lastHint = hint; }
      if (has) {
        const path = sessionFile();
        mkdirSync(join(homedir(), ".deviantart_dl"), { recursive: true });
        const payload = {
          cookies,
          saved_at: new Date().toISOString(),
          method: "cdp-one-click",
        };
        writeFileSync(path, JSON.stringify(payload, null, 2), { encoding: "utf8", mode: 0o600 });
        try { chmodSync(path, 0o600); } catch { /* best effort */ }
        ws.close();
        console.log(`\n✅ Cookie 已保存到 ${path}`);
        console.log("现在可以直接用 devart-dl 下载成熟/NSFW 作品（会自动带上登录会话）。");
        return;
      }
    }
    ws.close();
    throw new Error("登录超时，请重新运行并在 10 分钟内完成登录。");
  } finally {
    try { isWin ? chrome.kill() : process.kill(-chrome.pid); } catch { /* cleanup */ }
  }
}

main().catch((e) => { console.error("\n❌ 获取 Cookie 失败：", e.message); process.exit(1); });
