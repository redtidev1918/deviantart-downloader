#!/usr/bin/env python3
"""测试新的 404 检测逻辑"""
import sys
sys.path.insert(0, '.')

from da_downloader.api import DeviantArtAPI

# 创建 API 实例
proxies = {'http': 'http://127.0.0.1:7890', 'https': 'http://127.0.0.1:7890'}
headers = {'User-Agent': 'Mozilla/5.0'}

with open('cookies.txt', 'r') as f:
    cookies = f.read().strip()
headers['Cookie'] = cookies

api = DeviantArtAPI(headers=headers, proxies=proxies)

print("Testing new 404 detection logic...")
print("=" * 60)

# 获取 CSRF token
token = api.get_csrf_token('weaver-of-fate')

if token:
    print(f"✅ SUCCESS! CSRF token obtained: {token[:20]}...")
    print("\nThe new code is working correctly!")
else:
    print("❌ FAILED to get token")
    print("\nChecking debug file...")
    import os
    if os.path.exists('/tmp/deviantart_weaver-of-fate_response.html'):
        print("✅ Debug file exists at /tmp/deviantart_weaver-of-fate_response.html")
        with open('/tmp/deviantart_weaver-of-fate_response.html') as f:
            content = f.read()
            print(f"File size: {len(content)} bytes")
            if 'window.__CSRF_TOKEN__' in content:
                print("✅ CSRF token IS in the page")
            else:
                print("❌ No CSRF token in page")
    else:
        print("❌ No debug file - new code not running")
