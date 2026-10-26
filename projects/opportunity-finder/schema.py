"""
Data models shared across the Opportunity Finder pipeline.

Each stage reads and writes records with a fixed shape. Defining those shapes once, here, means every file agrees 
on the field names and types, and a record that does not match is rejected when it is created or loaded.

Models:
    RawPost             A job post exactly as collected, before any interpretation.
                        Written by ``fetch.py`` to ``data/raw.jsonl``.
    Role                One role advertised in a post
    Extraction          What the LLM reads out of a post. This is the "form" the LLM fills in; its field
                        descriptions are shown to the model
    ExtractedPost       A RawPost plus its Extraction. Written by ``extract.py`` to ``data/extracted.jsonl`` (the knowledge
                        base)

Rule for every Extraction field: record only what the post states. Use ``None``, an empty list, or ``unclear`` when 
the post does not say any. Never guess                 

"""


from __future__ import annotations
from pydantic import BaseModel, ConfigDict, Field, model_validator
from datetime import date
from typing import Literal



class RawPost(BaseModel):
    """One job post as collected from a source, before any interpretation.
 
    Attributes:
        source: Where the post came from, e.g. ``"hackernews"``.
        post_id: ID of the post within its source. ``(source, post_id)`` is unique.
        thread_id: ID of the thread the post belongs to.
        thread_title: Title of that thread, e.g. ``"Ask HN: Who is hiring? (October 2026)"``.
        author: Username of the poster, if known.
        created_at: ISO 8601 UTC time the post was written.
        n_replies: Number of direct replies to the post.
        url: Link to the original post.
        text: Post body as plain text (never empty). Link URLs are kept.
        fetched_at: ISO 8601 UTC time we collected the post.
    """

    # frozen: a record cannot be changed after creation
    # extra="forbid": unknown or misspelled fields raise an error instead of being silently accepted

    model_config = ConfigDict(frozen=True, extra="forbid")

    source: str
    post_id: int
    thread_id: int
    thread_title: str | None = None
    author: str | None = None
    created_at: str
    n_replies: int = Field(ge=0)
    url: str
    text: str = Field(min_length=1)
    fetched_at: str


class Role(BaseModel):
    """One role advertised in a post. A post can advertise several"""

    model_config = ConfigDict(frozen=True, extra='forbid')

    title: str = Field(description="Role title as written in the post, e.g. 'Senior Full Stack Engineer'.")
    location: str | None = Field(
        default=None,
        description="Where this specific role is based, as written, null if the post gives one location for the whole company or does not say"
    )
    salary_min: int | None = Field(
        default=None,
        ge=0,
        description="Lower end of the stated pay as a plain number (100k -> 100000), null if no pay is stated"
    )
    salary_max: int | None = Field(
        default=None,
        ge=0,
        description="Upper end of the stated pay. If only one figure is stated, put it in both salary_min and salary_max."
    )
    currency: str | None = Field(
        default=None,
        pattern=r"^[A-Z]{3}$",
        description="Three-letter currency code, e.g. USD, EUR, GBP. null if no pay is stated."
    )
    salary_period: Literal['year', 'month', 'day', 'hour'] | None = Field(
        default=None,
        description="What the stated pay covers. null if no pay is stated or the period is not clear."
    )
    skills: list[str] = Field(
        default_factory=list,
        description="Technologies and skills the post names for this role, e.g. "
        "['Python', 'PostgreSQL']. If the post lists one stack for all roles, repeat it "
        "for each role. Empty list if none are named.",
    )

    @model_validator(mode='after')
    def _salary_is_consistent(self) -> "Role":
        if self.salary_min is not None and self.salary_max is not None:
            if self.salary_min > self.salary_max:
                raise ValueError("salary_min cannot be greater than salary_max")

        return self



class Extraction(BaseModel):
    """
    What the LLM reads out of one post.
 
    This model is given to the LLM as the form to fill in, so the field
    descriptions below are instructions to the model.
 
    If the post is not an opportunity (a stray comment, ``[flagged]``, an
    announcement), set ``is_opportunity`` to false and leave everything else at
    its default.
    """

    model_config = ConfigDict(frozen=True, extra='forbid')

    is_opportunity: bool = Field(
        description="True if the post advertises at least one job, internship or similar "
        "opportunity a person could apply for. False otherwise."
    )
    company: str | None = Field(
        default=None,
        description="Name of the hiring company or organisation, as written."
    )
    summary: str | None = Field(
        default=None,
        description="Two to four sentences: what the company does and what the role(s) "
        "involve. Use only information in the post. Do not include salary or apply details."
    )
    remote_policy: Literal["remote", "hybrid", "onsite", "unclear"] = Field(
        default="unclear",
        description="'remote' if work can be done remotely, 'hybrid' for a mix, 'onsite' if "
        "in-person only. 'unclear' if the post does not say.",
    )
    remote_scope: str | None = Field(
        default=None,
        description="Where remote work is allowed, copied as written (e.g. 'US only', "
        "'Germany', 'World'). null if the post does not say.",
    )
    locations: list[str] = Field(
        default_factory=list,
        description="Office or work locations named in the post, as written. Empty list if none.",
    )
    employment_types: list[Literal["full-time", "part-time", "contract", "internship"]] = Field(
        default_factory=list,
        description="Employment types the post offers. Empty list if not stated.",
    )
    visa_sponsorship: Literal["yes", "no", "unclear"] = Field(
        default="unclear",
        description="'yes' if the post says it sponsors visas or relocation support for "
        "visas, 'no' if it says it does not. 'unclear' if it says nothing.",
    )
    language_required: list[str] = Field(
        default_factory=list,
        description="Human languages the post requires, e.g. ['German', 'English']. Do not "
        "list programming languages. Empty list if none are required.",
    )
    apply_method: Literal["url", "email", "other", "unclear"] = Field(
        default="unclear",
        description="How to apply: 'url' for a web link or form, 'email' for an email "
        "address, 'other' for anything else (e.g. 'reply to this post'). 'unclear' if not stated.",
    )
    apply_target: str | None = Field(
        default=None,
        description="The link, email address or instruction for applying, copied exactly. "
        "null if not stated.",
    )
    deadline: date | None = Field(
        default=None,
        description="Application deadline as a date, only if the post states one. Otherwise null.",
    )
    roles: list[Role] = Field(
        default_factory=list,
        description="Every distinct role the post advertises. Empty list if the post does "
        "not name a specific role.",
    )


class ExtractionInfo(BaseModel):
    """How an extraction was produced, for traceability."""

    model_config = ConfigDict(frozen=True, extra='forbid')

    model: str = Field(description="Model identifier used for the extraction.")
    extracted_at: str = Field(description="ISO 8601 UTC time of the extraction.")


class ExtractedPost(RawPost):
    """
    A raw post together with what was extracted from it.

    Inherits every ``RawPost`` field, so the original ``text`` is kept unchanged.
    Code attaches the ``extraction``; the LLM never rewrites the text.
    """
    extraction: Extraction
    extracted_with: ExtractionInfo



class LabeledPost(BaseModel):
    """
    One hand-labeled post: the answer key used to score the extractor.
 
    Labels are never part of the knowledge base; they are only compared with
    what the LLM extracts. ``extraction.summary`` is left empty because the
    summary is judged by reading, not by matching.
 
    Attributes:
        post_id: ID of the labeled post (see ``RawPost.post_id``).
        source: Source of the post, e.g. ``"hackernews"``.
        labeled_at: ISO 8601 UTC time the label was saved.
        note: Free-text doubt or comment from the labeler, if any.
        extraction: The correct field values, as read from the post.
    """

    model_config = ConfigDict(frozen=True, extra='forbid')

    post_id: int
    source: str
    labeled_at: str
    note: str | None = None
    extraction: Extraction


