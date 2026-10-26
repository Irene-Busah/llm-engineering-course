"""
Collect job posts from Hacker News "Who is Hiring?" threads.

First stage of the Opportunity Finder pipeline. Downloads the monthly "Ask HN: Who is hiring?" threads, 
turns each top-level comment (one company's job post) into a plain-text record, and appends only the 
posts it has not stored before to ``data/raw.jsonl``.

Pipeline: Hacker News API --> fetch.py --> data/raw.jsonl --> extract.py

This module does not interpret posts (roles, locations, salaries). That is the job of ``extract.py``.


Data Source:
    Hacker News Algolia API (public, no key needed).
        Find threads: https://hn.algolia.com/api/v1/search_by_date?tags=story,author_whoishiring

        Get a thread: https://hn.algolia.com/api/v1/items/<story_id>
    Top-level comments are job posts; replies are ignored.

Ouptut (``data/raw.jsonl``, one JSON object per line):
    source              "hackernews"
    post_id             HN comment ID(unique within the source)
    thread_id           HN story ID of the thread
    thread_title        e.g. "Ask HN: Who is hiring? (October 2026)"
    author              HN username
    created_at          ISO 8601 UTC time the post was written
    n_replies           number of direct replies
    url                 link to the original post
    text                post body as plain text, link URLs kept
    fetched_at          ISO 8601 UTC time we collected it

Deduplication:
    Posts already in the output file (matched by ``post_id``) are skipped, so re-running only adds new posts.

Usage:
    python fetch.py                             # new posts from the latest thread
    python fetch.py --thread 6                  # backfill the six latest threads
    python fetch.py --thread-id ID              # one specific thread

Requires Python 3.10+ and ``requests``.

Limitations:
    Edited posts are not updated, and there is no automatic retry on network errors.
"""


# libraries
from __future__ import annotations
import argparse
from pathlib import Path
from typing import Any
import re
import sys
import html
import requests
from datetime import datetime, timezone
from schema import RawPost

# constants
ALGOLIA_BASE_URL = "https://hn.algolia.com/api/v1"
DEFAULT_OUTPUT_PATH = Path("data/raw.jsonl")
SOURCE_NAME = 'hackernews'
REQUEST_TIMEOUT_SECONDS = 60


# patterns used to clean the HTML data
_LINK_RE = re.compile(r'<a\s[^>]*?href="([^"]+)"[^>]*>.*?</a>', re.DOTALL | re.IGNORECASE)
_PARAGRAPH_RE = re.compile(r"<p\s*/?>", re.IGNORECASE)
_LINE_BREAK_RE = re.compile(r"<br\s*/?>", re.IGNORECASE)
_TAG_RE = re.compile(r"<[^>]+>")
_EXTRA_BLANK_LINES_RE = re.compile(r"\n{3,}")


# helper function
def _get_json(path: str, params: dict[str, Any] | None = None) -> Any:
    """GET ``ALGOLIA_BASE_URL + path`` and return the decoded JSON.
 
    Raises:
        requests.RequestException: On a network failure or an error status.
    """

    response = requests.get(f"{ALGOLIA_BASE_URL}{path}", params=params, timeout=REQUEST_TIMEOUT_SECONDS)

    response.raise_for_status()

    return response.json()


# defining the functions needed
def find_hiring_threads(limit: int = 1) -> list[dict[str, Any]]:
    """
    Find the most recent "Who is hiring?" threads, newest first.

    Args:
        limit: How many threads to return (at least 1).
    
    Returns:
        Dicts with ``thread_id`` (int) and ``title`` (str).
    
    Raises:
        ValueError: If ``limit`` is less than 1.
        requests.RequestException: If the API fails or cannot be reached.
    """

    if limit < 1:
        raise ValueError(f"limit must be at least 1, got {limit}")

    # The 'whoishiring' account posts 3 threads a month, only 1 of them "Who is hiring?" so
    # ask for several times more results than threads wanted

    data = _get_json(
        "/search_by_date",
        params={"tags": "story,author_whoishiring", "hitsPerPage": max(20, limit * 4)},
    )

    threads = []
    for hit in data['hits']:    # newest first
        title = hit.get('title') or ""

        if title.lower().startswith("ask hn: who is hiring"):
            threads.append({"thread_id": int(hit['objectID']), "title": title})

            if len(threads) == limit:
                break

    return threads



def fetch_thread(thread_id: int) -> dict[str, Any]:
    """
    Download one thread as a nested tree (comments under ``children``).

    Args:
        thread_id: Hacker News story ID.
    
    Returns:
        The decoded JSON tree from the API.
    
    Raises:
        requests.RequestException: If the API fails or cannot be reached.
    """

    return _get_json(f"/items/{thread_id}")



def clean_html(raw_html: str) -> str:
    """Convert a Hacker News comment from HTML to plain text.
 
    Link text is replaced by the link's URL, paragraphs and line breaks become
    newlines, other tags are removed, and HTML entities are decoded.
 
    Args:
        raw_html: Comment body as returned by the API.
 
    Returns:
        Plain text with surrounding whitespace removed.
    """

    text = _LINK_RE.sub(r"\1", raw_html)    # 1. <a href="URL">...</a> -> URL
    text = _PARAGRAPH_RE.sub("\n\n", text)  # 2. <p> -> blank line
    text = _LINE_BREAK_RE.sub("\n", text)   # 3. <br> -> new line
    text = _TAG_RE.sub("", text)            # 4. drop every other tag
    text = html.unescape(text)
    text = _EXTRA_BLANK_LINES_RE.sub("\n\n", text)

    return text.strip()



def parse_posts(thread_tree: dict[str, Any], thread_id: int, fetched_at: str) -> list[dict[str, Any]]:
    """
    Turn a thread tree into one record per top-level job post.
 
    Replies and comments with no text (deleted or dead) are skipped.
 
    Args:
        thread_tree: Tree returned by :func:`fetch_thread`.
        thread_id: Hacker News story ID of the thread.
        fetched_at: ISO 8601 UTC time stored in every record.
 
    Returns:
        Records in thread order, in the output format described above.
    """

    thread_title = thread_tree.get('title')
    posts = []

    for comment in thread_tree.get("children", []): 
        # top level only: replies are ignored
        text = clean_html(comment.get('text') or '')

        # deleted or dead comments have text=None
        if not text:
            continue

        posts.append(RawPost(
            source=SOURCE_NAME,
            post_id=comment['id'],
            thread_id=thread_id,
            thread_title=thread_title,
            author=comment.get('author'),
            created_at=comment.get('created_at'),
            n_replies=len(comment.get('children', [])),
            url=f"https://news.ycombinator.com/item?id={comment['id']}",
            text=text,
            fetched_at=fetched_at,
        ))

    return posts
 


def load_seen_ids(path: Path) -> set[tuple[str, int]]:
    """
    Read which posts are already stored in the output file.
 
    Args:
        path: Path to the JSONL output file.
 
    Returns:
        A set of ``(source, post_id)`` pairs; empty if the file does not exist.
    
    Raises:
        pydantic.ValidationError: If a line is not a valid ``RawPost``.
    """

    if not path.exists():
        return set()

    seen = set()
    with open(path, encoding='utf-8') as file:
        for line in file:
            if line.strip():
                post = RawPost.model_validate_json(line)
                seen.add((post.source, post.post_id))

    return seen
 


def append_posts(posts: list[dict[str, Any]], path: Path) -> int:
    """Append post records to the output file, creating it if needed.
 
    Args:
        posts: Records to write (already filtered for duplicates).
        path: Path to the JSONL output file.
 
    Returns:
        Number of records written.
    """

    if not posts:
        return 0 
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, 'a', encoding='utf-8') as file:
        for post in posts:
            file.write(post.model_dump_json() + "\n")

    return len(posts)
 


def build_parser() -> argparse.ArgumentParser:
    """Create the parser for ``--threads``, ``--thread-id`` and ``--out``."""

    parser = argparse.ArgumentParser(description="Collect job posts from Hacker News 'Who is hiring?' threads.")

    parser.add_argument(
        "--threads",
        type=int,
        default=1,
        help="number of most recent threads to fetch (default: 1)",
    )

    parser.add_argument(
        "--thread-id",
        type=int,
        default=None,
        help="fetch this one thread instead of the latest (overrides --threads)",
    )

    parser.add_argument(
        '--out',
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
        help=f"output file (default: {DEFAULT_OUTPUT_PATH})"
    )

    return parser
 


def main(argv: list[str] | None = None) -> int:
    """Fetch the chosen threads and save the posts not seen before.
 
    Prints a short summary: threads fetched, posts found, new posts saved.
 
    Args:
        argv: Command-line arguments; defaults to ``sys.argv[1:]``.
 
    Returns:
        Exit status, 0 on success (including when nothing new was found).
    """

    parser = build_parser()
    args = parser.parse_args(argv)

    if args.threads < 1:
        parser.error("--threads must be at least 1")

    try:
        if args.thread_id is not None:
            threads = [{"thread_id": args.thread_id, "title": None}]
        else:
            threads = find_hiring_threads(args.threads)
        if not threads:
            print("No 'Who is hiring?' thread found.", file=sys.stderr)
            return 1
 
        seen = load_seen_ids(args.out)
        fetched_at = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
 
        found = saved = 0
        for thread in threads:
            tree = fetch_thread(thread["thread_id"])
            posts = parse_posts(tree, thread["thread_id"], fetched_at)
            fresh = [p for p in posts if (p.source, p.post_id) not in seen]
            seen.update((p.source, p.post_id) for p in fresh)
            saved += append_posts(fresh, args.out)        # saved per thread: progress survives a later failure
            found += len(posts)
    except requests.RequestException as error:
        print(f"Could not reach Hacker News: {error}", file=sys.stderr)
        return 1
 
    print(f"Threads fetched: {len(threads)} | posts found: {found} | "
          f"new posts saved: {saved} -> {args.out}")
    return 0

 
 
if __name__ == "__main__":
    raise SystemExit(main())

