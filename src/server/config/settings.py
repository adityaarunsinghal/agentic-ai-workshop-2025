"""
Configuration Management System

Pydantic-based configuration system with environment variable support,
validation, and nested settings for different application components.

Features:
- Type-safe configuration with validation
- Environment variable override support (MCP_ prefix)
- Nested settings for logical grouping
- Default value management with constraints
- Singleton pattern for global access
"""

from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class NewsSettings(BaseSettings):
    """
    News fetching and processing configuration.

    Defines defaults for news story limits, summarization styles,
    and supported news sources.
    """

    default_story_count: int = Field(
        default=5, ge=1, le=30, description="Default number of stories to fetch"
    )

    summary_style: str = Field(
        default="brief",
        pattern="^(brief|detailed|technical)$",
        description="Default summarization style for articles",
    )

    sources: list[str] = Field(
        default_factory=lambda: ["hackernews"],
        description="List of enabled news sources",
    )


class HttpSettings(BaseSettings):
    """
    HTTP client configuration for external API calls.

    Controls timeouts, retries, connection pooling, and other
    HTTP client behavior for reliable external service integration.
    """

    timeout: float = Field(
        default=15.0, ge=1.0, le=60.0, description="Request timeout in seconds"
    )

    max_retries: int = Field(
        default=3, ge=0, le=10, description="Maximum number of retry attempts"
    )

    retry_backoff_factor: float = Field(
        default=1.0,
        ge=0.1,
        le=5.0,
        description="Exponential backoff factor for retries",
    )

    pool_connections: int = Field(
        default=10, ge=1, le=100, description="Number of connection pools"
    )

    pool_maxsize: int = Field(
        default=10, ge=1, le=100, description="Maximum number of connections per pool"
    )


class ServerSettings(BaseSettings):
    """
    Main server configuration with nested settings and environment support.

    Provides centralized configuration management with:
    - Environment variable overrides (MCP_ prefix)
    - Nested configuration sections
    - Path management for data directories
    - Logging configuration
    - User preferences integration
    """

    model_config = SettingsConfigDict(
        env_file=".env",  # Load from .env file if present
        env_file_encoding="utf-8",  # UTF-8 encoding for env file
        env_prefix="MCP_",  # Environment variable prefix
        extra="ignore",  # Ignore unknown env vars
    )

    chromadb_path: Path = Field(
        default_factory=lambda: Path(__file__).parent.parent / "data" / "chromadb",
        description="ChromaDB storage directory",
    )

    # ============= Server Identity =============

    server_name: str = Field(
        default="news-agent-mcp-server", description="MCP server name identifier"
    )

    server_version: str = Field(
        default="0.1.0", description="Server version for client compatibility"
    )

    # ============= Directory Paths =============

    config_dir: Path = Field(
        default_factory=lambda: Path(__file__).parent.parent / "config",
        description="Configuration files directory",
    )

    data_dir: Path = Field(
        default_factory=lambda: Path(__file__).parent.parent / "data",
        description="Data storage directory (ChromaDB, etc.)",
    )

    log_dir: Path = Field(
        default_factory=lambda: Path(__file__).parent.parent / "server_logs",
        description="Server log files directory",
    )

    # ============= Nested Configuration Sections =============

    news: NewsSettings = Field(
        default_factory=NewsSettings,
        description="News fetching and processing settings",
    )

    http: HttpSettings = Field(
        default_factory=HttpSettings, description="HTTP client configuration"
    )

    # ============= Logging Configuration =============

    log_level: str = Field(
        default="INFO",
        pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$",
        description="Logging level for server output",
    )

    log_to_file: bool = Field(default=True, description="Enable logging to file")

    log_to_console: bool = Field(default=True, description="Enable logging to console")


# ============= Singleton Pattern =============

# Global settings instance for application-wide access
_settings: Optional[ServerSettings] = None


def get_settings() -> ServerSettings:
    """
    Get or create the global settings singleton instance.

    Implements lazy initialization of the settings object.
    The first call creates the instance, subsequent calls
    return the same instance for consistency.

    Returns:
        ServerSettings: The global settings instance
    """
    global _settings
    if _settings is None:
        _settings = ServerSettings()
    return _settings
