"""
Defines the Pydantic models for candidate profiles.

A candidate profile contains structured information extracted from an uploaded resume and preferences
provided by the candidate.

The profile is used by the opportunity assistant and fit-scoring service to identify and rank 
opportunity opportunities relevant to the candidate.
"""


from pydantic import BaseModel, EmailStr



class CandidateExperience(BaseModel):
    """
    Represents an individual work experience entry.

    Attributes:
        company: Name of the organization.
        role: Job title or position held.
        description: Summary of responsibilities and achievements.
        start_date: Start date of the experience.
        end_date: End date, or None if the candidate currently holds the role.
    """

    company: str
    role: str
    description: str | None
    start_date: str | None
    end_date: str | None


class CandidateEducation(BaseModel):
    """
    Represents an individual education entry.

    Attributes:
        institution: Name of the educational institution.
        qualification: Degree or qualification obtained.
        field_of_study: Academic discipline or specialization.
        graduation_year: Year of graduation, if available.
    """

    institution: str
    qualification: str
    field_of_study: str | None
    graduation_year: int | None


class ResumeData(BaseModel):
    """
    Represents structured information extracted from a candidate's resume.

    This model contains only information supported by the resume.
    Candidate preferences and application-generated identifiers are
    handled separately.
    """

    email: EmailStr | None
    professional_summary: str | None
    skills: list[str]
    experience: list[CandidateExperience]
    education: list[CandidateEducation]
    years_of_experience: float | None


class CandidateProfile(BaseModel):
    """
    Represents the structured profile of a candidate.

    Attributes:
        candidate_id: Unique identifier assigned to the candidate.
        email: Candidate's email address, if provided.
        professional_summary: Summary of the candidate's professional background.
        skills: Technical and professional skills identified from the resume.
        experience: List of the candidate's work experience entries.
        education: List of the candidate's education entries.
        years_of_experience: Estimated total professional experience in years.
        preferred_roles: Types of roles the candidate is interested in.
        preferred_locations: Locations where the candidate would like to work.
        remote_preference: Preferred working arrangement.
        visa_sponsorship_required: Whether the candidate requires visa sponsorship.
    """

    candidate_id: str
    email: EmailStr | None
    professional_summary: str | None
    skills: list[str]
    experience: list[CandidateExperience]
    education: list[CandidateEducation]
    years_of_experience: float | None
    preferred_roles: list[str]
    preferred_locations: list[str]
    remote_preference: str | None
    visa_sponsorship_required: bool | None

