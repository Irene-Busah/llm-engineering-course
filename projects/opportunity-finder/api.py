"""
FastAPI application for Opportunity Finder.

The API exposes candidate onboarding/profile management, opportunity browsing,
semantic search, and candidate-specific matching. Collection and indexing remain
the responsibility of the Prefect pipeline.
"""

import logging
import os
import tempfile
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from database.connection import DatabaseConnection
from database.vector_store import VectorStore
from agents.matching_agent import OpportunityMatchingAgent
from models.candidate import CandidateProfile
from models.opportunity import Opportunity, OpportunityStatus, RemotePolicy
from services.candidate_service import CandidateService
from services.embedding_service import EmbeddingService
from services.opportunity_service import OpportunityService
from services.post_storage import PostStorage
from services.resume_service import ResumeService
from services.retrieval_service import RetrievalService


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

database = DatabaseConnection()
candidate_service = CandidateService(database)
resume_service = ResumeService(candidate_service=candidate_service)

# Initialized during application startup so importing api.py has no side effects
# beyond constructing lightweight service objects.
embedding_service: EmbeddingService | None = None
vector_store: VectorStore | None = None
opportunity_service: OpportunityService | None = None
retrieval_service: RetrievalService | None = None
matching_agent: OpportunityMatchingAgent | None = None
post_storage: PostStorage | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global embedding_service, vector_store, opportunity_service
    global retrieval_service, matching_agent, post_storage

    database.create_tables()
    embedding_service = EmbeddingService()
    vector_store = VectorStore()
    opportunity_service = OpportunityService(
        database=database,
        embedding_service=embedding_service,
        vector_store=vector_store,
    )
    retrieval_service = RetrievalService(
        embedding_service=embedding_service,
        vector_store=vector_store,
        opportunity_service=opportunity_service,
    )
    matching_agent = OpportunityMatchingAgent()
    post_storage = PostStorage()

    logger.info("Opportunity Finder API started.")
    yield
    logger.info("Opportunity Finder API stopped.")


app = FastAPI(
    title="Opportunity Finder API",
    description=(
        "API for candidate onboarding, opportunity discovery, "
        "semantic search, and candidate matching."
    ),
    version="1.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class OnboardingResponse(BaseModel):
    message: str
    candidate_id: str
    email: str | None = None
    professional_summary: str | None = None
    skills: list[str]
    years_of_experience: float | None = None
    preferred_roles: list[str]
    preferred_locations: list[str]
    remote_preference: str | None = None
    visa_sponsorship_required: bool | None = None


class CandidateUpdateRequest(BaseModel):
    preferred_roles: list[str] | None = None
    preferred_locations: list[str] | None = None
    remote_preference: str | None = None
    visa_sponsorship_required: bool | None = None


class OpportunitySearchRequest(BaseModel):
    candidate_id: str
    query: str = Field(min_length=1, max_length=4000)
    limit: int = Field(default=5, ge=1, le=50)


class OpportunityPage(BaseModel):
    items: list[Opportunity]
    total: int
    limit: int
    offset: int


class OpportunityMatchResponse(BaseModel):
    confirmed_matches: list[Opportunity]
    potential_matches: list[Opportunity]
    total: int
    query: str


def _require_matching_services() -> tuple[
    RetrievalService, OpportunityMatchingAgent, PostStorage
]:
    if retrieval_service is None or matching_agent is None or post_storage is None:
        raise HTTPException(
            status_code=503,
            detail="Opportunity matching services are not ready.",
        )
    return retrieval_service, matching_agent, post_storage


def _default_candidate_query(profile: CandidateProfile) -> str:
    """Build a natural-language search query from saved candidate preferences."""
    parts: list[str] = []

    if profile.preferred_roles:
        parts.append("Roles: " + ", ".join(profile.preferred_roles))
    if profile.preferred_locations:
        parts.append("Preferred locations: " + ", ".join(profile.preferred_locations))
    if profile.remote_preference:
        parts.append("Work arrangement: " + profile.remote_preference)
    if profile.visa_sponsorship_required is True:
        parts.append("Requires employers that provide visa sponsorship.")
    elif profile.visa_sponsorship_required is False:
        parts.append("Does not require visa sponsorship.")
    if profile.skills:
        parts.append("Candidate skills: " + ", ".join(profile.skills))
    if profile.professional_summary:
        parts.append("Professional background: " + profile.professional_summary)

    return "\n".join(parts) or (
        "Find opportunities relevant to the candidate's education, "
        "experience, and professional background."
    )


def _match_candidate(
    candidate_id: str,
    query: str,
    limit: int,
) -> OpportunityMatchResponse:
    profile = candidate_service.get_candidate_profile(candidate_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Candidate profile not found.")

    retrieval, agent, storage = _require_matching_services()

    try:
        # Retrieval intentionally returns a larger pool (limit * 4).
        # The matching agent applies the final user-facing limit.
        candidates = retrieval.search_opportunities(query=query, limit=limit)

        if not candidates:
            return OpportunityMatchResponse(
                confirmed_matches=[],
                potential_matches=[],
                total=0,
                query=query,
            )

        source_ids = {opportunity.source_post_id for opportunity in candidates}
        # Load once rather than rescanning the JSONL file for every candidate.
        original_posts = {
            post.source_post_id: post
            for post in storage.load_posts()
            if post.source_post_id in source_ids
        }

        result = agent.match_opportunities(
            candidate_profile=profile,
            query=query,
            opportunities=candidates,
            original_posts=original_posts,
            limit=limit,
        )

        confirmed_ids = result["confirmed_opportunity_ids"]
        potential_ids = result["potential_opportunity_ids"]
        candidates_by_id = {item.id: item for item in candidates}

        confirmed = [
            candidates_by_id[item_id]
            for item_id in confirmed_ids
            if item_id in candidates_by_id
        ]
        confirmed_set = set(confirmed_ids)
        potential = [
            candidates_by_id[item_id]
            for item_id in potential_ids
            if item_id in candidates_by_id and item_id not in confirmed_set
        ]

        return OpportunityMatchResponse(
            confirmed_matches=confirmed,
            potential_matches=potential,
            total=len(confirmed) + len(potential),
            query=query,
        )

    except HTTPException:
        raise
    except ValueError as exc:
        logger.warning("Invalid opportunity matching request: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Opportunity matching failed.")
        raise HTTPException(
            status_code=502,
            detail="Opportunity matching could not be completed.",
        ) from exc


@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "opportunity-finder-api"}


@app.post("/api/candidates/onboard", response_model=OnboardingResponse)
async def onboard_candidate(
    resume: UploadFile = File(...),
    preferred_roles: list[str] = Form(default=[]),
    preferred_locations: list[str] = Form(default=[]),
    remote_preference: str = Form(default="Flexible"),
    visa_sponsorship_required: bool = Form(...),
):
    filename = resume.filename or ""
    suffix = Path(filename).suffix.lower()

    if suffix not in {".pdf", ".docx"}:
        raise HTTPException(
            status_code=400,
            detail="Please upload a PDF or DOCX resume.",
        )

    content = await resume.read()
    if not content:
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail="Resume must be 10 MB or smaller.",
        )

    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_file.write(content)
            temp_path = temp_file.name

        profile = resume_service.create_candidate_profile_from_resume(
            file_path=temp_path,
            preferred_roles=preferred_roles,
            preferred_locations=preferred_locations,
            remote_preference=remote_preference,
            visa_sponsorship_required=visa_sponsorship_required,
        )

        return OnboardingResponse(
            message="Your profile has been created successfully.",
            candidate_id=profile.candidate_id,
            email=str(profile.email) if profile.email else None,
            professional_summary=profile.professional_summary,
            skills=profile.skills,
            years_of_experience=profile.years_of_experience,
            preferred_roles=profile.preferred_roles,
            preferred_locations=profile.preferred_locations,
            remote_preference=profile.remote_preference,
            visa_sponsorship_required=profile.visa_sponsorship_required,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Candidate onboarding failed.")
        raise HTTPException(
            status_code=500,
            detail="We couldn't process your resume. Please try again.",
        ) from exc
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
        await resume.close()


@app.get("/api/candidates/{candidate_id}", response_model=CandidateProfile)
def get_candidate(candidate_id: str):
    profile = candidate_service.get_candidate_profile(candidate_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Candidate profile not found.")
    return profile


@app.patch("/api/candidates/{candidate_id}", response_model=CandidateProfile)
def update_candidate(candidate_id: str, payload: CandidateUpdateRequest):
    profile = candidate_service.get_candidate_profile(candidate_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Candidate profile not found.")

    updates: dict[str, Any] = payload.model_dump(exclude_unset=True)
    if not updates:
        return profile

    updated_profile = CandidateProfile.model_validate({
        **profile.model_dump(),
        **updates,
    })
    # save_candidate_profile handles the database updated_at timestamp.
    # This avoids coupling the Pydantic candidate profile to DB metadata.
    candidate_service.save_candidate_profile(updated_profile)
    return updated_profile


@app.get("/api/opportunities", response_model=OpportunityPage)
def list_opportunities(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    role: str | None = None,
    company: str | None = None,
    location: str | None = None,
    status: OpportunityStatus | None = None,
    remote_policy: RemotePolicy | None = None,
):
    if opportunity_service is None:
        raise HTTPException(status_code=503, detail="Opportunity service is not ready.")
    try:
        items, total = opportunity_service.list_opportunities(
            limit=limit,
            offset=offset,
            role=role,
            company=company,
            location=location,
            status=status,
            remote_policy=remote_policy,
        )
        return OpportunityPage(items=items, total=total, limit=limit, offset=offset)
    except Exception as exc:
        logger.exception("Failed to list opportunities.")
        raise HTTPException(
            status_code=500,
            detail="Could not retrieve opportunities.",
        ) from exc


@app.get("/api/opportunities/{opportunity_id}", response_model=Opportunity)
def get_opportunity(opportunity_id: str):
    if opportunity_service is None:
        raise HTTPException(status_code=503, detail="Opportunity service is not ready.")
    opportunity = opportunity_service.get_opportunity(opportunity_id)
    if opportunity is None:
        raise HTTPException(status_code=404, detail="Opportunity not found.")
    return opportunity


@app.post("/api/opportunities/search", response_model=OpportunityMatchResponse)
def search_opportunities(payload: OpportunitySearchRequest):
    return _match_candidate(
        candidate_id=payload.candidate_id,
        query=payload.query.strip(),
        limit=payload.limit,
    )


@app.get(
    "/api/candidates/{candidate_id}/matches",
    response_model=OpportunityMatchResponse,
)
def get_candidate_matches(
    candidate_id: str,
    query: str | None = Query(default=None, min_length=1, max_length=4000),
    limit: int = Query(default=5, ge=1, le=50),
):
    profile = candidate_service.get_candidate_profile(candidate_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Candidate profile not found.")

    effective_query = query.strip() if query else _default_candidate_query(profile)
    return _match_candidate(
        candidate_id=candidate_id,
        query=effective_query,
        limit=limit,
    )
