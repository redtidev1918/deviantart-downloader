/**
 * DeviantArt Cookie 导出工具
 * 在浏览器控制台运行此脚本，快速导出 Cookie
 * 
 * 使用方法：
 * 1. 在 DeviantArt 登录后的页面
 * 2. 按 F12 打开开发者工具
 * 3. 切换到 Console 标签
 * 4. 复制粘贴此脚本并回车
 * 5. Cookie 会自动复制到剪贴板
 */

(function() {
    'use strict';
    
    // 样式定义
    const styles = `
        #cookie-export-panel {
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            z-index: 999999;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 12px;
            padding: 30px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            font-family: 'Segoe UI', Arial, sans-serif;
            color: white;
            min-width: 500px;
            max-width: 90vw;
        }
        
        #cookie-export-panel h2 {
            margin: 0 0 20px 0;
            font-size: 24px;
            text-align: center;
        }
        
        #cookie-export-panel .cookie-box {
            background: rgba(255,255,255,0.1);
            border: 1px solid rgba(255,255,255,0.2);
            border-radius: 8px;
            padding: 15px;
            margin: 15px 0;
            word-break: break-all;
            max-height: 200px;
            overflow-y: auto;
            font-family: 'Courier New', monospace;
            font-size: 12px;
        }
        
        #cookie-export-panel .btn {
            background: rgba(255,255,255,0.9);
            color: #667eea;
            border: none;
            border-radius: 6px;
            padding: 12px 24px;
            margin: 5px;
            cursor: pointer;
            font-weight: bold;
            font-size: 14px;
            transition: all 0.3s;
        }
        
        #cookie-export-panel .btn:hover {
            background: white;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        }
        
        #cookie-export-panel .btn-group {
            text-align: center;
            margin-top: 20px;
        }
        
        #cookie-export-panel .status {
            text-align: center;
            margin-top: 10px;
            font-size: 14px;
            min-height: 20px;
        }
        
        #cookie-export-panel .success {
            color: #4ade80;
        }
        
        #cookie-export-panel .info {
            background: rgba(255,255,255,0.1);
            border-radius: 6px;
            padding: 10px;
            margin: 10px 0;
            font-size: 12px;
            line-height: 1.6;
        }
        
        #cookie-export-overlay {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0,0,0,0.5);
            z-index: 999998;
            backdrop-filter: blur(5px);
        }
    `;
    
    // 获取所有 Cookie
    function getCookies() {
        return document.cookie;
    }
    
    // 获取关键 Cookie
    function getKeyCookies() {
        const cookies = document.cookie.split(';');
        const keyCookies = ['auth', 'auth_secure', 'userinfo'];
        const result = [];
        
        cookies.forEach(cookie => {
            const [name, value] = cookie.trim().split('=');
            if (keyCookies.some(key => name.includes(key))) {
                result.push(`${name}=${value}`);
            }
        });
        
        return result.join('; ');
    }
    
    // 复制到剪贴板
    async function copyToClipboard(text) {
        try {
            await navigator.clipboard.writeText(text);
            return true;
        } catch (err) {
            // 备用方法
            const textarea = document.createElement('textarea');
            textarea.value = text;
            textarea.style.position = 'fixed';
            textarea.style.opacity = '0';
            document.body.appendChild(textarea);
            textarea.select();
            const success = document.execCommand('copy');
            document.body.removeChild(textarea);
            return success;
        }
    }
    
    // 保存为文件
    function saveAsFile(content, filename) {
        const blob = new Blob([content], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.click();
        URL.revokeObjectURL(url);
    }
    
    // 显示状态消息
    function showStatus(message, isSuccess = true) {
        const status = document.getElementById('cookie-status');
        if (status) {
            status.textContent = message;
            status.className = isSuccess ? 'status success' : 'status';
            setTimeout(() => {
                status.textContent = '';
            }, 3000);
        }
    }
    
    // 创建UI
    function createUI() {
        // 添加样式
        const styleEl = document.createElement('style');
        styleEl.textContent = styles;
        document.head.appendChild(styleEl);
        
        // 创建遮罩
        const overlay = document.createElement('div');
        overlay.id = 'cookie-export-overlay';
        
        // 创建面板
        const panel = document.createElement('div');
        panel.id = 'cookie-export-panel';
        
        const cookies = getCookies();
        const keyCookies = getKeyCookies();
        
        panel.innerHTML = `
            <h2>🍪 DeviantArt Cookie 导出工具</h2>
            
            <div class="info">
                ✓ 已检测到登录状态<br>
                ✓ 找到 ${cookies.split(';').length} 个 Cookie<br>
                ✓ 关键认证 Cookie: ${keyCookies ? '已找到' : '未找到'}
            </div>
            
            <div style="margin: 15px 0;">
                <strong>完整 Cookie:</strong>
                <div class="cookie-box" id="full-cookies">${cookies || '(无)'}</div>
            </div>
            
            <div style="margin: 15px 0;">
                <strong>关键 Cookie (推荐):</strong>
                <div class="cookie-box" id="key-cookies">${keyCookies || '(未找到关键Cookie)'}</div>
            </div>
            
            <div class="btn-group">
                <button class="btn" id="copy-full-btn">📋 复制完整 Cookie</button>
                <button class="btn" id="copy-key-btn">📋 复制关键 Cookie</button>
                <button class="btn" id="save-file-btn">💾 保存为文件</button>
                <button class="btn" id="close-btn">❌ 关闭</button>
            </div>
            
            <div id="cookie-status" class="status"></div>
            
            <div class="info" style="margin-top: 15px; font-size: 11px;">
                <strong>使用说明:</strong><br>
                1. 点击"复制关键 Cookie"（推荐）或"复制完整 Cookie"<br>
                2. 运行: <code>devart-dl login interactive</code><br>
                3. 粘贴复制的 Cookie<br>
                4. 开始下载！
            </div>
        `;
        
        // 添加到页面
        document.body.appendChild(overlay);
        document.body.appendChild(panel);
        
        // 绑定事件
        document.getElementById('copy-full-btn').addEventListener('click', async () => {
            const success = await copyToClipboard(cookies);
            showStatus(success ? '✓ 完整 Cookie 已复制到剪贴板！' : '✗ 复制失败，请手动复制', success);
        });
        
        document.getElementById('copy-key-btn').addEventListener('click', async () => {
            const success = await copyToClipboard(keyCookies || cookies);
            showStatus(success ? '✓ 关键 Cookie 已复制到剪贴板！' : '✗ 复制失败，请手动复制', success);
        });
        
        document.getElementById('save-file-btn').addEventListener('click', () => {
            saveAsFile(cookies, 'deviantart_cookies.txt');
            showStatus('✓ Cookie 已保存为文件！');
        });
        
        const closePanel = () => {
            document.body.removeChild(overlay);
            document.body.removeChild(panel);
        };
        
        document.getElementById('close-btn').addEventListener('click', closePanel);
        overlay.addEventListener('click', closePanel);
    }
    
    // 执行
    console.log('%c🍪 DeviantArt Cookie 导出工具', 'font-size: 20px; color: #667eea; font-weight: bold;');
    console.log('%c正在导出 Cookie...', 'font-size: 14px; color: #666;');
    
    createUI();
    
    console.log('%c✓ Cookie 导出面板已打开！', 'font-size: 14px; color: #4ade80; font-weight: bold;');
    
})();
