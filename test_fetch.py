#!/usr/bin/env python3
"""快速测试获取用户页面"""
import requests

# 代理
proxies = {'http': 'http://127.0.0.1:7890', 'https': 'http://127.0.0.1:7890'}

# Cookies
with open('cookies.txt', 'r') as f:
    cookies = f.read().strip()

# 请求
url = 'https://www.deviantart.com/weaver-of-fate'
headers = {
    'User-Agent': 'Mozilla/5.0',
    'Cookie': cookies
}

print(f"Fetching: {url}")
print(f"Proxy: {proxies}")

response = requests.get(url, headers=headers, proxies=proxies, timeout=30)

print(f"\nStatus: {response.status_code}")
print(f"Content-Length: {len(response.text)}")

# 保存
with open('/tmp/test_page.html', 'w') as f:
    f.write(response.text)
print(f"Saved to: /tmp/test_page.html")

# 检查
checks = {
    '404': '404' in response.text,
    'Page Not Found': 'Page Not Found' in response.text,
    'CSRF Token': 'window.__CSRF_TOKEN__' in response.text,
}

print("\nChecks:")
for key, value in checks.items():
    status = "✅" if value else "❌"
    print(f"  {status} {key}")

# 标题
if '<title>' in response.text:
    try:
        start = response.text.index('<title>') + 7
        end = response.text.index('</title>', start)
        print(f"\nTitle: {response.text[start:end]}")
    except:
        pass
