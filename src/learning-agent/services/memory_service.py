"""
Memory Service using ChromaDB.

Provides memory storage and semantic search capabilities for the Learning Agent.
"""

import hashlib
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, cast

import chromadb
from chromadb.api import ClientAPI
from chromadb.config import Settings as ChromaSettings

logger = logging.getLogger(__name__)


class MemoryService:
    """
    ChromaDB-based memory service for semantic document storage and retrieval.

    Provides methods for storing, searching, and managing documents with semantic
    embeddings using ChromaDB's built-in embedding models.
    """

    def __init__(self, collection_name: str = "learning_data") -> None:
        """
        Initialize the memory service.

        Args:
            collection_name: Name of the ChromaDB collection to use
        """
        self.collection_name = collection_name
        self.client: ClientAPI | None = None
        self.collection: chromadb.Collection | None = None
        self._initialized = False

    def initialize(self, db_path: Path | None = None) -> None:
        """
        Initialize the ChromaDB client and collection.

        Args:
            db_path: Path to store ChromaDB data. If None, uses ./data/chroma
        """
        if self._initialized:
            logger.debug("Memory service already initialized")
            return

        if db_path is None:
            db_path = Path("./data/chroma")

        db_path.mkdir(parents=True, exist_ok=True)

        logger.info(f"Initializing ChromaDB at {db_path}")

        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(path=str(db_path), settings=ChromaSettings(anonymized_telemetry=False))

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"description": "Learning Agent document storage"},
        )

        self._initialized = True
        logger.info(f"Memory service initialized with collection '{self.collection_name}'")

    def _ensure_initialized(self) -> None:
        """Ensure the memory service is initialized before operations."""
        if not self._initialized or self.collection is None:
            raise RuntimeError("Memory service not initialized. Call initialize() first.")

    def store_document(
        self,
        content: str,
        doc_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Store a document in the memory database.

        Args:
            content: Document content to store
            doc_id: Optional document ID. If None, auto-generated
            metadata: Optional metadata to store with document

        Returns:
            Dict with storage result including doc_id and metadata
        """
        self._ensure_initialized()

        if doc_id is None:
            # Generate ID from content hash and timestamp
            content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
            timestamp = int(datetime.now().timestamp())
            doc_id = f"doc_{content_hash}_{timestamp}"

        # Prepare metadata
        doc_metadata = metadata or {}
        doc_metadata.update({"created_at": datetime.now().isoformat(), "content_length": len(content)})

        # Limit content length for embedding (ChromaDB has limits)
        embedding_content = content[:8000] if len(content) > 8000 else content

        try:
            # Store in ChromaDB
            assert self.collection is not None  # Ensured by _ensure_initialized
            self.collection.add(documents=[embedding_content], metadatas=[doc_metadata], ids=[doc_id])

            logger.info(f"Stored document {doc_id} ({len(content)} chars)")

            return {
                "stored": True,
                "doc_id": doc_id,
                "content_length": len(content),
                "timestamp": doc_metadata["created_at"],
                "metadata": doc_metadata,
            }

        except Exception as e:
            logger.error(f"Failed to store document: {e}")
            return {"stored": False, "error": str(e), "doc_id": doc_id}

    def search_documents(
        self, query: str, limit: int = 10, metadata_filter: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """
        Search for similar documents using semantic similarity.

        Args:
            query: Search query text
            limit: Maximum number of results to return
            metadata_filter: Optional metadata filters to apply

        Returns:
            List of matching documents with similarity scores
        """
        self._ensure_initialized()

        try:
            # Query ChromaDB
            assert self.collection is not None  # Ensured by _ensure_initialized
            results = self.collection.query(query_texts=[query], n_results=limit, where=metadata_filter)

            # Format results
            documents = []
            if results["documents"] and results["documents"][0]:
                docs_list = cast(list[str], results["documents"][0])
                distances_list = (
                    cast(list[float], results["distances"][0])
                    if results["distances"] and results["distances"][0]
                    else []
                )
                metadatas_list = (
                    cast(list[dict[str, Any]], results["metadatas"][0])
                    if results["metadatas"] and results["metadatas"][0]
                    else []
                )
                ids_list = (
                    cast(list[str], results["ids"][0])
                    if results["ids"] and results["ids"][0]
                    else []
                )

                for i, doc in enumerate(docs_list):
                    distance = distances_list[i]

                    doc_data = {
                        "doc_id": ids_list[i] if i < len(ids_list) else None,
                        "content": doc,
                        "content_preview": doc[:200] + "..." if len(doc) > 200 else doc,
                        "metadata": metadatas_list[i] if i < len(metadatas_list) else {},
                        "distance": distance,
                    }
                    documents.append(doc_data)

            # Sort by distance (lower is more similar)
            documents = sorted(documents, key=lambda x: x["distance"])

            logger.info(f"Search for '{query}' returned {len(documents)} results")
            return documents

        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

    def get_document(self, doc_id: str) -> dict[str, Any] | None:
        """
        Retrieve a specific document by ID.

        Args:
            doc_id: Document ID to retrieve

        Returns:
            Document data if found, None otherwise
        """
        self._ensure_initialized()

        try:
            assert self.collection is not None  # Ensured by _ensure_initialized
            results = self.collection.get(ids=[doc_id])

            if results["documents"] and results["documents"][0]:
                return {
                    "doc_id": doc_id,
                    "content": results["documents"][0],
                    "metadata": results["metadatas"][0] if results["metadatas"] else {},
                }

            return None

        except Exception as e:
            logger.error(f"Failed to get document {doc_id}: {e}")
            return None

    def delete_document(self, doc_id: str) -> bool:
        """
        Delete a document by ID.

        Args:
            doc_id: Document ID to delete

        Returns:
            True if deleted successfully, False otherwise
        """
        self._ensure_initialized()

        try:
            assert self.collection is not None  # Ensured by _ensure_initialized
            self.collection.delete(ids=[doc_id])
            logger.info(f"Deleted document {doc_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete document {doc_id}: {e}")
            return False

    def get_collection_stats(self) -> dict[str, Any]:
        """
        Get statistics about the document collection.

        Returns:
            Dict with collection statistics
        """
        self._ensure_initialized()

        try:
            assert self.collection is not None  # Ensured by _ensure_initialized
            count = self.collection.count()

            # Get sample of documents to calculate average length
            sample_results = self.collection.get(limit=min(100, count))
            total_length = 0

            if sample_results["metadatas"]:
                metadatas_list = cast(list[dict[str, Any] | None], sample_results["metadatas"])
                for metadata in metadatas_list:
                    if metadata and "content_length" in metadata:
                        content_length = metadata["content_length"]
                        if isinstance(content_length, (int, float)):
                            total_length += int(content_length)

            avg_length = total_length // len(sample_results["metadatas"]) if sample_results["metadatas"] else 0

            return {
                "collection_name": self.collection_name,
                "total_documents": count,
                "total_content_length": total_length,
                "avg_content_length": avg_length,
                "initialized": self._initialized,
            }

        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            return {
                "collection_name": self.collection_name,
                "total_documents": 0,
                "total_content_length": 0,
                "avg_content_length": 0,
                "initialized": self._initialized,
                "error": str(e),
            }

    def cleanup_old_documents(self, max_age_days: int = 90) -> dict[str, Any]:
        """
        Remove documents older than the specified age.

        Args:
            max_age_days: Maximum age in days for documents to keep

        Returns:
            Dict with cleanup results
        """
        self._ensure_initialized()

        try:
            cutoff_date = datetime.now() - timedelta(days=max_age_days)
            cutoff_iso = cutoff_date.isoformat()

            # Get all documents
            assert self.collection is not None  # Ensured by _ensure_initialized
            all_docs = self.collection.get()
            old_doc_ids = []

            if all_docs["metadatas"]:
                metadatas_list = cast(list[dict[str, Any] | None], all_docs["metadatas"])
                ids_list = cast(list[str], all_docs["ids"])
                for i, metadata in enumerate(metadatas_list):
                    if metadata and "created_at" in metadata:
                        created_at = metadata["created_at"]
                        if isinstance(created_at, str) and created_at < cutoff_iso:
                            old_doc_ids.append(ids_list[i])

            # Delete old documents
            if old_doc_ids:
                self.collection.delete(ids=old_doc_ids)
                logger.info(f"Cleaned up {len(old_doc_ids)} old documents")

            return {
                "removed": len(old_doc_ids),
                "cutoff_date": cutoff_iso,
                "max_age_days": max_age_days,
            }

        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
            return {"removed": 0, "error": str(e)}

    def close(self) -> None:
        """
        Close the ChromaDB client and clean up resources.

        This should be called when the service is no longer needed,
        especially in test scenarios to prevent file handle leaks.
        """
        if self.client is not None:
            try:
                # Reset the collection and client references
                self.collection = None

                # ChromaDB doesn't have an explicit close method,
                # but we can reset our references to help garbage collection
                self.client = None
                self._initialized = False

                logger.debug("Memory service closed")
            except Exception as e:
                logger.warning(f"Error during memory service cleanup: {e}")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        self.close()
