"""
Article and Newspaper Memory Service using ChromaDB

Enhanced with content ID system for clean references and context management.

Features:
- Content ID system (cnt_source_date_hash) for easy reference
- Persistent vector storage with ChromaDB
- Semantic similarity search
- Automatic cleanup (60 days, 500 items per collection)
- Context summary generation
"""

from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import chromadb
from chromadb.api.models.Collection import Collection
from fastmcp.utilities.logging import get_logger


class ArticleMemoryService:
    """
    Dual-collection memory service for articles and newspapers with content ID support.
    """

    def __init__(self):
        """Initialize memory service with logging and state tracking."""
        self.logger = get_logger("ArticleMemoryService")
        self.client = None
        self.article_collection: Optional[Collection] = None
        self.newspaper_collection: Optional[Collection] = None
        self._initialized = False

        # Configuration
        self.max_items_per_collection = 500
        self.max_age_days = 60

    def initialize(self, db_path: Path) -> None:
        """
        Initialize ChromaDB with two collections.

        Args:
            db_path: Path to ChromaDB storage directory
        """
        if self._initialized:
            self.logger.debug("ChromaDB already initialized")
            return

        try:
            # Ensure directory exists
            db_path.mkdir(parents=True, exist_ok=True)

            # Initialize ChromaDB client
            self.client = chromadb.PersistentClient(path=str(db_path))
            self.logger.debug(f"ChromaDB client initialized at {db_path}")

            # Create/get collections
            self.article_collection = self.client.get_or_create_collection(
                name="article_archive", metadata={"hnsw:space": "cosine"}
            )

            self.newspaper_collection = self.client.get_or_create_collection(
                name="newspaper_archive", metadata={"hnsw:space": "cosine"}
            )

            self.logger.debug("Collections ready: article_archive, newspaper_archive")

            # Cleanup old items
            self._cleanup_old_items()

            self.logger.info("Article memory service initialized successfully")
            self._initialized = True

        except Exception as e:
            self.logger.error(f"Failed to initialize article memory: {e}")
            raise

    # ============= ARTICLE STORAGE WITH CONTENT IDS =============

    def store_article_with_content_id(
        self,
        content_id: str,
        url: str,
        content: str,
        title: str = "",
        source: str = "web",
        topics: List[str] = None,
        summary: str = "",
        metadata: Dict = None,
    ) -> Dict:
        """
        Store article with content ID for easy reference.

        Args:
            content_id: Clean content ID (e.g., cnt_hn_20251005_1234)
            url: Article URL
            content: Full article content
            title: Article title
            source: Source (hn, web, arxiv, etc.)
            topics: List of topic tags
            summary: Brief summary
            metadata: Additional metadata dict

        Returns:
            Dict with storage confirmation
        """
        timestamp = datetime.now().isoformat()
        topics = topics or []
        metadata = metadata or {}

        try:
            # Prepare metadata
            meta = {
                "content_id": content_id,
                "url": url,
                "title": title,
                "source": source,
                "topics": ",".join(topics),
                "summary": summary,
                "timestamp": timestamp,
                "word_count": len(content.split()),
                "reading_time": max(1, len(content.split()) // 200),
                **metadata,
            }

            # Store with embedding (limit content for embedding)
            self.article_collection.add(
                documents=[content[:8000]], metadatas=[meta], ids=[content_id]
            )

            self.logger.debug(f"Stored article with content_id: {content_id}")

            return {
                "success": True,
                "content_id": content_id,
                "url": url,
                "title": title,
                "timestamp": timestamp,
            }

        except Exception as e:
            self.logger.error(f"Failed to store article '{title}': {e}")
            return {"success": False, "error": str(e), "content_id": content_id}

    def get_by_content_id(self, content_id: str) -> Optional[Dict]:
        """
        Retrieve article by content ID.

        Args:
            content_id: Content ID to retrieve

        Returns:
            Article dict with content and metadata, or None if not found
        """
        try:
            results = self.article_collection.get(ids=[content_id])

            if not results["documents"]:
                return None

            metadata = results["metadatas"][0]
            content = results["documents"][0]

            return {
                "content_id": content_id,
                "title": metadata.get("title", "Unknown"),
                "url": metadata.get("url", ""),
                "source": metadata.get("source", "unknown"),
                "topics": (
                    metadata.get("topics", "").split(",")
                    if metadata.get("topics")
                    else []
                ),
                "summary": metadata.get("summary", ""),
                "timestamp": metadata.get("timestamp", ""),
                "word_count": metadata.get("word_count", 0),
                "reading_time": metadata.get("reading_time", 0),
                "content": content,
                "content_preview": content[:300] + "...",
            }

        except Exception as e:
            self.logger.error(f"Failed to get content by ID '{content_id}': {e}")
            return None

    # ============= LEGACY STORAGE (for backwards compatibility) =============

    def store_article(
        self,
        url: str,
        content: str,
        title: str = "",
        source: str = "web",
        topics: List[str] = None,
        summary: str = "",
        metadata: Dict = None,
    ) -> Dict:
        """
        Legacy storage method - generates content_id automatically.

        For new code, use store_article_with_content_id instead.
        """
        # Generate content ID
        timestamp = datetime.now()
        content_id = (
            f"cnt_{source}_{timestamp.strftime('%Y%m%d')}_{abs(hash(url))%10000:04d}"
        )

        return self.store_article_with_content_id(
            content_id=content_id,
            url=url,
            content=content,
            title=title,
            source=source,
            topics=topics,
            summary=summary,
            metadata=metadata,
        )

    # ============= SEARCH =============

    def search_articles(
        self,
        query: str,
        limit: int = 5,
        source_filter: str = None,
        topic_filter: str = None,
    ) -> List[Dict]:
        """
        Semantic search for related articles.

        Args:
            query: Search query
            limit: Maximum results
            source_filter: Filter by source
            topic_filter: Filter by topic

        Returns:
            List of matching articles with similarity scores
        """
        try:
            # Build where clause
            where = {}
            if source_filter:
                where["source"] = source_filter
            if topic_filter:
                where["topics"] = {"$contains": topic_filter}

            # Query collection
            results = self.article_collection.query(
                query_texts=[query], n_results=limit, where=where if where else None
            )

            if not results["documents"] or not results["documents"][0]:
                return []

            # Format results
            articles = []
            for i, metadata in enumerate(results["metadatas"][0]):
                article = {
                    "content_id": metadata.get("content_id", ""),
                    "url": metadata.get("url", ""),
                    "title": metadata.get("title", "Unknown"),
                    "source": metadata.get("source", "unknown"),
                    "topics": (
                        metadata.get("topics", "").split(",")
                        if metadata.get("topics")
                        else []
                    ),
                    "summary": metadata.get("summary", ""),
                    "timestamp": metadata.get("timestamp", ""),
                    "word_count": metadata.get("word_count", 0),
                    "reading_time": metadata.get("reading_time", 0),
                    "content_preview": results["documents"][0][i][:200] + "...",
                    "similarity": (
                        1 - results["distances"][0][i]
                        if results["distances"] and results["distances"][0]
                        else 0
                    ),
                }
                articles.append(article)

            return articles

        except Exception as e:
            self.logger.error(f"Article search failed for '{query}': {e}")
            return []

    # ============= CONTEXT SUMMARY =============

    def get_context_summary(self) -> Dict:
        """
        Get live summary of archive state.

        Returns:
            Dict with recent newspapers, trending topics, coverage stats
        """
        try:
            article_count = self.article_collection.count()
            newspaper_count = self.newspaper_collection.count()

            # Get recent newspapers
            recent_newspapers = self.search_newspapers(days_back=30)[:5]
            recent_papers_formatted = [
                {
                    "title": p["title"],
                    "date": p["timestamp"][:10],
                    "reading_time": p["reading_time"],
                    "article_count": p["article_count"],
                }
                for p in recent_newspapers
            ]

            # Get topic distribution
            article_results = self.article_collection.get()
            topic_counts = {}

            if article_results["metadatas"]:
                for meta in article_results["metadatas"]:
                    topics = meta.get("topics", "").split(",")
                    for topic in topics:
                        if topic:
                            topic_counts[topic] = topic_counts.get(topic, 0) + 1

            # Sort topics by frequency
            trending_topics = sorted(
                topic_counts.items(), key=lambda x: x[1], reverse=True
            )[:10]

            # Get last article date
            last_article_date = "Never"
            if article_results["metadatas"]:
                timestamps = [
                    m.get("timestamp", "") for m in article_results["metadatas"]
                ]
                if timestamps:
                    last_article_date = max(timestamps)[:10]

            return {
                "total_articles": article_count,
                "total_newspapers": newspaper_count,
                "recent_newspapers": recent_papers_formatted,
                "trending_topics": trending_topics,
                "last_article_date": last_article_date,
            }

        except Exception as e:
            self.logger.error(f"Failed to get context summary: {e}")
            return {
                "total_articles": 0,
                "total_newspapers": 0,
                "recent_newspapers": [],
                "trending_topics": [],
                "last_article_date": "Unknown",
            }

    # ============= NEWSPAPER STORAGE =============

    def store_newspaper(self, newspaper_id: str, newspaper_data: Dict) -> Dict:
        """
        Store complete newspaper in archive.

        Args:
            newspaper_id: Unique newspaper ID
            newspaper_data: Complete newspaper structure

        Returns:
            Dict with storage confirmation
        """
        try:
            # Create searchable text from newspaper
            sections_text = []
            total_articles = 0
            total_reading_time = 0

            for section in newspaper_data.get("sections", []):
                section_title = section.get("title", "")
                sections_text.append(f"Section: {section_title}")

                for article in section.get("articles", []):
                    article_title = article.get("title", "")
                    article_content = article.get("content", "")[:500]
                    sections_text.append(f"{article_title}: {article_content}")

                    # Count articles and reading time
                    total_articles += 1
                    total_reading_time += article.get("format", {}).get(
                        "reading_time", 0
                    )

            searchable_text = "\n".join(sections_text)

            # Prepare metadata - RECALCULATE article_count and reading_time
            metadata = {
                "newspaper_id": newspaper_id,
                "title": newspaper_data.get("title", ""),
                "edition_type": newspaper_data.get("edition_type", "standard"),
                "timestamp": newspaper_data.get("metadata", {}).get(
                    "created_at", datetime.now().isoformat()
                ),
                "article_count": total_articles,  # Use calculated value
                "topics": ",".join(
                    newspaper_data.get("metadata", {}).get("topics", [])
                ),
                "tone": newspaper_data.get("metadata", {}).get("tone", ""),
                "reading_time": total_reading_time,  # Use calculated value
            }

            # Store with embedding
            self.newspaper_collection.add(
                documents=[searchable_text[:8000]],
                metadatas=[metadata],
                ids=[newspaper_id],
            )

            self.logger.info(
                f"Stored newspaper: {newspaper_id} ({total_articles} articles, "
                f"{total_reading_time} min)"
            )

            return {
                "success": True,
                "newspaper_id": newspaper_id,
                "timestamp": metadata["timestamp"],
                "article_count": total_articles,
                "reading_time": total_reading_time,
            }

        except Exception as e:
            self.logger.error(f"Failed to store newspaper '{newspaper_id}': {e}")
            return {"success": False, "error": str(e), "newspaper_id": newspaper_id}

    def search_newspapers(self, days_back: int = 7, query: str = None) -> List[Dict]:
        """
        Search or list past newspapers.

        Args:
            days_back: How many days back to search
            query: Optional semantic search query

        Returns:
            List of matching newspapers
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days_back)

            if query:
                # Semantic search - get all results, filter by date in Python
                results = self.newspaper_collection.query(
                    query_texts=[query],
                    n_results=50,  # Get more results to filter
                )
            else:
                # Just get all
                results = self.newspaper_collection.get()

            if not results["metadatas"]:
                return []

            # Format results
            newspapers = []
            metadatas = (
                results["metadatas"]
                if isinstance(results["metadatas"], list)
                else results["metadatas"]
            )

            # Handle both query results (nested) and get results (flat)
            if metadatas and isinstance(metadatas[0], list):
                metadatas = metadatas[0]

            for metadata in metadatas:
                # Parse timestamp and filter by date in Python
                timestamp_str = metadata.get("timestamp", "")
                try:
                    timestamp = datetime.fromisoformat(timestamp_str)
                    if timestamp < cutoff_date:
                        continue  # Skip old newspapers
                except (ValueError, TypeError):
                    continue  # Skip if timestamp is invalid

                newspaper = {
                    "newspaper_id": metadata.get("newspaper_id", ""),
                    "title": metadata.get("title", ""),
                    "edition_type": metadata.get("edition_type", ""),
                    "timestamp": metadata.get("timestamp", ""),
                    "article_count": metadata.get("article_count", 0),
                    "topics": (
                        metadata.get("topics", "").split(",")
                        if metadata.get("topics")
                        else []
                    ),
                    "tone": metadata.get("tone", ""),
                    "reading_time": metadata.get("reading_time", 0),
                }
                newspapers.append(newspaper)

            # Sort by timestamp (newest first)
            newspapers.sort(key=lambda x: x["timestamp"], reverse=True)

            self.logger.debug(f"Found {len(newspapers)} newspapers")
            return newspapers

        except Exception as e:
            self.logger.error(f"Newspaper search failed: {e}")
            return []

    # ============= STATISTICS =============

    def get_stats(self) -> Dict:
        """Get statistics about both collections."""
        try:
            article_count = self.article_collection.count()
            newspaper_count = self.newspaper_collection.count()

            # Get article stats
            article_results = self.article_collection.get()
            article_sources = {}
            article_topics = {}

            if article_results["metadatas"]:
                for meta in article_results["metadatas"]:
                    # Source breakdown
                    source = meta.get("source", "unknown")
                    article_sources[source] = article_sources.get(source, 0) + 1

                    # Topic breakdown
                    topics = meta.get("topics", "").split(",")
                    for topic in topics:
                        if topic:
                            article_topics[topic] = article_topics.get(topic, 0) + 1

            return {
                "article_archive": {
                    "total": article_count,
                    "sources": article_sources,
                    "top_topics": dict(
                        sorted(
                            article_topics.items(), key=lambda x: x[1], reverse=True
                        )[:10]
                    ),
                },
                "newspaper_archive": {"total": newspaper_count},
                "limits": {
                    "max_items_per_collection": self.max_items_per_collection,
                    "max_age_days": self.max_age_days,
                },
            }

        except Exception as e:
            self.logger.error(f"Failed to get stats: {e}")
            return {"error": str(e)}

    # ============= CLEANUP =============

    def _cleanup_old_items(self) -> None:
        """Clean up old items in both collections."""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.max_age_days)

            # Cleanup articles
            article_results = self.article_collection.get()
            if article_results["ids"]:
                old_article_ids = []
                for i, meta in enumerate(article_results["metadatas"]):
                    timestamp_str = meta.get("timestamp", "")
                    try:
                        timestamp = datetime.fromisoformat(timestamp_str)
                        if timestamp < cutoff_date:
                            old_article_ids.append(article_results["ids"][i])
                    except (ValueError, TypeError):
                        continue

                if old_article_ids:
                    self.article_collection.delete(ids=old_article_ids)
                    self.logger.info(f"Cleaned up {len(old_article_ids)} old articles")

            # Cleanup newspapers
            newspaper_results = self.newspaper_collection.get()
            if newspaper_results["ids"]:
                old_newspaper_ids = []
                for i, meta in enumerate(newspaper_results["metadatas"]):
                    timestamp_str = meta.get("timestamp", "")
                    try:
                        timestamp = datetime.fromisoformat(timestamp_str)
                        if timestamp < cutoff_date:
                            old_newspaper_ids.append(newspaper_results["ids"][i])
                    except (ValueError, TypeError):
                        continue

                if old_newspaper_ids:
                    self.newspaper_collection.delete(ids=old_newspaper_ids)
                    self.logger.info(
                        f"Cleaned up {len(old_newspaper_ids)} old newspapers"
                    )

            # Enforce size limits
            self._enforce_size_limits()

        except Exception as e:
            self.logger.error(f"Cleanup failed: {e}")

    def _enforce_size_limits(self) -> None:
        """Enforce maximum collection sizes by removing oldest items."""
        try:
            # Check article collection
            article_count = self.article_collection.count()
            if article_count > self.max_items_per_collection:
                excess = article_count - self.max_items_per_collection
                article_results = self.article_collection.get()

                # Sort by timestamp (oldest first)
                items_with_time = [
                    (meta.get("timestamp", ""), article_results["ids"][i])
                    for i, meta in enumerate(article_results["metadatas"])
                ]
                items_with_time.sort(key=lambda x: x[0])

                # Remove oldest
                oldest_ids = [item[1] for item in items_with_time[:excess]]
                self.article_collection.delete(ids=oldest_ids)
                self.logger.info(
                    f"Removed {len(oldest_ids)} oldest articles to enforce size limit"
                )

            # Check newspaper collection
            newspaper_count = self.newspaper_collection.count()
            if newspaper_count > self.max_items_per_collection:
                excess = newspaper_count - self.max_items_per_collection
                newspaper_results = self.newspaper_collection.get()

                # Sort by timestamp (oldest first)
                items_with_time = [
                    (meta.get("timestamp", ""), newspaper_results["ids"][i])
                    for i, meta in enumerate(newspaper_results["metadatas"])
                ]
                items_with_time.sort(key=lambda x: x[0])

                # Remove oldest
                oldest_ids = [item[1] for item in items_with_time[:excess]]
                self.newspaper_collection.delete(ids=oldest_ids)
                self.logger.info(
                    f"Removed {len(oldest_ids)} oldest newspapers to enforce size limit"
                )

        except Exception as e:
            self.logger.error(f"Size limit enforcement failed: {e}")
