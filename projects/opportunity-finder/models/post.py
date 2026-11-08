"""
Define the Pydantic models for source posts collected from external opportunity platforms.

    SourcePost represents the original content collected from a platform.

A source post represents the original content retrieved from a platform such as Hacker News. 
It preserves the source information and metadata needed for deduplication, opportunity extraction,
traceability, and eventual retrieval-augumented generation (RAG).
"""


# importing the libraries
from datetime import datetime
from pydantic import BaseModel, HttpUrl


class SourcePost(BaseModel):
    """
    Represents a single post collected from an external source.

    Attributes:
        source: Name of the platform where the post originated.
        source_post_id: Unique identifier assigned to the post by its source.
        thread_id: Identifier of the discussion thread containing the post.
        thread_title: Title of the original discussion thread.
        author: Username or identifier of the post author.
        url: Direct URL to the original post.
        text: Original text content of the post.
        published_at: Date and time when the post was originally published.
        fetched_at: Date and time when the system collected the post. 
    """


    source: str
    source_post_id: str
    thread_id: str | None = None
    thread_title: str | None = None
    author: str | None = None
    url: HttpUrl
    text: str
    published_at: datetime | None = None
    fetched_at: datetime

