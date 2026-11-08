import logging
import uuid
from pathlib import Path

from docx import Document
from pypdf import PdfReader

from openai import OpenAI
from config import OPENAI_API_KEY
from models.candidate import ResumeData, CandidateProfile
from services.candidate_service import CandidateService




class ResumeService:

    MODEL = 'gpt-4o-mini'

    def __init__(self, client: OpenAI | None = None, candidate_service: CandidateService | None = None,):
        self.client = client
        self.candidate_service = candidate_service
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("Resume service initialized.")


    def extract_text(self, file_path: str) -> str:
        """
        Extract readable text from a PDF or DOCX resume.

        Args:
            file_path: Path to the uploaded resume.

        Returns:
            Extracted resume text.
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"Resume file not found: {file_path}")

        file_extension = path.suffix.lower()

        self.logger.info(f"Extracting text from resume: {path.name}")

        try:
            if file_extension == ".pdf":
                reader = PdfReader(str(path))
                text = "\n".join(
                    page.extract_text() or ""
                    for page in reader.pages
                )

            elif file_extension == ".docx":
                document = Document(str(path))
                text = "\n".join(
                    paragraph.text
                    for paragraph in document.paragraphs
                )

            else:
                raise ValueError(
                    f"Unsupported resume format: {file_extension}"
                )

            text = text.strip()

            if not text:
                raise ValueError(
                    "No readable text found in the resume."
                )

            self.logger.info("Resume text extraction completed successfully.")

            return text

        except Exception:
            self.logger.exception("Failed to extract resume text.")
            raise


    def parse_resume(self, resume_text: str) -> ResumeData:
        """
        Extract structured candidate information from resume text.

        Args:
            resume_text: Text extracted from an uploaded resume.

        Returns:
            A validated ResumeData object.
        """
        if not resume_text or not resume_text.strip():
            raise ValueError("Resume text cannot be empty.")

        self.logger.info("Starting resume parsing.")

        if self.client is None:
            if not OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY is not configured.")

            self.client = OpenAI(api_key=OPENAI_API_KEY)

        system_prompt = """
        You are a resume information extraction assistant.

        Extract candidate information from the provided resume and return
        it using the supplied structured output schema.

        Follow these rules:
        1. Only extract information supported by the resume.
        2. Do not invent skills, qualifications, companies, or experience.
        3. Preserve the meaning of professional summaries and experience
        descriptions.
        4. Extract each work experience as a separate entry.
        5. Extract each education record as a separate entry.
        6. If information is unavailable, return null for nullable fields
        and an empty list for list fields.
        7. Calculate the candidate's total years of professional experience
        based on the employment start and end dates provided in the resume.
        Account for overlapping employment periods without double-counting
        them. If an employment end date is missing, do not assume the role
        is ongoing unless the resume explicitly indicates this. If there
        are insufficient dates to make a reasonable calculation, return null.
        8. Do not infer candidate preferences, desired locations, or
        visa sponsorship requirements from the resume.
        """

        try:
            response = self.client.beta.chat.completions.parse(
                model=self.MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": resume_text},
                ],
                response_format=ResumeData,
            )

            resume_data = response.choices[0].message.parsed

            if resume_data is None:
                raise ValueError("The model returned no parsed resume data.")

            self.logger.info("Resume parsing completed successfully.")

            return resume_data

        except Exception:
            self.logger.exception("Failed to parse resume.")
            raise


    def create_candidate_profile(
        self, resume_data: ResumeData, preferred_roles: list[str], preferred_locations: list[str], remote_preference: str | None, visa_sponsorship_required: bool | None,) -> CandidateProfile:
        """
        Create a complete candidate profile from resume data and user preferences.

        Args:
            resume_data: Structured information extracted from the resume.
            preferred_roles: Roles the candidate is interested in.
            preferred_locations: Candidate's preferred work locations.
            remote_preference: Preferred working arrangement.
            visa_sponsorship_required: Whether the candidate requires sponsorship.

        Returns:
            A complete CandidateProfile object.
        """

        self.logger.info("Creating candidate profile.")

        candidate_profile = CandidateProfile(
            candidate_id=str(uuid.uuid4()),
            email=resume_data.email,
            professional_summary=resume_data.professional_summary,
            skills=resume_data.skills,
            experience=resume_data.experience,
            education=resume_data.education,
            years_of_experience=resume_data.years_of_experience,
            preferred_roles=preferred_roles,
            preferred_locations=preferred_locations,
            remote_preference=remote_preference,
            visa_sponsorship_required=visa_sponsorship_required,
        )

        self.logger.info(
            f"Candidate profile created: {candidate_profile.candidate_id}"
        )

        return candidate_profile

    def create_candidate_profile_from_resume(
        self,
        file_path: str,
        preferred_roles: list[str],
        preferred_locations: list[str],
        remote_preference: str | None,
        visa_sponsorship_required: bool | None,
    ) -> CandidateProfile:
        """
        Extract resume information, create a candidate profile,
        and persist it.
        """

        if self.candidate_service is None:
            raise ValueError("Candidate service has not been configured.")

        self.logger.info("Starting candidate onboarding.")

        # Extract text from the uploaded resume.
        resume_text = self.extract_text(file_path)

        # Parse the resume into structured information.
        resume_data = self.parse_resume(resume_text)

        # Create the candidate profile using resume data and user preferences.
        candidate_profile = self.create_candidate_profile(
            resume_data=resume_data,
            preferred_roles=preferred_roles,
            preferred_locations=preferred_locations,
            remote_preference=remote_preference,
            visa_sponsorship_required=visa_sponsorship_required,
        )

        # Persist the candidate profile.
        self.candidate_service.save_candidate_profile(candidate_profile)

        self.logger.info(
            "Candidate onboarding completed: %s",
            candidate_profile.candidate_id,
        )

        return candidate_profile
            
