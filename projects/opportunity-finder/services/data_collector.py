"""
Data collection service for retrieving job-related posts from Hacker News.

This module uses the public Hacker News Algolia API to discover monthly 'who is Hiring?' threads
and retrieve their comments.

It is responsible for:
    - Discovering relevant hiring threads.
    - Retrieving comments belonging to those threads.
    - Converting source comments into validated SourcePost objects.
    - Handling API requests, pagination, and HTTP errors.

The collected posts are passed to the opportunity extraction agent for structured job opportunity
extraction.
"""


# importing the libraries
import logging

import httpx
from models.post import SourcePost
from typing import Any
import html
import re
from datetime import datetime, timezone


# constants
_LINK_RE = re.compile(
    r'<a\s[^>]*?href="([^"]+)"[^>]*>.*?</a>',
    re.DOTALL | re.IGNORECASE,
)
_PARAGRAPH_RE = re.compile(r"<p\s*/?>", re.IGNORECASE)
_LINE_BREAK_RE = re.compile(r"<br\s*/?>", re.IGNORECASE)
_TAG_RE = re.compile(r"<[^>]+>")
_EXTRA_BLANK_LINES_RE = re.compile(r"\n{3,}")


class HackerNewsDataCollector:
    """
    Collects job-related posts from Hacker News using the Algolia API.

    Attributes:
        BASE_URL: Base URL for the Hacker News Algolia API.
        HIRING_USERNAME: Hacker News account that publishes hiring threads.
        client: HTTP client used to communicate with the API.
        logger: Logger for tracking collection activities and errors.
    """

    BASE_URL = 'https://hn.algolia.com/api/v1/'
    HIRING_USERNAME = 'whoishiring'

    def __init__(self, client: httpx.Client | None = None) -> None:
        """
        Initialize the Hacker News data collector.

        Args:
            client: Optional HTTP client. If not provided, a new client is initialized using
            the Algolia API base URL.
        """

        self.client = client or httpx.Client(
            base_url=self.BASE_URL,
            timeout=10.0,
        )

        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("Hacker News data collector initialized.")


    def _fetch_json(self, endpoint: str, params: dict | None = None) -> dict:
        """
        Send a GET request to the Algolia API and return the JSON response.

        Args:
            endpoint: API endpoint to request
            params: Optional query parameters to include in the request.

        Returns:
            The API response as a dictionary.
        
        Raises:
            httpx.HTTPStatusError: If the API returns an unsuccessful HTTP status.
            httpx.RequestError: If a network-related error occurs.
            ValueError: If the response cannot be decoded as JSON.
        """

        try:
            response = self.client.get(endpoint, params=params)
            response.raise_for_status()

            return response.json()

        except httpx.HTTPStatusError:
            self.logger.exception("API request failed with HTTP status error: %s", endpoint)
            raise

        except httpx.RequestError:
            self.logger.exception("Network error while requesting API endpoint: %s", endpoint)
            raise
        
        except ValueError:
            self.logger.exception('Failed to decode API response as JSON: %s', endpoint)
            raise

    def find_hiring_threads(self, limit: int = 1) -> list[dict[str, Any]]:
        """
        Find the most recent 'Who is hiring?' threads, newest first.

        Args:
            limit: Number of hiring threads to retrieve.
        
        Returns:
            A list of dictionaries containing each thread's ID and title.

        Raises:
            ValueError: If limit is less than 1.
        """

        if limit < 1:
            raise ValueError(f"Limit must be at least 1, got {limit}")

        self.logger.info(f"Searching for the {limit} most recent hiring thread(s).")

        data = self._fetch_json(
            "/search_by_date",
            params={
                "tags": "story,author_whoishiring",
                "hitsPerPage": max(20, limit * 4),
            },
        )

        threads = []

        for hit in data.get('hits', []):
            title = hit.get('title') or ""

            if title.lower().startswith("ask hn: who is hiring"):
                threads.append({
                    "thread_id": int(hit['objectID']),
                    'title': title
                })

                if len(threads) == limit:
                    break

        self.logger.info(f"Found {len(threads)} hiring thread(s).")

        return threads

    def fetch_thread(self, thread_id: int) -> dict[str, Any]:
        """
        Retrieve a hiring thread and its nested comments from Hacker News.

        Args:
            thread_id: The Hacker News story ID.

        Returns:
            The thread data as a dictionary, including its comments.

        Raises:
            httpx.HTTPStatusError: If the API returns an unsuccessful status.
            httpx.RequestError: If a network-related error occurs.
            ValueError: If the response cannot be decoded as JSON.
        """
        self.logger.info(f"Fetching hiring thread: {thread_id}")

        thread = self._fetch_json(f"/items/{thread_id}")

        self.logger.info(f"Successfully fetched hiring thread: {thread_id}")

        return thread


    def clean_html(self, raw_html: str) -> str:
        """
        Convert Hacker News comment HTML into reasonable plain text.

        Links are replaced with their URLs, paragraphs and line breaks are preserved, and remaining 
        HTML tags are removed.

        Args:
            raw_html: Raw comment content returned by Hacker News.

        Returns:
            Cleaned plain-text comment.
        """

        text = _LINK_RE.sub(r"\1", raw_html)
        text = _PARAGRAPH_RE.sub("\n\n", text)
        text = _LINE_BREAK_RE.sub("\n", text)
        text = _TAG_RE.sub("", text)
        text = html.unescape(text)
        text = _EXTRA_BLANK_LINES_RE.sub("\n\n", text)

        return text.strip()


    def parse_posts(self, thread_tree: dict[str, Any], thread_id: int) -> list[SourcePost]:
        """
        Convert top-level comments from a hiring thread into SourcePost objects.

        Deleted comments, dead comments, and comments without text are skipped.
        Replies are not processed

        Args:
            thread_tree: Nested thread data returned by fetch_thread().
            thread_id: Hacker News ID of the hiring thread.

        Returns:
            A list of validated SourcePost objects.
        """

        thread_title = thread_tree.get('title')
        fetched_at = datetime.now(timezone.utc)

        posts = []

        for comment in thread_tree.get('children', []):
            raw_text = comment.get('text') or ''
            text = self.clean_html(raw_text)

            # skip deleted, dead, or empty comments.
            if not text:
                continue

            post = SourcePost(
                source="hackernews",
                source_post_id=str(comment["id"]),
                thread_id=str(thread_id),
                thread_title=thread_title,
                author=comment.get("author"),
                url=f"https://news.ycombinator.com/item?id={comment['id']}",
                text=text,
                published_at=comment.get("created_at"),
                fetched_at=fetched_at,
            )

            posts.append(post)

        self.logger.info(f"Parsed {len(posts)} top-level posts from thread {thread_id}")

        return posts


    def collect_posts(self, limit: int = 1) -> list[SourcePost]:
        """
        Discover hiring threads, retrieve their comments, and parse them
        into SourcePost objects.

        Args:
            limit: Number of recent hiring threads to retrieve.

        Returns:
            A list of collected SourcePost objects.
        """

        self.logger.info("Starting Hacker News Post Collection.")

        threads = self.find_hiring_threads(limit=limit)

        if not threads:
            self.logger.info("No hiring threads found.", logging.WARNING)
            return []

        all_posts = []

        for thread in threads:
            thread_id = thread['thread_id']

            thread_tree = self.fetch_thread(thread_id)

            posts = self.parse_posts(
                thread_tree=thread_tree,
                thread_id=thread_id,
            )

            all_posts.extend(posts)

        self.logger.info(
            f"Collection completed. Retrieved {len(all_posts)} posts "
            f"from {len(threads)} thread(s)."
        )

        return all_posts
    
