# 🍪 Cookie 快速导出指南

DeviantArt 登录后快速导出 Cookie 的多种方法

---

## 方法1: 浏览器控制台脚本 ⭐推荐

**最简单！一键导出并复制**

### 使用步骤：

1. 在浏览器中登录 DeviantArt
2. 按 `F12` 打开开发者工具
3. 切换到 `Console`（控制台）标签
4. 复制粘贴以下代码并回车：

```javascript
// 直接复制下面的代码到控制台
(function(){let c=document.cookie;navigator.clipboard.writeText(c).then(()=>alert('✓ Cookie已复制到剪贴板！\n\n现在运行:\ndevart-dl login interactive\n\n然后粘贴Cookie')).catch(()=>{let t=document.createElement('textarea');t.value=c;t.style.position='fixed';t.style.opacity='0';document.body.appendChild(t);t.select();document.execCommand('copy');document.body.removeChild(t);alert('✓ Cookie已复制！')})})();
```

5. Cookie 自动复制到剪贴板！
6. 运行 `devart-dl login interactive` 并粘贴

---

## 方法2: 完整可视化脚本

**带UI界面，功能更强大**

1. 登录 DeviantArt
2. 按 `F12` → `Console`
3. 复制粘贴 `tools/export_cookies.js` 的完整内容
4. 会弹出一个漂亮的导出面板
5. 点击"复制关键 Cookie"或"复制完整 Cookie"

### 特点：
- ✓ 可视化界面
- ✓ 区分关键Cookie和完整Cookie
- ✓ 可保存为文件
- ✓ 一键复制
- ✓ 使用说明

---

## 方法3: 书签工具 (Bookmarklet)

**最方便！一键点击**

### 设置步骤：

1. 创建新书签
2. 名称：`导出DA Cookie`
3. 网址填入以下代码：

```javascript
javascript:(function(){let c=document.cookie;if(!c){alert('未检测到Cookie，请先登录！');return}navigator.clipboard.writeText(c).then(()=>alert('✓ Cookie已复制！\n\n下一步:\n1. 运行: devart-dl login interactive\n2. 粘贴Cookie')).catch(()=>{let t=document.createElement('textarea');t.value=c;document.body.appendChild(t);t.select();document.execCommand('copy');document.body.removeChild(t);alert('✓ Cookie已复制！')})})();
```

### 使用方法：
1. 在 DeviantArt 登录后的页面
2. 点击书签栏的"导出DA Cookie"
3. Cookie 自动复制到剪贴板！

---

## 方法4: 手动复制（传统方法）

### Chrome/Edge:

1. 登录 DeviantArt
2. `F12` → `Application` (应用程序) 标签
3. 左侧 `Storage` → `Cookies` → `https://www.deviantart.com`
4. 找到关键 Cookie：
   - `auth`
   - `auth_secure`
   - `userinfo`
5. 双击值，复制
6. 组合格式：`auth=xxx; auth_secure=xxx; userinfo=xxx`

### Firefox:

1. 登录 DeviantArt
2. `F12` → `存储` 标签
3. `Cookie` → `https://www.deviantart.com`
4. 找到并复制关键 Cookie

### Safari:

1. `Safari` → `偏好设置` → `高级`
2. 勾选"在菜单栏中显示开发菜单"
3. `开发` → `显示Web检查器`
4. `存储` → `Cookie`

---

## 方法5: 浏览器扩展

### EditThisCookie (推荐)

1. 安装扩展：
   - Chrome: [EditThisCookie](https://chrome.google.com/webstore/detail/editthiscookie/fngmhnnpilhplaeedifhccceomclgfbg)
   - Firefox: 在附加组件商店搜索
   
2. 使用方法：
   - 登录 DeviantArt
   - 点击扩展图标
   - 点击"Export" → 选择格式
   - 复制导出的 Cookie

### Cookie-Editor

1. 安装 [Cookie-Editor](https://cookie-editor.cgagnier.ca/)
2. 登录 DeviantArt
3. 点击扩展图标
4. 点击"Export" → "Header String"
5. 复制 Cookie 字符串

---

## 快速对比

| 方法 | 速度 | 难度 | 推荐 |
|------|------|------|------|
| **控制台脚本** | ⚡⚡⚡ 最快 | ⭐ 简单 | ✅ 推荐 |
| **书签工具** | ⚡⚡⚡ 最快 | ⭐ 简单 | ✅ 推荐 |
| **可视化脚本** | ⚡⚡ 快 | ⭐⭐ 中等 | - |
| **浏览器扩展** | ⚡⚡ 快 | ⭐ 简单 | ✅ |
| **手动复制** | ⚡ 慢 | ⭐⭐⭐ 复杂 | - |

---

## 完整工作流程示例

### 使用控制台脚本（最快）：

```bash
# 步骤1: 浏览器中
1. 登录 DeviantArt
2. F12 → Console
3. 粘贴一键脚本
4. Cookie自动复制

# 步骤2: 终端中
devart-dl login interactive
# 粘贴 Cookie
# 完成！

# 步骤3: 开始下载
devart-dl gallery username
```

---

## 常见问题

### Q: Cookie 会过期吗？
A: 是的，通常几天到几周。过期后重新导出即可。

### Q: 需要复制全部 Cookie 吗？
A: 不需要，关键 Cookie（auth, auth_secure, userinfo）即可。

### Q: 可以在多台电脑使用同一个 Cookie 吗？
A: 可以，但 DeviantArt 可能检测异常登录。

### Q: Cookie 安全吗？
A: Cookie 相当于登录凭证，不要分享给他人！

### Q: 脚本运行报错？
A: 确保：
- 已登录 DeviantArt
- 在 deviantart.com 域名下运行
- 允许 JavaScript 运行

---

## 安全提示

⚠️ **重要：**
- ✗ 不要将 Cookie 上传到 GitHub
- ✗ 不要分享 Cookie 给他人
- ✗ 不要在公共电脑使用
- ✓ 使用完后可以清除会话：`devart-dl login clear`
- ✓ 定期更新 Cookie
- ✓ 退出登录会使 Cookie 失效

---

## 故障排除

### 脚本无法复制到剪贴板
```
可能原因：浏览器安全限制
解决方案：手动复制控制台输出的 Cookie
```

### 找不到关键 Cookie
```
可能原因：未登录或登录过期
解决方案：重新登录 DeviantArt
```

### Cookie 导出后无法使用
```
可能原因：Cookie 格式错误
解决方案：确保格式为 name=value; name2=value2
```

---

## 推荐方案

**日常使用：**
1. 设置书签工具
2. 需要时点击书签
3. 自动复制 Cookie
4. 粘贴到工具

**首次设置：**
1. 使用控制台脚本
2. 或使用可视化界面
3. 保存为文件备用

**技术用户：**
1. 安装浏览器扩展
2. 设置自动导出
3. 或使用 API 方式

---

## 相关文档

- [登录方式完整指南](../README.md#登录方式)
- [防封IP指南](../README.md#防封ip指南)
- [FAQ](../README.md#faq)

---

**现在就试试最简单的方法吧！** 🚀

只需要在 DeviantArt 登录页面的控制台粘贴一行代码，Cookie 就自动复制好了！
