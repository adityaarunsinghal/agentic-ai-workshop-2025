"""
Application Constants and Configuration Values

Centralized constants for API endpoints, limits, headers, and other
configuration values used throughout the application. Organized by
functional area for easy maintenance and discovery.
"""

# ============= HTTP CLIENT CONFIGURATION =============

# Realistic browser headers
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
}

# ============= HACKER NEWS API CONFIGURATION =============

# Hacker News Firebase API base URL
HN_API_BASE = "https://hacker-news.firebaseio.com/v0"

# Hacker News website base URL
HN_WEBSITE_BASE = "https://news.ycombinator.com"

# Rate limiting delays (in seconds)
HN_API_DELAY = 0.1  # 100ms delay between HN API calls
WEB_SCRAPING_DELAY = 1.0  # 1 second delay for web scraping

# ============= NEWSPAPER LAYOUTS =============

VALID_LAYOUTS = ["grid", "single-column", "featured", "timeline"]

VALID_PLACEMENTS = ["lead", "standard", "sidebar", "quick-read"]

VALID_HIGHLIGHT_TYPES = ["breaking", "trending", "exclusive", "deep-dive"]

VALID_TOC_STYLES = ["compact", "detailed", "visual"]

VALID_EDITORIAL_TONES = ["analytical", "educational", "skeptical", "enthusiastic"]

VALID_SUMMARY_STYLES = ["brief", "balanced", "detailed", "technical"]

# ============= READING TIME CALCULATION =============

WORDS_PER_MINUTE = 200  # Average reading speed

# ============= CHROMADB SETTINGS =============

CHROMA_METADATA = {"hnsw:space": "cosine"}  # Cosine similarity for semantic search
