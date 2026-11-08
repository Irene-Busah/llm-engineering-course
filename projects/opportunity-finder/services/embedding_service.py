"""
Embedding service for generating vector representations of opportunities.

This module converts opportunity text into embeddings that can be
stored in Chroma for semantic retrieval.
"""


import logging
from openai import OpenAI
from config import OPENAI_API_KEY
from models.opportunity import Opportunity
from database.vector_store import VectorStore


class EmbeddingService:
    """
    Generates text embeddings using OpenAI.
    """

    MODEL = "text-embedding-3-small"

    def __init__(self, client: OpenAI | None = None) -> None:
        self.client = client
        self.logger = logging.getLogger(self.__class__.__name__)

        self.logger.info(
            "Embedding service initialized using model: %s",
            self.MODEL,
        )


    def generate_embedding(self, text: str) -> list[float]:
        """
        Generate an embedding vector for the provided text.

        Args:
            text: The text to convert into an embedding.

        Returns:
            A list of floating-point values representing the text.
        """
        if not text.strip():
            raise ValueError("Cannot generate an embedding from empty text.")

        try:
            if self.client is None:
                self.client = OpenAI(api_key=OPENAI_API_KEY)

            response = self.client.embeddings.create(
                model=self.MODEL,
                input=text,
            )

            embedding = response.data[0].embedding

            self.logger.info("Successfully generated text embedding.")

            return embedding

        except Exception:
            self.logger.exception("Failed to generate text embedding.")
            raise


    def prepare_opportunity_text(self, opportunity: Opportunity) -> str:
        """
        Prepare opportunity fields as text for embedding generation.
        """
        return (
            f"Company: {opportunity.company or 'Unknown'}\n"
            f"Role: {opportunity.role_title}\n"
            f"Description: {opportunity.description or ''}\n"
            f"Seniority: {opportunity.seniority or ''}\n"
            f"Employment Type: {opportunity.employment_type or ''}\n"
            f"Required Skills: {', '.join(opportunity.required_skills)}\n"
            f"Locations: {', '.join(opportunity.locations)}\n"
            f"Remote Policy: {opportunity.remote_policy.value}\n"
        )

    def index_opportunity(self, opportunity: Opportunity, vector_store: VectorStore,) -> None:
        """
        Generate an embedding and store an opportunity in ChromaDB.
        """
        try:
            document = self.prepare_opportunity_text(opportunity)

            embedding = self.generate_embedding(document)

            metadata = {
                "source_post_id": opportunity.source_post_id,
                "company": opportunity.company or "Unknown",
                "role_title": opportunity.role_title,
                "remote_policy": opportunity.remote_policy.value,
                "visa_sponsorship": opportunity.visa_sponsorship.value,
                "seniority": opportunity.seniority or "Unknown",
                "locations": ", ".join(opportunity.locations),
            }

            vector_store.add_opportunity(
                opportunity_id=opportunity.id,
                document=document,
                embedding=embedding,
                metadata=metadata,
            )

            self.logger.info(
                "Successfully indexed opportunity: %s",
                opportunity.id,
            )

        except Exception:
            self.logger.exception(
                "Failed to index opportunity: %s",
                opportunity.id,
            )
            raise
