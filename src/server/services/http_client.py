"""
HTTP Client Services with Retry Logic

Provides robust HTTP clients for external API integration with:
- Automatic retry logic with exponential backoff
- Connection pooling and timeout management
- Respectful delays for rate limiting
- Comprehensive error handling and logging
- Simple content extraction from HTML

Classes:
    BaseHTTPClient: Foundation class with retry and configuration
    HackerNewsClient: Specialized client for Hacker News API
    fetch_content: Simple utility for fetching and converting HTML to markdown
"""

import asyncio
from typing import Optional

import httpx
from fastmcp.utilities.logging import get_logger
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from src.server.config.constants import (
    DEFAULT_HEADERS,
    HN_API_BASE,
    HN_API_DELAY,
)
from src.server.config.settings import get_settings


class BaseHTTPClient:
    """
    Base HTTP client with configurable retry logic and connection pooling.

    Provides common functionality for all HTTP clients including:
    - Exponential backoff retry logic
    - Connection pooling configuration
    - Timeout management
    - Error handling patterns
    """

    def __init__(self):
        """Initialize base HTTP client with settings and retry config."""
        self.settings = get_settings()
        self.logger = get_logger(self.__class__.__name__)
        self.timeout = self.settings.http.timeout

        # Configure retry decorator with exponential backoff
        self.retry_decorator = retry(
            stop=stop_after_attempt(self.settings.http.max_retries),
            wait=wait_exponential(
                multiplier=self.settings.http.retry_backoff_factor,
                min=1,  # Minimum wait time
                max=10,  # Maximum wait time
            ),
            retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException)),
            reraise=True,  # Re-raise final exception after all retries
        )

    @property
    def client_config(self) -> dict:
        """
        Get standardized HTTP client configuration.

        Returns:
            dict: Configuration for httpx.AsyncClient with timeouts,
                  redirects, and connection pooling settings
        """
        return {
            "timeout": self.timeout,
            "follow_redirects": True,  # Handle redirects automatically
            "limits": httpx.Limits(
                max_connections=self.settings.http.pool_connections,
                max_keepalive_connections=self.settings.http.pool_maxsize,
            ),
        }


class HackerNewsClient(BaseHTTPClient):
    """
    Specialized client for Hacker News API.

    Provides methods for fetching stories, items, users, and updates
    from the Hacker News Firebase API.

    API Documentation: https://github.com/HackerNews/API
    """

    async def get_story_ids(self, endpoint: str, count: int) -> list[int]:
        """
        Fetch story IDs from a Hacker News category endpoint.

        Args:
            endpoint: HN API endpoint (e.g., 'topstories', 'newstories')
            count: Maximum number of story IDs to return

        Returns:
            list[int]: List of story IDs, limited to requested count

        Raises:
            httpx.HTTPError: If API request fails
        """

        @self.retry_decorator
        async def _fetch():
            async with httpx.AsyncClient(**self.client_config) as client:
                response = await client.get(f"{HN_API_BASE}/{endpoint}.json")
                response.raise_for_status()
                return response.json()[:count]  # Limit to requested count

        try:
            ids = await _fetch()
            self.logger.debug(f"Fetched {len(ids)} story IDs from {endpoint}")
            await asyncio.sleep(HN_API_DELAY)
            return ids
        except Exception as e:
            self.logger.error(f"Failed to fetch story IDs from {endpoint}: {e}")
            raise

    async def get_item(self, item_id: int) -> Optional[dict]:
        """
        Fetch a single item (story, comment, etc.) by ID.

        Args:
            item_id: Hacker News item ID

        Returns:
            Optional[dict]: Item data or None if not found/error
        """

        @self.retry_decorator
        async def _fetch():
            async with httpx.AsyncClient(**self.client_config) as client:
                response = await client.get(f"{HN_API_BASE}/item/{item_id}.json")
                response.raise_for_status()
                return response.json()

        try:
            item = await _fetch()
            if item:
                self.logger.debug(
                    f"Fetched item {item_id}: {item.get('type', 'unknown')}"
                )
            await asyncio.sleep(HN_API_DELAY)
            return item
        except Exception as e:
            self.logger.error(f"Failed to fetch item {item_id}: {e}")
            return None

    async def get_user(self, username: str) -> Optional[dict]:
        """
        Fetch user profile information.

        Args:
            username: Hacker News username

        Returns:
            Optional[dict]: User profile data or None if not found/error
        """

        @self.retry_decorator
        async def _fetch():
            async with httpx.AsyncClient(**self.client_config) as client:
                response = await client.get(f"{HN_API_BASE}/user/{username}.json")
                response.raise_for_status()
                return response.json()

        try:
            user = await _fetch()
            if user:
                self.logger.debug(
                    f"Fetched user profile: {username} (karma: {user.get('karma', 0)})"
                )
            await asyncio.sleep(HN_API_DELAY)
            return user
        except Exception as e:
            self.logger.error(f"Failed to fetch user {username}: {e}")
            return None

    async def get_updates(self) -> dict:
        """
        Fetch recent updates (changed items and profiles).

        Returns:
            dict: Updates data with 'items' and 'profiles' lists
        """

        @self.retry_decorator
        async def _fetch():
            async with httpx.AsyncClient(**self.client_config) as client:
                response = await client.get(f"{HN_API_BASE}/updates.json")
                response.raise_for_status()
                return response.json()

        try:
            updates = await _fetch()
            self.logger.debug(
                f"Fetched HN updates: "
                f"{len(updates.get('items', []))} items, "
                f"{len(updates.get('profiles', []))} profiles"
            )
            await asyncio.sleep(HN_API_DELAY)
            return updates
        except Exception as e:
            self.logger.error(f"Failed to fetch updates: {e}")
            # Return empty structure on error
            return {"items": [], "profiles": []}


async def fetch_content(url: str, max_length: Optional[int] = 5000) -> str:
    """
    Simple utility for fetching content from a URL and converting to markdown.

    Uses html_to_markdown for clean content extraction with automatic
    retry logic and length limiting.

    Args:
        url: URL to fetch content from
        max_length: Maximum content length (default: 5000 chars)

    Returns:
        str: Markdown content, truncated if needed

    Raises:
        httpx.HTTPError: If request fails after retries
    """
    from html_to_markdown import convert_to_markdown

    retries = 2
    logger = get_logger("fetch_content")

    async with httpx.AsyncClient(headers=DEFAULT_HEADERS, timeout=120) as client:
        for attempt in range(1, retries + 1):
            try:
                resp = await client.get(url)
                resp.raise_for_status()
                content = convert_to_markdown(resp.text)

                # Apply length limit if specified
                if max_length and len(content) > max_length:
                    content = content[:max_length] + "... [truncated]"
                logger.debug(f"Fetched content from {url} ({len(content)} chars)")
                return content

            except httpx.HTTPError as exc:
                if attempt == retries:
                    logger.error(
                        f"Failed to fetch content from {url} "
                        f"after {retries} attempts: {exc}"
                    )
                    raise
                logger.warning(f"Attempt {attempt} failed for {url}, retrying: {exc}")
                await asyncio.sleep(0.5 * attempt)
