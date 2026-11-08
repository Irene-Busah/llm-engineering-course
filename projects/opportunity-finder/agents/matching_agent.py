
import json
import logging

from openai import OpenAI

from agents.agent import Agent
from config import OPENAI_API_KEY
from models.opportunity import Opportunity
from models.post import SourcePost
from models.candidate import CandidateProfile


class OpportunityMatchingAgent(Agent):
    """
    Evaluates and ranks job opportunities against a user's
    natural-language search query.
    """

    MODEL = "gpt-4o-mini"

    
        
    SYSTEM_PROMPT = """
        You are an opportunity matching agent responsible for finding
        the most relevant job opportunities for a user.

        You will receive:
        1. The user's candidate profile, containing their professional
        background, skills, experience, education, and saved preferences.
        2. The user's original search query, describing what they are
        currently looking for.
        3. A list of candidate job opportunities retrieved from a database.
        4. Original source posts when available, which may provide additional
        context about an opportunity.
        5. A limit specifying the maximum number of opportunities to return.

        Your task is to evaluate the candidate opportunities against the
        candidate's qualifications, saved preferences, and actual search
        requirements, then rank the most suitable ones.

        CANDIDATE PROFILE AND SEARCH INTENT:

        - Use the candidate's skills, experience, education, and professional
        background to evaluate their suitability for each opportunity.
        - Consider the candidate's saved preferences, including preferred
        roles, locations, remote work, and visa sponsorship requirements.
        - Treat the current search query as the candidate's immediate
        search intent. It may refine or override saved preferences.
        - When the current query explicitly conflicts with a saved preference,
        prioritize the current query for that search.
        - Do not assume every saved preference is a mandatory requirement.
        Distinguish between preferences and explicit requirements.
        - Do not infer qualifications, experience, or preferences that are
        not supported by the candidate profile or current query.

        Follow these rules:

        - Interpret the user's actual intentions, not just individual keywords.
        - Distinguish mandatory requirements from flexible preferences.
        - Treat explicitly required conditions as mandatory.
        - Treat a requested role, location, or work arrangement as mandatory
        when it defines the scope of the search, unless the user expresses
        flexibility.
        - Reject opportunities that explicitly violate mandatory requirements.
        - Classify opportunities that satisfy all mandatory requirements as
        confirmed matches.
        - Classify opportunities that appear relevant but have one or more
        unverified mandatory requirements as potential matches.
        - Missing information is not confirmation that a requirement is
        satisfied, but it should not automatically disqualify an otherwise
        relevant opportunity.
        - Never classify an opportunity as confirmed when a mandatory
        requirement remains unverified.
        - Use original source posts as supplementary evidence when available.
        - If an original source post is unavailable, evaluate the opportunity
        using its structured database record.
        - Do not invent information or make unsupported assumptions.
        - Rank opportunities within each classification by relevance to the
        candidate's qualifications, search requirements, and preferences.
        - Return no more than the requested number of opportunities in total.
        - Never modify, rewrite, or generate opportunity records.

        OUTPUT REQUIREMENTS:

        - Return the actual `opportunity_id` provided for each selected candidate.
        - Do not return company names, role titles, source post IDs, or any
        other identifiers in place of opportunity IDs.
        - Preserve ranking order within each classification, from most
        relevant to least relevant.
        - Return confirmed matches before potential matches.
        - Return no more than the specified limit across both lists combined.
        - Each opportunity ID must appear only once.
        - Do not include explanations, comments, or additional fields.
        - Do not use alternative keys.

        Your response MUST follow this exact JSON structure:

        {
            "confirmed_opportunity_ids": [
                "actual-opportunity-id-1"
            ],
            "potential_opportunity_ids": [
                "actual-opportunity-id-2"
            ]
        }

        If no candidates qualify, return:

        {
            "confirmed_opportunity_ids": [],
            "potential_opportunity_ids": []
        }
    """




    name = "Opportunity Matching Agent"

    def __init__(self, client: OpenAI | None = None) -> None:
        """
        Initializes the matching agent.

        Args:
            client: Optional OpenAI client for dependency injection.
        """

        super().__init__()
        self.client = client
        self.log(f"Initialized using model: {self.MODEL}")


    
    def match_opportunities(self, candidate_profile: CandidateProfile, query: str, opportunities: list[Opportunity], original_posts: dict[str, SourcePost] | None = None, limit: int = 5,) -> dict[str, list[str]]:
        """
        Evaluates and ranks opportunities against the user's query.

        Args:
            query: The user's original natural-language search query.
            opportunities: Candidate opportunities retrieved from SQLite.
            original_posts: Optional original posts keyed by source_post_id.
            limit: Maximum number of opportunity IDs to return.

        Returns:
            A dictionary containing ranked confirmed and potential opportunity IDs.
        """

        if not isinstance(candidate_profile, CandidateProfile):
            raise ValueError("A valid candidate profile is required.")

        if not query.strip():
            raise ValueError("Search query cannot be empty.")

        if not opportunities:
            self.log("No candidate opportunities available.")
            return {
                "confirmed_opportunity_ids": [],
                "potential_opportunity_ids": [],
            }

        if limit < 1:
            raise ValueError("Search limit must be at least 1.")

        self.log(
            f"Evaluating {len(opportunities)} candidate opportunities."
        )

        candidate_profile_data = candidate_profile.model_dump(mode="json")

        candidate_data = []

        for opportunity in opportunities:
            candidate = {
                "opportunity_id": opportunity.id,
                "opportunity": opportunity.model_dump(mode="json"),
                "original_post": None,
            }

            original_post = (
                original_posts.get(opportunity.source_post_id)
                if original_posts
                else None
            )

            if original_post:
                candidate["original_post"] = (
                    original_post.model_dump(mode="json")
                )

            candidate_data.append(candidate)

        user_prompt = f"""
            Candidate profile:
            {json.dumps(candidate_profile_data, indent=2)}
        
            User search query:
            {query}

            Maximum number of opportunities to return:
            {limit}

            Candidate opportunities:
            {json.dumps(candidate_data, indent=2)}
        """


        # self.log(
        #     f"Candidate data sent to matching model:\n"
        #     f"{json.dumps(candidate_data, indent=2)}"
        # )


        try:
            if self.client is None:
                if not OPENAI_API_KEY:
                    raise ValueError("OPENAI_API_KEY is not configured.")

                self.client = OpenAI(api_key=OPENAI_API_KEY)

            self.log("Sending candidates to the matching model.")

            response = self.client.chat.completions.create(
                model=self.MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": self.SYSTEM_PROMPT,
                    },
                    {
                        "role": "user",
                        "content": user_prompt,
                    },
                ],
                response_format={"type": "json_object"},
            )

        except Exception:
            self.logger.exception("Opportunity matching request failed.")
            raise

        try:
            response_content = response.choices[0].message.content

            if not response_content:
                raise ValueError("The matching model returned an empty response.")

            result = json.loads(response_content)
            self.log(f"Matching model response")
            
            
            confirmed_ids = result.get("confirmed_opportunity_ids")
            potential_ids = result.get("potential_opportunity_ids")

            
            candidate_ids = {opportunity.id for opportunity in opportunities}

            def validate_ids(opportunity_ids: list) -> list[str]:
                ranked_ids = []
                seen_ids = set()

                for opportunity_id in opportunity_ids:
                    if (
                        isinstance(opportunity_id, str)
                        and opportunity_id in candidate_ids
                        and opportunity_id not in seen_ids
                    ):
                        ranked_ids.append(opportunity_id)
                        seen_ids.add(opportunity_id)

                    if len(ranked_ids) == limit:
                        break

                return ranked_ids


            ranked_confirmed_ids = validate_ids(confirmed_ids)

            ranked_potential_ids = [
                opportunity_id
                for opportunity_id in validate_ids(potential_ids)
                if opportunity_id not in set(ranked_confirmed_ids)
            ]

            remaining_limit = limit - len(ranked_confirmed_ids)
            ranked_potential_ids = ranked_potential_ids[:remaining_limit]

            self.log(
                f"Matching completed. "
                f"Confirmed: {len(ranked_confirmed_ids)}, "
                f"Potential: {len(ranked_potential_ids)}."
            )

            return {
                "confirmed_opportunity_ids": ranked_confirmed_ids,
                "potential_opportunity_ids": ranked_potential_ids,
            }


        except (json.JSONDecodeError, ValueError, AttributeError, IndexError):
            self.logger.exception("Failed to parse matching model response.")
            raise





    