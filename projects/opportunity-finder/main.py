
"""
Application entry point for the Opportunity Finder.

This module coordinates the opportunity discovery pipeline:
    - Initializes application components.
    - Collects and stores Hacker News posts.
    - Retrieves posts awaiting extraction.
    - Extracts structured job opportunities.
    - Persists opportunities in SQLite.
    - Generates embeddings and indexes opportunities in ChromaDB.
    - Tracks extraction processing status.
"""

import logging
from services.data_collector import HackerNewsDataCollector
from services.post_storage import PostStorage
from database.connection import DatabaseConnection
from database.vector_store import VectorStore
from agents.extraction_agent import OpportunityExtractionAgent
from services.opportunity_service import OpportunityService
from services.embedding_service import EmbeddingService
from services.retrieval_service import RetrievalService
from agents.matching_agent import OpportunityMatchingAgent
from services.resume_service import ResumeService
from services.candidate_service import CandidateService




logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def process_pending_posts(storage: PostStorage, extraction_agent: OpportunityExtractionAgent, opportunity_service: OpportunityService,) -> None:
    """
    Process pending source posts and extract job opportunities.

    Retrieves posts awaiting extraction, processes each post,
    persists extracted opportunities, indexes them in ChromaDB,
    and updates processing status.
    """

    # Temporarily limit processing to one post for testing.
    pending_posts = storage.get_pending_posts()[:1]

    if not pending_posts:
        print("No posts awaiting extraction.")
        return

    print(f"Posts awaiting extraction: {len(pending_posts)}")

    for index, post in enumerate(pending_posts, start=1):
        print(
            f"\nProcessing post {index}/{len(pending_posts)}: "
            f"{post.source_post_id}"
        )

        try:
            storage.update_extraction_status(
                source_post_id=post.source_post_id,
                status="pending",
            )

            result = extraction_agent.extract(post)

            saved_count = opportunity_service.process_extraction(
                result=result,
                post=post,
            )

            storage.update_extraction_status(
                source_post_id=post.source_post_id,
                status="completed",
            )

            print(f"Opportunities saved: {saved_count}")

        except Exception:
            extraction_agent.logger.exception(
                "Failed to process source post %s.",
                post.source_post_id,
            )

            try:
                storage.update_extraction_status(
                    source_post_id=post.source_post_id,
                    status="failed",
                )
            except Exception:
                extraction_agent.logger.exception(
                    "Failed to update extraction status for post %s.",
                    post.source_post_id,
                )


def test_opportunity_indexing(opportunity_service: OpportunityService, embedding_service: EmbeddingService, vector_store: VectorStore,) -> None:
    """
    Test indexing using an opportunity already stored in SQLite.
    """

    opportunity_id = "7bb757ae-0be7-4656-b328-7d3ca706363a"

    opportunity = opportunity_service.get_opportunity(opportunity_id)

    if opportunity is None:
        print("Opportunity not found.")
        return

    embedding_service.index_opportunity(
        opportunity=opportunity,
        vector_store=vector_store,
    )

    print(
        f"Indexed opportunities: "
        f"{vector_store.get_collection_count()}"
    )



def main() -> None:
    """Test candidate onboarding and profile persistence."""

    # Initialize database.
    database = DatabaseConnection()
    database.create_tables()

    # Initialize candidate and resume services.
    candidate_service = CandidateService(database)

    resume_service = ResumeService(
        candidate_service=candidate_service
    )

    print("Database initialized successfully.")

    # Candidate onboarding preferences.
    candidate_preferences = {
        "preferred_roles": ["Backend Engineer", "AI Engineer"],
        "preferred_locations": ["Europe", "United States"],
        "remote_preference": "Remote or Hybrid",
        "visa_sponsorship_required": True,
    }

    # Create and persist candidate profile from resume.
    candidate_profile = resume_service.create_candidate_profile_from_resume(
        file_path="/Users/irenebusah/Downloads/Irene-Busah-Resume.pdf",
        **candidate_preferences,
    )

    print("\nCandidate profile created and saved successfully.")
    print(candidate_profile.model_dump_json(indent=2))

    # Retrieve the saved candidate profile.
    retrieved_profile = candidate_service.get_candidate_profile(
        candidate_profile.candidate_id
    )

    if retrieved_profile is None:
        print("\nCandidate profile retrieval failed.")
        return

    print("\nCandidate profile retrieved successfully.")
    print(retrieved_profile.model_dump_json(indent=2))




if __name__ == "__main__":
    main()
