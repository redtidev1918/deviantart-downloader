"""Async DeviantArt API client using httpx"""

import asyncio
import html
import logging
from typing import Any, AsyncIterator, Optional
from urllib.parse import urlencode

import httpx
from pydantic import HttpUrl

from ..models.config import AppConfig
from ..models.deviation import Deviation

logger = logging.getLogger(__name__)


class APIError(Exception):
    """DeviantArt API error"""

    pass


class AuthenticationError(APIError):
    """Authentication/authorization error"""

    pass


class DeviantArtAPI:
    """
    Async DeviantArt API client.

    Features:
    - Async/await support with httpx
    - Automatic retry with exponential backoff
    - Rate limiting
    - CSRF token management
    - Cookie-based authentication
    """

    BASE_URL = "https://www.deviantart.com"
    DOWNLOAD_MARKER = "https://www.deviantart.com/download/"

    def __init__(self, config: AppConfig, cookies: str = ""):
        self.config = config
        self.cookies = cookies
        self.csrf_token: Optional[str] = None

        # Create async client
        self.client = httpx.AsyncClient(
            headers=config.get_headers(cookies),
            proxies=config.get_proxies(),
            timeout=config.timeout,
            follow_redirects=True,
            limits=httpx.Limits(
                max_connections=config.concurrent_downloads * 2,
                max_keepalive_connections=config.concurrent_downloads,
            ),
        )

    async def __aenter__(self):
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()

    async def _request(
        self, 
        url: str, 
        method: str = "GET",
        **kwargs
    ) -> httpx.Response:
        """
        Make HTTP request with retry logic.

        Args:
            url: Request URL
            method: HTTP method
            **kwargs: Additional arguments for httpx

        Returns:
            httpx.Response

        Raises:
            APIError: On request failure
        """
        last_error = None

        for attempt in range(self.config.max_retries + 1):
            try:
                if attempt > 0:
                    delay = self.config.retry_delay * (2 ** (attempt - 1))
                    logger.debug(f"Retry attempt {attempt} after {delay}s delay")
                    await asyncio.sleep(delay)

                response = await self.client.request(method, url, **kwargs)
                response.raise_for_status()

                # Rate limiting
                if self.config.rate_limit_delay > 0:
                    await asyncio.sleep(self.config.rate_limit_delay)

                return response

            except httpx.HTTPStatusError as e:
                last_error = e
                if e.response.status_code == 404:
                    raise APIError(f"Not found: {url}") from e
                elif e.response.status_code in (401, 403):
                    raise AuthenticationError("Authentication required") from e
                elif e.response.status_code >= 500:
                    logger.warning(f"Server error {e.response.status_code}, retrying...")
                    continue
                else:
                    raise APIError(f"HTTP {e.response.status_code}") from e

            except (httpx.RequestError, httpx.TimeoutException) as e:
                last_error = e
                logger.warning(f"Request failed: {e}, retrying...")
                continue

        raise APIError(f"Request failed after {self.config.max_retries + 1} attempts") from last_error

    async def get_csrf_token(self, username: str = "") -> str:
        """
        Get CSRF token from DeviantArt.

        Args:
            username: Optional username to fetch from user page

        Returns:
            CSRF token string

        Raises:
            APIError: If token cannot be retrieved
        """
        url = f"{self.BASE_URL}/{username}" if username else self.BASE_URL

        logger.info(f"Fetching CSRF token from {url}")
        response = await self._request(url)
        html_content = response.text

        # Check if user exists
        if "404" in html_content or "Page Not Found" in html_content:
            raise APIError(f"User '{username}' not found")

        # Extract CSRF token
        marker_start = 'window.__CSRF_TOKEN__ = \''
        marker_end = '\';'

        if marker_start not in html_content:
            raise APIError("CSRF token not found in page")

        try:
            start_idx = html_content.index(marker_start) + len(marker_start)
            end_idx = html_content.index(marker_end, start_idx)
            token = html_content[start_idx:end_idx]

            self.csrf_token = token
            logger.info("✓ CSRF token acquired")
            return token

        except ValueError as e:
            raise APIError("Failed to extract CSRF token") from e

    def build_api_url(
        self,
        action: str,
        username: str,
        query: Optional[str] = None,
        folder_id: Optional[str] = None,
    ) -> str:
        """
        Build DeviantArt API URL.

        Args:
            action: Action type (gallery/search/fav)
            username: Username
            query: Search query (for search action)
            folder_id: Folder ID (for specific gallery/fav)

        Returns:
            Complete API URL with placeholders

        Raises:
            ValueError: If required parameters missing
        """
        if not self.csrf_token:
            raise ValueError("CSRF token not set. Call get_csrf_token() first")

        base_params = {"csrf_token": self.csrf_token}
        lazy_params = "&offset=<OFFSET>&limit=<LIMIT>"

        if action == "gallery":
            url = f"{self.BASE_URL}/_puppy/dashared/gallection/contents"
            params = {**base_params, "username": username, "type": "gallery"}

            if folder_id:
                params["folderid"] = folder_id
            else:
                params["all_folder"] = "true"

        elif action == "search":
            if username.lower() == "all":
                # Global search
                url = f"{self.BASE_URL}/_puppy/da-browse/api/networkbar/search/deviations"
                params = {**base_params, "q": query}
                lazy_params = "&cursor=<CURSOR>"
            else:
                # User search
                url = f"{self.BASE_URL}/_puppy/dashared/gallection/search"
                params = {
                    **base_params,
                    "username": username,
                    "type": "gallery",
                    "order": "most-recent",
                    "q": query,
                    "init": "true",
                }

        elif action == "fav":
            if not folder_id:
                raise ValueError("folder_id required for fav action")

            url = f"{self.BASE_URL}/_puppy/dashared/gallection/contents"
            params = {
                **base_params,
                "username": username,
                "type": "collection",
                "folderid": folder_id,
            }

        else:
            raise ValueError(f"Unknown action: {action}")

        return f"{url}?{urlencode(params)}{lazy_params}"

    async def fetch_deviations(
        self,
        url: str,
        offset: int = 0,
        cursor: str = "",
        limit: Optional[int] = None,
    ) -> tuple[list[Deviation], bool, int, str]:
        """
        Fetch deviations from API.

        Args:
            url: API URL with placeholders
            offset: Pagination offset
            cursor: Pagination cursor (for global search)
            limit: Items per request

        Returns:
            Tuple of (deviations, has_more, next_offset, next_cursor)

        Raises:
            APIError: On API error
        """
        limit = limit or self.config.lazy_load_limit

        # Replace placeholders
        request_url = url.replace("<OFFSET>", str(offset))
        request_url = request_url.replace("<LIMIT>", str(limit))
        request_url = request_url.replace("<CURSOR>", cursor)

        logger.debug(f"Fetching deviations: {request_url}")

        response = await self._request(request_url)
        data = response.json()

        # Check for API errors
        if "errorCode" in data:
            error_msg = data.get("errorDescription", "Unknown error")
            raise APIError(f"API Error: {error_msg}")

        # Extract deviations
        deviations_data = data.get("results") or data.get("deviations", [])
        if not deviations_data:
            logger.warning("No deviations found in response")
            return [], False, offset, ""

        # Parse deviations
        deviations = []
        for item in deviations_data:
            try:
                deviation = Deviation.from_api_response(item)
                deviations.append(deviation)
            except Exception as e:
                logger.warning(f"Failed to parse deviation: {e}")
                continue

        # Pagination info
        has_more = data.get("hasMore", False)
        next_offset = data.get("nextOffset", offset + len(deviations))
        next_cursor = data.get("nextCursor", "")

        logger.info(f"Fetched {len(deviations)} deviations (has_more={has_more})")

        return deviations, has_more, next_offset, next_cursor

    async def fetch_all_deviations(
        self,
        url: str,
        max_items: Optional[int] = None,
    ) -> AsyncIterator[Deviation]:
        """
        Fetch all deviations with pagination.

        Args:
            url: API URL with placeholders
            max_items: Maximum items to fetch (None = unlimited)

        Yields:
            Deviation objects

        Raises:
            APIError: On API error
        """
        offset = self.config.offset
        cursor = ""
        fetched_count = 0

        while True:
            deviations, has_more, offset, cursor = await self.fetch_deviations(
                url, offset, cursor
            )

            for deviation in deviations:
                if max_items and fetched_count >= max_items:
                    return

                yield deviation
                fetched_count += 1

            if not has_more:
                break

    async def get_download_url(
        self, 
        deviation: Deviation, 
        quality: str
    ) -> Optional[HttpUrl]:
        """
        Get download URL for a deviation.

        Args:
            deviation: Deviation object
            quality: Quality level (original/full/preview)

        Returns:
            Download URL or None

        Raises:
            AuthenticationError: If login required
        """
        if not deviation.media:
            return None

        media = deviation.media
        base_uri = str(media.base_uri)
        token = media.token[0] if media.token else ""
        pretty_name = media.pretty_name

        # Original quality - requires download button
        if quality == "original" and deviation.is_downloadable:
            return await self._get_original_url(deviation)

        # Full view
        elif quality == "full" or (quality == "original" and not deviation.is_downloadable):
            return self._get_full_url(media, base_uri, token, pretty_name)

        # Preview
        else:
            return self._get_preview_url(media, base_uri, token, pretty_name)

    async def _get_original_url(self, deviation: Deviation) -> Optional[HttpUrl]:
        """Get original download URL from deviation page"""
        try:
            response = await self._request(str(deviation.url))
            html_content = response.text

            if self.DOWNLOAD_MARKER not in html_content:
                raise AuthenticationError("Download link not found (login required)")

            # Extract download URL
            parts = html_content.split(self.DOWNLOAD_MARKER)[1].split('"')[0]
            download_url = html.unescape(self.DOWNLOAD_MARKER + parts)

            return HttpUrl(download_url)

        except Exception as e:
            logger.error(f"Failed to get original URL: {e}")
            return None

    def _get_full_url(
        self, 
        media: Any, 
        base_uri: str, 
        token: str, 
        pretty_name: str
    ) -> Optional[HttpUrl]:
        """Get full view URL"""
        full_view = media.get_type("fullview")

        if full_view and "c" in full_view:
            url = base_uri + full_view["c"].replace("<prettyName>", pretty_name)
        else:
            url = base_uri

        if token:
            url += f"?token={token}"

        return HttpUrl(url)

    def _get_preview_url(
        self, 
        media: Any, 
        base_uri: str, 
        token: str, 
        pretty_name: str
    ) -> Optional[HttpUrl]:
        """Get preview URL"""
        preview = media.get_type("preview")

        if not preview or "c" not in preview:
            return None

        url = base_uri + preview["c"].replace("<prettyName>", pretty_name)

        if token:
            url += f"?token={token}"

        return HttpUrl(url)

    async def download_file(self, url: HttpUrl) -> bytes:
        """
        Download file content.

        Args:
            url: File URL

        Returns:
            File content as bytes

        Raises:
            APIError: On download failure
        """
        logger.debug(f"Downloading file: {url}")

        try:
            response = await self._request(str(url))
            return response.content
        except Exception as e:
            raise APIError(f"Failed to download file: {e}") from e
