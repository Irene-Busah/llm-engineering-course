import json
import logging
from pathlib import Path
from datetime import datetime, timedelta, timezone

from models.post import SourcePost


class PostStorage:
    """
    Handles local storage and retention of raw source posts.

    Posts are stored in JSONL format and retained for 30 days.
    """

    def __init__(self, storage_dir: str = "data/raw") -> None:
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        self.file_path = self.storage_dir / "hackernews_posts.jsonl"
        self.logger = logging.getLogger(self.__class__.__name__)

        self.logger.info("Post storage initialized.")

        self.status_dir = Path("data/processing")
        self.status_dir.mkdir(parents=True, exist_ok=True)

        self.status_file_path = self.status_dir / "post_extraction_status.jsonl"


    def save_posts(self, posts: list[SourcePost]) -> int:
        """
        Save new source posts to the JSONL file.

        Existing posts are identified by their source_post_id
        and are not saved again.

        Args:
            posts: List of validated SourcePost objects.

        Returns:
            Number of new posts saved.
        """
        if not posts:
            self.logger.info("No posts to save.")
            return 0

        # Identify posts that are already stored.
        existing_posts = self.load_posts()
        existing_ids = {post.source_post_id for post in existing_posts}

        new_posts = []

        for post in posts:
            if post.source_post_id not in existing_ids:
                new_posts.append(post)
                existing_ids.add(post.source_post_id)

        if not new_posts:
            self.logger.info("No new posts to save. All posts already exist.")
            return 0

        # Append only new posts.
        with self.file_path.open("a", encoding="utf-8") as file:
            for post in new_posts:
                post_data = post.model_dump(mode="json")
                file.write(json.dumps(post_data) + "\n")

        self.logger.info("Saved %d new posts.", len(new_posts))

        return len(new_posts)


    def load_posts(self) -> list[SourcePost]:
        """
        Load saved posts from the JSONL file.

        Each JSON line is converted back into a validated
        SourcePost object.

        Returns:
            List of loaded SourcePost objects.
        """
        if not self.file_path.exists():
            self.logger.warning("No saved posts file found.")
            return []

        posts = []

        with self.file_path.open("r", encoding="utf-8") as file:
            for line_number, line in enumerate(file, start=1):
                if not line.strip():
                    continue

                try:
                    post_data = json.loads(line)
                    post = SourcePost.model_validate(post_data)
                    posts.append(post)

                except (json.JSONDecodeError, ValueError):
                    self.logger.exception(
                        "Failed to load post at line %d.", line_number
                    )

        self.logger.info("Loaded %d posts from %s.", len(posts), self.file_path)

        return posts


    
    def get_post_by_id(self, source_post_id: str) -> SourcePost | None:
        """
        Retrieve a source post by its unique ID.

        Returns:
            The matching SourcePost if available, otherwise None.
        """
        if not source_post_id.strip():
            raise ValueError("source_post_id cannot be empty.")

        if not self.file_path.exists():
            self.logger.info("Original posts file is unavailable.")
            return None

        with self.file_path.open("r", encoding="utf-8") as file:
            for line_number, line in enumerate(file, start=1):
                if not line.strip():
                    continue

                try:
                    post_data = json.loads(line)

                    if post_data.get("source_post_id") == source_post_id:
                        post = SourcePost.model_validate(post_data)

                        self.logger.info(
                            "Found original post: %s",
                            source_post_id,
                        )

                        return post

                except (json.JSONDecodeError, ValueError):
                    self.logger.exception(
                        "Failed to read post at line %d.",
                        line_number,
                    )

        self.logger.info(
            "Original post %s is no longer available.",
            source_post_id,
        )

        return None



    def delete_expired_posts(self, retention_days: int = 30) -> int:
        """
        Delete posts older than the specified retention period.

        Args:
            retention_days: Number of days to retain collected posts.

        Returns:
            Number of posts deleted.
        """
        if retention_days < 1:
            raise ValueError("retention_days must be at least 1.")

        posts = self.load_posts()

        cutoff_date = datetime.now(timezone.utc) - timedelta(days=retention_days)

        # Read the latest extraction status for every source post.
        latest_status = {}

        if self.status_file_path.exists():
            with self.status_file_path.open("r", encoding="utf-8") as file:
                for line_number, line in enumerate(file, start=1):
                    if not line.strip():
                        continue

                    try:
                        status_data = json.loads(line)
                        latest_status[status_data["source_post_id"]] = (
                            status_data["status"]
                        )
                    except (json.JSONDecodeError, KeyError):
                        self.logger.exception(
                            "Invalid extraction status at line %d.",
                            line_number,
                        )

        # Keep recent posts and all posts that have not completed extraction.
        retained_posts = [
            post
            for post in posts
            if (
                post.fetched_at >= cutoff_date
                or latest_status.get(post.source_post_id) != "completed"
            )
        ]

        deleted_count = len(posts) - len(retained_posts)

        if deleted_count == 0:
            self.logger.info("No expired posts found.")
            return 0

        with self.file_path.open("w", encoding="utf-8") as file:
            for post in retained_posts:
                post_data = post.model_dump(mode="json")
                file.write(json.dumps(post_data) + "\n")

        self.logger.info("Deleted %d expired posts.", deleted_count)

        return deleted_count


    def get_pending_posts(self) -> list[SourcePost]:
        """
        Retrieve posts that are pending or eligible for retry.

        The latest extraction status determines whether a post
        should be processed again.
        """
        posts = self.load_posts()

        if not posts:
            return []

        latest_status = {}

        if self.status_file_path.exists():
            with self.status_file_path.open("r", encoding="utf-8") as file:
                for line in file:
                    if not line.strip():
                        continue

                    status_data = json.loads(line)

                    latest_status[status_data["source_post_id"]] = (
                        status_data["status"]
                    )

        pending_posts = [
            post for post in posts
            if latest_status.get(post.source_post_id) != "completed"
        ]

        self.logger.info(
            "Found %d posts awaiting extraction.",
            len(pending_posts),
        )

        return pending_posts


    def update_extraction_status(self, source_post_id: str, status: str) -> None:
        """
        Record the extraction status of a source post.

        Args:
            source_post_id: Unique identifier of the source post.
            status: Extraction status (pending, completed, or failed).
        """

        valid_statuses = {'pending', 'completed', 'failed'}

        if status not in valid_statuses:
            raise ValueError(f"Invalid extraction status: {status}")

        status_data = {
            'source_post_id': source_post_id,
            'status': status,
            'extracted_at': (datetime.now(timezone.utc).isoformat() if status == 'completed' else None),
        }

        with self.status_file_path.open('a', encoding='utf-8') as file:
            file.write(json.dumps(status_data) + '\n')

        self.logger.info('Updated extraction status for post %s: %s', source_post_id, status)


    

    