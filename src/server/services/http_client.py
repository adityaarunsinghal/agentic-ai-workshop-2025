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

import httpx
from fastmcp.utilities.logging import get_logger
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
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
