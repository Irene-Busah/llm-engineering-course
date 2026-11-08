"""
Defines the Pydantic models for structured job opportunities.

    Opportunity represents the actual job opportunity extracted from that content.

An opportunity represents a job vacancy extracted from a source post. These models provide a
consistent structure for storing, searching, evaluating, and retrieving job opportunities across
different sources.
"""


# importing libraries
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, field_validator


class OpportunityStatus(str, Enum):
    """
    Defines the possible availability statuses of an opportunity

    Values:
        OPEN: The opportunity is confirmed to be accepting applications.
        CLOSED: The opportunity is confirmed to be closed.
        EXPIRED: The application deadline has passed.
        UNKNOWN: The current availability cannot be confirmed.
    """

    OPEN = 'open'
    CLOSED = 'closed'
    EXPIRED = 'expired'
    UNKNOWN = 'unknown'


class RemotePolicy(str, Enum):
    """
    Defines the working arrangement associated with an opportunity.

    Values:
        REMOTE: Work can be performed remotely.
        HYBRID: Work combines remote and on-site arrangements.
        ONSITE: Work requires physical attendance at a workplace.
        UNKNOWN: The working arrangement is not specified.
    """

    REMOTE = 'remote'
    HYBRID = 'hybrid'
    ONSITE = 'onsite'
    UNKNOWN = 'unknown'


class VisaSponsorship(str, Enum):
    """
    Indicates whether an employer supports visa sponsorship.

    Values:
        YES: Visa sponsorship is explicitly supported.
        NO: Visa sponsorship is explicitly not supported.
        UNKNOWN: The source does not provide sufficient information.
    """

    YES = 'yes'
    NO = 'no'
    UNKNOWN = 'unknown'


class Opportunity(BaseModel):
    """
    Represents a structured job opportunity extracted from a source post.

    Attributes:
        id: Unique identifier for the opportunity.
        source_post_id: Identifier of the original SourcePost.
        company: Name of the hiring organization.
        role_title: Title of the advertised position.
        description: Description of the role and its responsibilities.
        seniority: Expected experience or seniority level.
        employment_type: Type of employment, such as full-time or contract.
        required_skills: Technical and professional skills required.
        locations: Locations where the role is available.
        remote_policy: Working arrangement for the position.
        salary_min: Minimum advertised salary, if available.
        salary_max: Maximum advertised salary, if available.
        salary_currency: Currency used for the advertised salary.
        visa_sponsorship: Whether visa sponsorship is supported.
        application_url: Link through which candidates can apply.
        deadline: Application deadline, if specified.
        status: Current availability status of the opportunity.
        published_at: Date and time the original post was published.
        first_seen_at: Date and time the system first collected it.
        last_seen_at: Most recent time the opportunity was observed.
        extraction_confidence: Confidence assigned to the extraction result.
        created_at: Date and time the opportunity record was created.
        updated_at: Date and time the opportunity record was last updated.
    """

    id: str
    source_post_id: str
    opportunity_index: int
    company: str | None
    role_title: str
    description: str | None
    seniority: str | None
    employment_type: str | None
    required_skills: list[str]
    locations: list[str]
    remote_policy: RemotePolicy
    salary_min: float | None
    salary_max: float | None
    salary_currency: str | None
    visa_sponsorship: VisaSponsorship
    application_url: str | None
    deadline: datetime | None = None
    status: OpportunityStatus
    published_at: datetime | None
    first_seen_at: datetime
    last_seen_at: datetime
    extraction_confidence: float | None
    created_at: datetime
    updated_at: datetime
    indexed_at: datetime | None = None



class OpportunityDraft(BaseModel):
    """
    Represents an opportunity extracted by the LLM before persistence.

    Contains only information that can be identified from the source post.
    System-managed fields such as IDs and timestamps are added later.

    Attributes:
        company: Name of the hiring organization.
        role_title: Title of the advertised position.
        description: Description of the role and responsibilities.
        seniority: Expected experience or seniority level.
        employment_type: Type of employment.
        required_skills: Skills required for the position.
        locations: Locations where the role is available.
        remote_policy: Working arrangement for the position.
        salary_min: Minimum advertised salary, if available.
        salary_max: Maximum advertised salary, if available.
        salary_currency: Currency used for the advertised salary.
        visa_sponsorship: Whether visa sponsorship is supported.
        application_url: Link through which candidates can apply.
        deadline: Application deadline, if specified.
    """

    company: str | None
    role_title: str
    description: str | None
    seniority: str | None
    employment_type: str | None
    required_skills: list[str]
    locations: list[str]
    remote_policy: RemotePolicy
    salary_min: float | None
    salary_max: float | None
    salary_currency: str | None
    visa_sponsorship: VisaSponsorship
    application_url: str | None
    deadline: datetime | None

    @field_validator("deadline", mode="before")
    @classmethod
    def normalize_invalid_deadline(cls, value):
        if isinstance(value, str) and value.startswith("0000-"):
            return None

        return value




class OpportunityExtractionResult(BaseModel):
    """
    Represents the structured result returned by the extraction agent.

    Attributes:
        is_opportunity: Indicates whether the source post contains
                        one or more genuine job opportunities.
        opportunities: List of opportunities extracted from the post.
        rejection_reason: Explanation for rejecting a post, if applicable.
    """

    is_opportunity: bool
    opportunities: list[OpportunityDraft]
    rejection_reason: str | None
