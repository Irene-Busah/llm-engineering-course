# from pydantic import BaseModel, Field


# class OpportunitySearchIntent(BaseModel):
#     """
#     Represents the user's requirements and preferences
#     when searching for opportunities.
#     """

#     mandatory_requirements: list[str] = Field(
#         default_factory=list,
#         description="Conditions an opportunity must satisfy."
#     )

#     preferences: list[str] = Field(
#         default_factory=list,
#         description="Desirable conditions that are not mandatory."
#     )