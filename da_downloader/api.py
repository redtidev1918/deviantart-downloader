"""DeviantArt API 封装模块"""

import logging
import json
import html
import re
from time import sleep
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlencode

import requests
from requests.exceptions import RequestException

from .models import Deviation, ActionType

logger = logging.getLogger(__name__)


class APIError(RuntimeError):
    """A request or response error that must not be treated as end-of-list."""


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
        self.session = requests.Session()
        self.session.headers.update(headers)
        self.session.proxies.update(proxies)
        
        # 记录代理使用情况
        if self.proxies:
            logger.info("Using configured proxy")
        else:
            logger.info("No proxy configured")
        
    def _make_request(self, url: str, timeout: int = 30) -> requests.Response:
        """发起 HTTP 请求并处理重试"""
        for attempt in range(self.max_retries):
            try:
                response = self.session.get(
                    url,
                    timeout=timeout
                )
                response.raise_for_status()
                return response
            except RequestException as e:
                status = getattr(getattr(e, 'response', None), 'status_code', None)
                logger.warning(
                    "Request failed (attempt %s/%s, type=%s%s)",
                    attempt + 1,
                    self.max_retries,
                    type(e).__name__,
                    f", status={status}" if status is not None else "",
                )
                if attempt < self.max_retries - 1:
                    sleep(self.retry_delay)
                else:
                    raise APIError(
                        f"Request failed after {self.max_retries} attempts"
                    ) from e
    
    def get_csrf_token(self, username: str) -> Optional[str]:
        """获取 CSRF Token"""
        logger.info(f"[v3.1.3] Fetching CSRF token for user: {username}")
        
        response = self._make_request(f"{self.BASE_URL}/{username}")
        page = response.text
        
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
            except (ValueError, IndexError):
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
        
        params = {"csrf_token": self.csrf_token}

        if action == ActionType.GALLERY:
            url = f"{self.BASE_URL}/_puppy/dashared/gallection/contents"
            params.update({"username": username, "type": "gallery"})
            if folder_id:
                params["folderid"] = folder_id
            else:
                # Without this flag the private endpoint returns only Featured,
                # which silently omits works stored in other gallery folders.
                params["all_folder"] = "true"
            pagination = "offset=<OFFSET>&limit=<LIMIT>"
                
        elif action == ActionType.SEARCH:
            if username.lower() == 'all':
                url = f"{self.BASE_URL}/_puppy/da-browse/api/networkbar/search/deviations"
                params["q"] = query or ""
                pagination = "cursor=<CURSOR>"
            else:
                url = f"{self.BASE_URL}/_puppy/dashared/gallection/search"
                params.update({
                    "username": username,
                    "type": "gallery",
                    "order": "most-recent",
                    "q": query or "",
                    "init": "true",
                })
                pagination = "offset=<OFFSET>&limit=<LIMIT>"
                      
        elif action == ActionType.FAVORITE:
            url = f"{self.BASE_URL}/_puppy/dashared/gallection/contents"
            params.update({
                "username": username,
                "type": "collection",
                "folderid": folder_id or "",
            })
            pagination = "offset=<OFFSET>&limit=<LIMIT>"
        else:
            raise ValueError(f"Unknown action type: {action}")
        
        return f"{url}?{urlencode(params)}&{pagination}"
    
    def fetch_deviations(self, url: str, offset: int = 0, 
                        cursor: str = "") -> Tuple[List[Deviation], bool, int, str]:
        """
        获取作品列表
        
        Returns:
            Tuple[deviations, has_more, next_offset, next_cursor]
        """
        # 替换 URL 中的占位符
        request_url = url.replace('<OFFSET>', str(offset)).replace('<CURSOR>', cursor)
        
        logger.debug("Fetching deviations (offset=%s, cursor=%s)", offset, bool(cursor))
        response = self._make_request(request_url, timeout=30)
        
        try:
            data = response.json()
        except (json.JSONDecodeError, ValueError) as e:
            raise APIError("DeviantArt returned invalid JSON") from e

        if not isinstance(data, dict):
            raise APIError("DeviantArt returned an invalid page object")
        
        # 检查错误
        if 'errorCode' in data or 'error_code' in data:
            message = data.get('errorDescription') or data.get('error_description')
            raise APIError(f"DeviantArt API error: {message or 'unknown error'}")
        
        # 提取作品列表
        deviations_data = data.get('results')
        if deviations_data is None:
            deviations_data = data.get('deviations', [])
        if not isinstance(deviations_data, list):
            raise APIError("DeviantArt page does not contain a results list")
        
        # 转换为 Deviation 对象
        deviations = []
        for position, item in enumerate(deviations_data):
            try:
                if not isinstance(item, dict):
                    raise ValueError("result is not an object")
                deviation = Deviation.from_api_response(item)
                deviations.append(deviation)
            except Exception as e:
                raise APIError(
                    f"Failed to parse deviation at offset {offset + position}"
                ) from e
        
        # 获取分页信息
        has_more = bool(data.get('hasMore', data.get('has_more', False)))
        raw_next_offset = data.get(
            'nextOffset', data.get('next_offset', offset + len(deviations_data))
        )
        next_cursor = data.get('nextCursor', data.get('next_cursor', '')) or ''
        if raw_next_offset is None and not has_more:
            next_offset = offset + len(deviations_data)
        else:
            try:
                next_offset = int(raw_next_offset)
            except (TypeError, ValueError) as e:
                raise APIError("DeviantArt returned an invalid next offset") from e

        if has_more and not next_cursor and next_offset <= offset:
            raise APIError("DeviantArt reported another page without a continuation")
        
        logger.info(f"Fetched {len(deviations)} deviations (has_more={has_more})")
        
        return deviations, has_more, next_offset, next_cursor
    
    def get_download_url(self, deviation: Deviation, quality: str) -> Optional[str]:
        """获取下载链接"""
        media = deviation.media
        
        if not media:
            logger.error(f"No media info for: {deviation.title}")
            return None
        
        base_uri = media.get('baseUri', '')
        if not base_uri:
            logger.error(f"No media URI for: {deviation.title}")
            return None
        raw_token = media.get('token', [])
        if isinstance(raw_token, list):
            token = str(raw_token[0]) if raw_token else ''
        else:
            token = str(raw_token or '')
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
        html_text = response.text
        
        if self.DOWNLOAD_STARTER not in html_text:
            logger.error("Download link not found in page (login may be required)")
            return None
        
        # 提取下载链接
        match = re.search(
            r'https://www\.deviantart\.com/download/[^"\'\\\s<]+',
            html_text,
        )
        if match:
            return html.unescape(match.group(0).replace('\\u0026', '&'))
        logger.error("Failed to extract original download URL")
        return None
    
    def _get_full_view_url(self, media: Dict, base_uri: str, 
                          token: str, pretty_name: str) -> Optional[str]:
        """获取全尺寸视图 URL（支持图片和视频）"""
        types = media.get('types', [])
        
        # 查找所有视频类型并选择最高质量
        videos = [t for t in types if isinstance(t, dict) and t.get('t') == 'video']
        
        if videos:
            # 按质量排序（1080p > 720p > 480p > 360p）
            quality_order = {'1080p': 4, '720p': 3, '480p': 2, '360p': 1}
            videos_sorted = sorted(
                videos, 
                key=lambda v: quality_order.get(v.get('q', ''), 0),
                reverse=True
            )
            
            best_video = videos_sorted[0]
            quality = best_video.get('q', 'unknown')
            logger.info(f"Found video content - selecting {quality} quality")
            
            # 视频URL在 'b' 字段中（完整URL）
            if 'b' in best_video:
                url = best_video['b']
                logger.info("Selected video quality: %s", quality)
                return url
        
        # 查找全图
        full_view = next(
            (t for t in types if isinstance(t, dict) and t.get('t') == 'fullview'),
            None,
        )
        
        if not full_view:
            logger.warning("Full view not found, using base URI")
            url = base_uri
        elif full_view.get('b'):
            url = full_view['b']
        elif 'c' in full_view:
            url = base_uri + full_view['c'].replace('<prettyName>', pretty_name)
        else:
            url = base_uri
        
        if token:
            url += f"{'&' if '?' in url else '?'}token={token}"
        
        return url
    
    def _get_preview_url(self, media: Dict, base_uri: str, 
                        token: str, pretty_name: str) -> Optional[str]:
        """获取预览 URL"""
        types = media.get('types', [])
        preview = next(
            (t for t in types if isinstance(t, dict) and t.get('t') == 'preview'),
            None,
        )
        
        if not preview:
            logger.warning("Preview not found, using full view")
            return self._get_full_view_url(media, base_uri, token, pretty_name)
        
        if 'c' not in preview:
            logger.warning("Preview path not found, using full view")
            return self._get_full_view_url(media, base_uri, token, pretty_name)
        
        url = base_uri + preview['c'].replace('<prettyName>', pretty_name)
        
        if token:
            url += f"{'&' if '?' in url else '?'}token={token}"
        
        return url
