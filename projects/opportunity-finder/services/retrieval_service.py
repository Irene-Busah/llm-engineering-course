
import logging

from services.embedding_service import EmbeddingService
from database.vector_store import VectorStore
from services.opportunity_service import OpportunityService
from models.opportunity import Opportunity


class RetrievalService:
    """
    Service responsible for retrieving relevant opportunities
    using semantic search.
    """

    def __init__(
        self,
        embedding_service: EmbeddingService,
        vector_store: VectorStore,
        opportunity_service: OpportunityService,
    ) -> None:
        self.embedding_service = embedding_service
        self.vector_store = vector_store
        self.opportunity_service = opportunity_service

        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("Retrieval service initialized.")

    def search_opportunities(
        self,
        query: str,
        limit: int = 5,
    ) -> list[Opportunity]:
        """
        Retrieve semantically relevant opportunities.

        Args:
            query: Natural-language search query.
            limit: Maximum number of opportunities to return.

        Returns:
            Opportunity objects ordered by semantic similarity.
        """

        if not query.strip():
            raise ValueError("Search query cannot be empty.")

        if limit < 1:
            raise ValueError("Search limit must be at least 1.")

        try:
            self.logger.info("Searching opportunities")

            query_embedding = self.embedding_service.generate_embedding(query)

            candidate_limit = limit * 4

            results = self.vector_store.search_opportunities(
                query_embedding=query_embedding,
                limit=candidate_limit,
            )

            opportunity_ids = results["ids"][0]

            opportunities = self.opportunity_service.get_opportunities_by_ids(
                opportunity_ids=opportunity_ids,
            )

            opportunities_by_id = {
                opportunity.id: opportunity
                for opportunity in opportunities
            }

            ranked_opportunities = [
                opportunities_by_id[opportunity_id]
                for opportunity_id in opportunity_ids
                if opportunity_id in opportunities_by_id
            ]

            # ranked_opportunities = ranked_opportunities[:limit]

            self.logger.info(
                "Search completed. Retrieved %d opportunities.",
                len(ranked_opportunities),
            )

            return ranked_opportunities

        except Exception:
            self.logger.exception("Opportunity search failed.")
            raise
