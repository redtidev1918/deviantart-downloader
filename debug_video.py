#!/usr/bin/env python3
"""调试视频下载 - 查看实际的media数据结构"""
import sys
import json
sys.path.insert(0, '.')

from da_downloader.api import DeviantArtAPI
from da_downloader.models import ActionType

# 设置
proxies = {'http': 'http://127.0.0.1:7890', 'https': 'http://127.0.0.1:7890'}
headers = {'User-Agent': 'Mozilla/5.0'}

with open('cookies.txt', 'r') as f:
    cookies = f.read().strip()
headers['Cookie'] = cookies

# 创建API
api = DeviantArtAPI(headers=headers, proxies=proxies)

# 获取CSRF token
token = api.get_csrf_token('weaver-of-fate')
print(f"CSRF token: {token[:20]}...")

# 构建API URL
api_url = api.build_api_url(
    action=ActionType.GALLERY,
    username='weaver-of-fate'
)

# 获取作品列表
deviations, has_more, offset, cursor = api.fetch_deviations(
    url=api_url,
    offset=0
)

print(f"\nFound {len(deviations)} deviations")

# 查看第一个作品的media结构
if deviations:
    dev = deviations[0]
    print(f"\n作品: {dev.title}")
    print(f"类型: {dev.deviation_type}")
    print(f"\nMedia 结构:")
    print(json.dumps(dev.media, indent=2, ensure_ascii=False))
    
    # 尝试获取下载URL
    url = api.get_download_url(dev, 'f')
    print(f"\n下载URL: {url}")
