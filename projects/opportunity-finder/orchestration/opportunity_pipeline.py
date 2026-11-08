
import logging

from prefect import flow, task, get_run_logger
from prefect.schedules import Cron

from agents.extraction_agent import OpportunityExtractionAgent
from database.connection import DatabaseConnection
from database.vector_store import VectorStore
from services.data_collector import HackerNewsDataCollector
from services.embedding_service import EmbeddingService
from services.opportunity_service import OpportunityService
from services.post_storage import PostStorage


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def create_opportunity_service() -> OpportunityService:
    """Initialize the dependencies required by OpportunityService."""

    database = DatabaseConnection()
    embedding_service = EmbeddingService()
    vector_store = VectorStore()

    return OpportunityService(
        database=database,
        embedding_service=embedding_service,
        vector_store=vector_store,
    )


@task(name="Initialize Database")
def initialize_database() -> None:
    logger = get_run_logger()

    database = DatabaseConnection()
    database.create_tables()

    logger.info("Database initialized successfully.")


@task(
    name="Collect HackerNews Posts",
    retries=2,
    retry_delay_seconds=60,
)
def collect_posts(limit: int = 1) -> list:
    logger = get_run_logger()

    collector = HackerNewsDataCollector()

    try:
        posts = collector.collect_posts(limit=limit)
        logger.info("Retrieved %d posts from HackerNews.", len(posts))
        return posts
    finally:
        collector.client.close()


@task(name="Store New Posts")
def store_posts(posts: list) -> int:
    logger = get_run_logger()

    storage = PostStorage()
    saved_count = storage.save_posts(posts)

    logger.info("Saved %d new source posts.", saved_count)

    return saved_count


@task(name="Get Pending Posts")
def get_pending_posts() -> list:
    logger = get_run_logger()

    storage = PostStorage()
    posts = storage.get_pending_posts()

    logger.info("%d posts are awaiting extraction.", len(posts))

    return posts


@task(
    name="Extract Opportunity From Post",
    retries=2,
    retry_delay_seconds=60,
)
def extract_post(post) -> int:
    logger = get_run_logger()
    storage = PostStorage()

    try:
        storage.update_extraction_status(
            source_post_id=post.source_post_id,
            status="pending",
        )

        extraction_agent = OpportunityExtractionAgent()
        opportunity_service = create_opportunity_service()

        result = extraction_agent.extract(post)

        saved_count = opportunity_service.process_extraction(
            result=result,
            post=post,
        )

        storage.update_extraction_status(
            source_post_id=post.source_post_id,
            status="completed",
        )

        logger.info(
            "Post %s processed. Opportunities saved: %d",
            post.source_post_id,
            saved_count,
        )

        return saved_count

    except Exception:
        logger.exception(
            "Extraction failed for source post %s.",
            post.source_post_id,
        )

        try:
            storage.update_extraction_status(
                source_post_id=post.source_post_id,
                status="failed",
            )
        except Exception:
            logger.exception(
                "Could not update extraction status for post %s.",
                post.source_post_id,
            )

        raise


@task(name="Index Pending Opportunities")
def index_opportunities() -> dict:
    logger = get_run_logger()

    opportunity_service = create_opportunity_service()

    indexed_count = opportunity_service.index_pending_opportunities()
    remaining_count = len(
        opportunity_service.get_unindexed_opportunities()
    )

    logger.info(
        "Indexing completed. Indexed: %d. Remaining: %d.",
        indexed_count,
        remaining_count,
    )

    return {
        "indexed": indexed_count,
        "remaining": remaining_count,
    }


@task(name="Clean Up Expired Source Posts")
def cleanup_expired_posts() -> int:
    logger = get_run_logger()

    storage = PostStorage()
    deleted_count = storage.delete_expired_posts(retention_days=30)

    logger.info("Deleted %d expired source posts.", deleted_count)

    return deleted_count


@flow(name="Opportunity Collection Pipeline")
def opportunity_collection_flow(limit: int = 1) -> dict:
    logger = get_run_logger()

    # 1. Ensure the database schema exists.
    initialize_database()

    # 2. Collect and persist new source posts.
    posts = collect_posts(limit=limit)
    saved_posts = store_posts(posts)

    # 3. Retrieve all posts that need extraction.
    pending_posts = get_pending_posts()

    extracted_posts = 0
    failed_posts = 0
    saved_opportunities = 0

    # 4. Process each post independently.
    for post in pending_posts:
        try:
            saved_opportunities += extract_post(post)
            extracted_posts += 1
        except Exception:
            # One failed post should not stop the remaining posts.
            failed_posts += 1
            logger.exception(
                "Skipping failed post %s and continuing.",
                post.source_post_id,
            )

    # 5. Index all opportunities that have not yet been indexed.
    indexing_summary = index_opportunities()

    # 6. Apply raw-post retention after processing.
    deleted_posts = cleanup_expired_posts()

    summary = {
        "posts_retrieved": len(posts),
        "posts_saved": saved_posts,
        "posts_processed": extracted_posts,
        "posts_failed": failed_posts,
        "opportunities_saved": saved_opportunities,
        "opportunities_indexed": indexing_summary["indexed"],
        "opportunities_awaiting_indexing": indexing_summary["remaining"],
        "expired_posts_deleted": deleted_posts,
    }

    logger.info("Pipeline completed: %s", summary)

    return summary


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--serve",
        action="store_true",
        help="Start the scheduled opportunity collection pipeline.",
    )

    args = parser.parse_args()

    if args.serve:
        opportunity_collection_flow.serve(
            name="opportunity-collection-local",
            schedules=[
                Cron(
                    "0 */6 * * *",
                    timezone="Africa/Kigali",
                )
            ],
            pause_on_shutdown=False,
        )
    else:
        opportunity_collection_flow()
