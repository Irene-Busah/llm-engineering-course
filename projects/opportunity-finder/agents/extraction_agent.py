
"""
Defines the OpportunityExtractionAgent responsible for extracting
structured job opportunities from collected source posts.

The agent receives a SourcePost, analyzes its content using an LLM,
and extracts any job opportunities it identifies.

Extracted information is structured using Pydantic models so that
the results can be validated before being passed to the persistence
and retrieval stages of the application.
"""

import logging

from openai import OpenAI

from agents.agent import Agent
from config import OPENAI_API_KEY
from models.post import SourcePost
from models.opportunity import OpportunityExtractionResult


class OpportunityExtractionAgent(Agent):
    """
    Extracts structured job opportunities from source posts.

    The agent uses an LLM to identify job vacancies, extract relevant
    details, and convert them into structured Opportunity objects.

    Attributes:
        MODEL: Name of the LLM used for opportunity extraction.
        SYSTEM_PROMPT: Instructions defining the agent's role and behavior.
        USER_PROMPT_PREFIX: Introductory instructions for the source post.
        USER_PROMPT_SUFFIX: Additional extraction instructions.
        name: Human-readable name of the agent.
    """

    MODEL = "gpt-4o-mini"

    
    SYSTEM_PROMPT = """
    You are an opportunity extraction agent responsible for identifying
    genuine job vacancies from online discussion posts.

    Your task is to analyze the provided source post and extract all
    relevant job opportunities into the required structured format.

    Follow these rules:

    1. Identify whether the post contains genuine job vacancies.
    2. Extract every distinct job opportunity advertised in the post.
    3. A single post may advertise multiple roles. Extract each role
    separately.
    4. Do not treat general company descriptions, networking requests,
    advertisements, or discussions about jobs as job opportunities.
    5. Extract only information explicitly stated or clearly supported
    by the source post.
    6. Never invent missing information or make unsupported assumptions.
    7. If a field is not provided, use null or an empty list as
    appropriate.
    8. For visa sponsorship, use:
    - yes: sponsorship is explicitly supported.
    - no: sponsorship is explicitly unavailable.
    - unknown: sponsorship information is not provided.
    9. For remote policy, use:
    - remote: the position is fully remote.
    - hybrid: the position combines remote and on-site work.
    - onsite: the position requires physical attendance.
    - unknown: the working arrangement is not specified.
    10. Preserve the original meaning of job descriptions and
        requirements when summarizing them.
    11. Do not combine different positions into one opportunity,
        even when they belong to the same company.
    12. If no genuine vacancies are found, return an empty opportunities
        list and explain the reason.

    Deadline handling:
        - Extract the deadline only when an explicit application deadline is
        stated in the source post.
        - If no deadline is provided, return null.
        - Never use placeholder dates such as 0000-01-01.
        - Do not infer or calculate application deadlines.

    Return your response using the provided structured output schema.
    """


    
    USER_PROMPT_PREFIX = """
    Analyze the following source post and identify any genuine job
    opportunities advertised within it.

    Extract the relevant details for each distinct position.
    """


    
    USER_PROMPT_SUFFIX = """
    Pay particular attention to:

    - Company name
    - Job title
    - Role description and responsibilities
    - Required technical and professional skills
    - Experience or seniority requirements
    - Employment type
    - Work location and remote arrangements
    - Salary information
    - Visa sponsorship availability
    - Application link
    - Application deadline

    Remember:
    - Extract multiple positions separately.
    - Do not invent missing information.
    - Distinguish between explicitly stated information and information
    that is unavailable.
    - Return only opportunities supported by the provided post.
    """

    name = "Opportunity Extraction Agent"

    def __init__(self, client: OpenAI | None = None) -> None:
        """
        Initializes the extraction agent.

        Sets up the shared agent functionality and initializes the
        OpenAI client used to communicate with the configured LLM.

        Args:
            client: Optional OpenAI client. Allows an existing client
                    to be injected instead of creating a new one.
        """

        super().__init__()
        self.client = client
        self.log(f"Initialized using model: {self.MODEL}")

    def make_user_prompt(self, post: SourcePost) -> str:
        """
        Constructs the user prompt containing the source post content.

        Combines the prompt prefix, original post content, and prompt
        suffix to provide the LLM with the information needed for extraction.

        Args:
            post: SourcePost containing the original collected content.

        Returns:
            A formatted prompt string.
        """

        return (
            f"{self.USER_PROMPT_PREFIX}\n"
            f"Source: {post.source}\n"
            f"Thread: {post.thread_title}\n"
            f"Post URL: {post.url}\n\n"
            f"Post Content:\n{post.text}\n\n"
            f"{self.USER_PROMPT_SUFFIX}"
        )

    def extract(self, post: SourcePost) -> OpportunityExtractionResult:
        """
        Extracts job opportunities from a source post using an LLM.

        Constructs the user prompt, sends it to the configured language
        model, and parses the response into an OpportunityExtractionResult.

        Args:
            post: SourcePost containing the original collected content.

        Returns:
            A validated OpportunityExtractionResult containing the
            extracted opportunities or the reason for rejecting the post.

        Raises:
            ValueError: If the model does not return a valid parsed result.
            Exception: If the LLM request or response processing fails.
        """

        self.log(f"Starting Extraction for Post: {post.source_post_id}")

        try:
            user_prompt = self.make_user_prompt(post)

            if self.client is None:
                if not OPENAI_API_KEY:
                    raise ValueError("OPENAI_API_KEY is missing. Check your .env file.")

                self.client = OpenAI(api_key=OPENAI_API_KEY)

            response = self.client.beta.chat.completions.parse(
                model=self.MODEL,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                response_format=OpportunityExtractionResult
            )

            result = response.choices[0].message.parsed

            if result is None:
                raise ValueError("The model returned no parsed extraction result.")

            if result.is_opportunity:
                self.log(
                    f"Successfully extracted {len(result.opportunities)} "
                    f"opportunity(s) from post: {post.source_post_id}"
                )
            else:
                self.log(
                    f"No opportunities found in post: {post.source_post_id}",
                    logging.WARNING
                )

            return result

        except Exception:
            self.logger.exception(f"Extraction failed for post: {post.source_post_id}")
            raise

