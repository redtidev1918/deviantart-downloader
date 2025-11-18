"""DeviantArt API 封装模块"""

import logging
import json
import html
from time import sleep
from typing import Dict, List, Optional, Tuple
import requests
from requests.exceptions import RequestException

from .models import Deviation, ActionType

logger = logging.getLogger(__name__)


class DeviantArtAPI:
    """DeviantArt API 客户端"""
    
    BASE_URL = "https://www.deviantart.com"
    DOWNLOAD_STARTER = "https://www.deviantart.com/download/"
    
    def __init__(self, headers: Dict[str, str], proxies: Dict[str, str], 
                 retry_delay: int = 3, max_retries: int = 3):
        self.headers = headers
        self.proxies = proxies
        self.retry_delay = retry_delay
        self.max_retries = max_retries
        self.csrf_token: Optional[str] = None
        
        # 记录代理使用情况
        if self.proxies:
            logger.info(f"Using proxy: {self.proxies.get('http') or self.proxies.get('https')}")
        else:
            logger.info("No proxy configured")
        
    def _make_request(self, url: str, timeout: int = 30) -> Optional[requests.Response]:
        """发起 HTTP 请求并处理重试"""
        for attempt in range(self.max_retries):
            try:
                response = requests.get(
                    url,
                    headers=self.headers,
                    proxies=self.proxies,
                    timeout=timeout
                )
                response.raise_for_status()
                return response
            except RequestException as e:
                logger.warning(f"Request failed (attempt {attempt + 1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    sleep(self.retry_delay)
                else:
                    logger.error(f"Failed after {self.max_retries} attempts")
                    return None
    
    def get_csrf_token(self, username: str) -> Optional[str]:
        """获取 CSRF Token"""
        logger.info(f"[v3.1.3] Fetching CSRF token for user: {username}")
        
        response = self._make_request(f"{self.BASE_URL}/{username}")
        if not response:
            return None
        
        page = response.text
        
        # 调试：保存响应到文件
        try:
            debug_file = f"/tmp/deviantart_{username}_response.html"
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(page)
            logger.debug(f"Response saved to: {debug_file}")
        except:
            pass
        
        # 检查用户是否存在（改进检测逻辑，避免误判）
        # 检查 HTTP 状态码和页面标题
        if response.status_code == 404:
            logger.error(f"User '{username}' not found! (HTTP 404)")
            return None
        
        # 检查页面标题
        if '<title>' in page:
            try:
                title_start = page.index('<title>') + 7
                title_end = page.index('</title>', title_start)
                page_title = page[title_start:title_end]
                logger.debug(f"Page title: {page_title}")
                
                # 检查是否为404页面
                page_title_lower = page_title.lower()
                if 'page not found' in page_title_lower or ('404' in page_title_lower and 'error' in page_title_lower):
                    logger.error(f"User '{username}' not found! (Title indicates 404)")
                    return None
            except:
                pass
        
        # 提取 CSRF token
        try:
            start_marker = 'window.__CSRF_TOKEN__ = \''
            end_marker = '\';'
            
            if start_marker not in page:
                logger.error("Could not find CSRF token in page")
                return None
            
            start_idx = page.index(start_marker) + len(start_marker)
            page_fragment = page[start_idx:]
            end_idx = page_fragment.index(end_marker)
            csrf = page_fragment[:end_idx]
            
            logger.info("✓ CSRF token acquired")
            self.csrf_token = csrf
            return csrf
            
        except (ValueError, IndexError) as e:
            logger.error(f"Error extracting CSRF token: {e}")
            return None
    
    def build_api_url(self, action: ActionType, username: str, 
                      query: Optional[str] = None,
                      folder_id: Optional[str] = None) -> str:
        """构建 API URL"""
        if not self.csrf_token:
            raise ValueError("CSRF token not set. Call get_csrf_token first.")
        
        lazy_params = "&offset=<OFFSET>&limit=<LIMIT>"
        csrf_param = f"&csrf_token={self.csrf_token}"
        
        if action == ActionType.GALLERY:
            url = (f"{self.BASE_URL}/_puppy/dashared/gallection/contents"
                  f"?username={username}&type=gallery{lazy_params}{csrf_param}")
            
            if folder_id:
                url += f"&folderid={folder_id}"
            else:
                url += "&all_folder=true"
                
        elif action == ActionType.SEARCH:
            if username.lower() == 'all':
                # 全局搜索
                url = (f"{self.BASE_URL}/_puppy/da-browse/api/networkbar/search/deviations"
                      f"?q={query}&cursor=<CURSOR>{csrf_param}")
            else:
                # 用户内搜索
                url = (f"{self.BASE_URL}/_puppy/dashared/gallection/search"
                      f"?username={username}&type=gallery&order=most-recent"
                      f"&q={query}&init=true{lazy_params}{csrf_param}")
                      
        elif action == ActionType.FAVORITE:
            url = (f"{self.BASE_URL}/_puppy/dashared/gallection/contents"
                  f"?username={username}&type=collection{lazy_params}"
                  f"&folderid={folder_id}{csrf_param}")
        else:
            raise ValueError(f"Unknown action type: {action}")
        
        return url
    
    def fetch_deviations(self, url: str, offset: int = 0, 
                        cursor: str = "") -> Tuple[List[Deviation], bool, int, str]:
        """
        获取作品列表
        
        Returns:
            Tuple[deviations, has_more, next_offset, next_cursor]
        """
        # 替换 URL 中的占位符
        request_url = url.replace('<OFFSET>', str(offset)).replace('<CURSOR>', cursor)
        
        logger.debug(f"Fetching from: {request_url}")
        response = self._make_request(request_url, timeout=30)
        
        if not response:
            logger.error("Failed to fetch deviations")
            return [], False, offset, ""
        
        try:
            data = response.json()
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            return [], False, offset, ""
        
        # 检查错误
        if 'errorCode' in data:
            logger.error(f"API Error: {data}")
            return [], False, offset, ""
        
        # 提取作品列表
        deviations_data = data.get('results') or data.get('deviations', [])
        if not deviations_data:
            logger.warning("No deviations found in response")
            return [], False, offset, ""
        
        # 转换为 Deviation 对象
        deviations = []
        for item in deviations_data:
            try:
                deviation = Deviation.from_api_response(item)
                deviations.append(deviation)
            except Exception as e:
                logger.warning(f"Failed to parse deviation: {e}")
                continue
        
        # 获取分页信息
        has_more = data.get('hasMore', False)
        next_offset = data.get('nextOffset', offset + len(deviations))
        next_cursor = data.get('nextCursor', '')
        
        logger.info(f"Fetched {len(deviations)} deviations (has_more={has_more})")
        
        return deviations, has_more, next_offset, next_cursor
    
    def get_download_url(self, deviation: Deviation, quality: str) -> Optional[str]:
        """获取下载链接"""
        media = deviation.media
        
        if not media:
            logger.error(f"No media info for: {deviation.title}")
            return None
        
        base_uri = media.get('baseUri', '')
        token = media.get('token', [''])[0] if 'token' in media else ''
        pretty_name = media.get('prettyName', '')
        
        # 原图下载
        if quality == 'o' and deviation.is_downloadable:
            return self._get_original_download_url(deviation)
        
        # 全尺寸或备选
        elif quality == 'f' or (quality == 'o' and not deviation.is_downloadable):
            return self._get_full_view_url(media, base_uri, token, pretty_name)
        
        # 预览
        else:
            return self._get_preview_url(media, base_uri, token, pretty_name)
    
    def _get_original_download_url(self, deviation: Deviation) -> Optional[str]:
        """获取原图下载链接"""
        response = self._make_request(deviation.url)
        if not response:
            return None
        
        html_text = response.text
        
        if self.DOWNLOAD_STARTER not in html_text:
            logger.error("Download link not found in page (login may be required)")
            return None
        
        # 提取下载链接
        try:
            fragment = html_text.split(self.DOWNLOAD_STARTER)[1]
            download_path = fragment.split('"')[0]
            download_url = html.unescape(self.DOWNLOAD_STARTER + download_path)
            return download_url
        except (IndexError, ValueError) as e:
            logger.error(f"Failed to extract download URL: {e}")
            return None
    
    def _get_full_view_url(self, media: Dict, base_uri: str, 
                          token: str, pretty_name: str) -> Optional[str]:
        """获取全尺寸视图 URL（支持图片和视频）"""
        types = media.get('types', [])
        
        # 优先查找视频类型
        video = next((t for t in types if t.get('t') == 'video'), None)
        if video:
            logger.info("Found video content")
            if 'c' in video:
                url = base_uri + video['c'].replace('<prettyName>', pretty_name)
                if token:
                    url += f"?token={token}"
                return url
        
        # 查找全图
        full_view = next((t for t in types if t.get('t') == 'fullview'), None)
        
        if not full_view:
            logger.warning("Full view not found, using base URI")
            url = base_uri
        elif 'c' in full_view:
            url = base_uri + full_view['c'].replace('<prettyName>', pretty_name)
        else:
            url = base_uri
        
        if token:
            url += f"?token={token}"
        
        return url
    
    def _get_preview_url(self, media: Dict, base_uri: str, 
                        token: str, pretty_name: str) -> Optional[str]:
        """获取预览 URL"""
        types = media.get('types', [])
        preview = next((t for t in types if t.get('t') == 'preview'), None)
        
        if not preview:
            logger.error("Preview not found")
            return None
        
        if 'c' not in preview:
            logger.error("Preview content path not found")
            return None
        
        url = base_uri + preview['c'].replace('<prettyName>', pretty_name)
        
        if token:
            url += f"?token={token}"
        
        return url
    
    def download_file(self, url: str, timeout: int = 180) -> Optional[bytes]:
        """下载文件内容"""
        logger.debug(f"Downloading: {url}")
        
        for attempt in range(self.max_retries):
            try:
                response = requests.get(
                    url,
                    headers=self.headers,
                    proxies=self.proxies,
                    allow_redirects=True,
                    timeout=timeout
                )
                response.raise_for_status()
                return response.content
            except RequestException as e:
                logger.warning(f"Download failed (attempt {attempt + 1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    sleep(self.retry_delay)
        
        return None
