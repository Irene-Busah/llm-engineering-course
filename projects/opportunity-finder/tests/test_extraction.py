
"""
Tests the opportunity extraction agent using sample source posts.

These tests verify that the agent can receive a valid SourcePost,
construct its input, and extract structured opportunities.
"""

from datetime import datetime, timezone
from pydantic import ValidationError
from models.post import SourcePost
import pytest
from unittest.mock import Mock
from agents.extraction_agent import OpportunityExtractionAgent, OpportunityExtractionResult
from models.opportunity import RemotePolicy, VisaSponsorship, OpportunityExtractionResult, OpportunityDraft


def create_sample_post() -> SourcePost:
    """
    Creates a sample Hacker News post for extraction testing.

    Returns:
        A validated SourcePost instance containing sample job details.
    """

    return SourcePost(
        source="Hacker News",
        source_post_id="12345678",
        thread_id="87654321",
        thread_title="Who is Hiring? November 2026",
        author="acme_recruiter",
        url="https://news.ycombinator.com/item?id=12345678",
        text="""
        Acme Technologies is hiring!

        We are looking for:

        1. Senior Backend Engineer
           Location: London, UK
           Experience: 5+ years
           Skills: Python, Django, PostgreSQL
           Employment: Full-time
           Work arrangement: Hybrid

        2. Machine Learning Engineer
           Location: Berlin, Germany
           Skills: Python, PyTorch, Machine Learning
           Employment: Full-time
           Work arrangement: Remote

        Apply through: https://acme.example.com/careers
        """,
        published_at=datetime.now(timezone.utc),
        fetched_at=datetime.now(timezone.utc)
    )


def test_source_post_creation():
    post = create_sample_post()

    assert post.source == "Hacker News"
    assert post.source_post_id == "12345678"
    assert post.author == "acme_recruiter"


def test_source_post_allows_missing_optional_fields():
    post_data = create_sample_post().model_dump()

    post_data.pop("thread_id")
    post_data.pop("thread_title")
    post_data.pop("author")
    post_data.pop("published_at")

    post = SourcePost(**post_data)

    assert post.thread_id is None
    assert post.thread_title is None
    assert post.author is None
    assert post.published_at is None


def test_source_post_rejects_invalid_url():
    post_data = create_sample_post().model_dump()
    post_data["url"] = "not-a-valid-url"

    with pytest.raises(ValidationError):
        SourcePost(**post_data)


def test_make_user_prompt():
    post = create_sample_post()
    agent = OpportunityExtractionAgent()

    prompt = agent.make_user_prompt(post)

    print("\n========== GENERATED PROMPT ==========\n")
    print(prompt)
    print("\n========== END OF PROMPT =============\n")

    assert post.source in prompt
    assert post.thread_title in prompt
    assert str(post.url) in prompt
    assert post.text in prompt


def test_extract_returns_opportunities():
    post = create_sample_post()

    expected_result = OpportunityExtractionResult(
        is_opportunity=True,
        opportunities=[
            OpportunityDraft(
                company="Acme",
                role_title="Backend Engineer",
                description="Build and maintain backend services.",
                seniority="Mid-level",
                employment_type="Full-time",
                required_skills=["Python", "Django", "PostgreSQL"],
                locations=["Remote"],
                remote_policy=RemotePolicy.REMOTE,
                salary_min=None,
                salary_max=None,
                salary_currency=None,
                visa_sponsorship=VisaSponsorship.UNKNOWN,
                application_url=None,
                deadline=None,
            )
        ],
        rejection_reason=None,
    )

    mock_client = Mock()
    mock_client.beta.chat.completions.parse.return_value.choices = [
        Mock(message=Mock(parsed=expected_result))
    ]

    agent = OpportunityExtractionAgent(client=mock_client)

    result = agent.extract(post)

    assert result.is_opportunity is True
    assert len(result.opportunities) == 1
    assert result.opportunities[0].role_title == "Backend Engineer"

    mock_client.beta.chat.completions.parse.assert_called_once()
