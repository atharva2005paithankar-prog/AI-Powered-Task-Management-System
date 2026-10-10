"""Shapes of the AI requests and responses.

GeneratedDescription and TaskSummary describe what we EXPECT the AI to
return. We validate the AI's JSON against them, because a language model
can return text that is wrong, incomplete or badly formatted.
"""
from typing import Annotated

from pydantic import BaseModel, Field, field_validator

ShortText = Annotated[str, Field(min_length=3, max_length=300)]


class GenerateDescriptionRequest(BaseModel):
    title: str = Field(min_length=3, max_length=200, examples=["Create a REST API for orders"])

    @field_validator("title")
    @classmethod
    def clean_title(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 3:
            raise ValueError("Title must have at least 3 characters")
        return value


# ----- what the AI must return (validated) -----
class GeneratedDescription(BaseModel):
    description: str = Field(min_length=10, max_length=2000)
    checklist: list[ShortText] = Field(min_length=2, max_length=8)


class TaskSummary(BaseModel):
    summary: str = Field(min_length=10, max_length=800)
    key_points: list[ShortText] = Field(min_length=1, max_length=6)


# ----- what our API sends back -----
class DescriptionResponse(GeneratedDescription):
    title: str
    provider: str
    model: str


class SummaryResponse(TaskSummary):
    task_id: int
    provider: str
    model: str
