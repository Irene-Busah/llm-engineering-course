"""
Vector storage management using ChromaDB.

This module manages the persistent ChromaDB client and
the collection used for opportunity embeddings.
"""

import os
import logging
import chromadb


class VectorStore:
    """
    Manages the ChromaDB vector collection.
    """

    COLLECTION_NAME = "opportunities"

    def __init__(self, persist_directory: str = "chroma_db") -> None:
        self.client = chromadb.HttpClient(
            host=os.getenv("CHROMA_HOST", "localhost"),
            port=int(os.getenv("CHROMA_PORT", "8001")),
        )

        self.collection = self.client.get_or_create_collection(
            name=self.COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

        self.logger = logging.getLogger(self.__class__.__name__)

        self.logger.info(
            "Vector store initialized. Collection: %s",
            self.COLLECTION_NAME,
        )


    def add_opportunity(self, opportunity_id: str, document: str, embedding: list[float], metadata: dict,) -> None:

        """
        Store an opportunity and its embedding in ChromaDB.

        Args:
            opportunity_id: Unique ID of the opportunity.
            document: Text representation of the opportunity.
            embedding: Vector representation of the document.
            metadata: Additional opportunity information.
        """
        try:
            self.collection.upsert(
                ids=[opportunity_id],
                documents=[document],
                embeddings=[embedding],
                metadatas=[metadata],
            )

            self.logger.info(
                "Opportunity %s added to vector store.",
                opportunity_id,
            )

        except Exception:
            self.logger.exception(
                "Failed to add opportunity %s to vector store.",
                opportunity_id,
            )
            raise


    def get_collection_count(self) -> int:
        """
        Return the number of opportunities staored in the collection.
        """

        count = self.collection.count()

        self.logger.info('Vector collection currently contains %d records.', count)

        return count


    def search_opportunities(self, query_embedding: list[float], limit: int = 5,) -> dict:
        """
        Search for opportunities using semantic similarity.

        Args:
            query_embedding: Embedding representation of the search query.
            limit: Maximum number of results to return.

        Returns:
            Matching opportunities with their documents, metadata and distances.
        """

        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=limit,
                include=["documents", "metadatas", "distances"],
            )

            self.logger.info(
                "Retrieved %d opportunity matches.",
                len(results["ids"][0]),
            )

            return results

        except Exception:
            self.logger.exception("Failed to search opportunities.")
            raise
    