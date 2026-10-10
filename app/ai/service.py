"""The two AI features, built on top of a provider.

Flow for every AI call:
  build prompt -> ask provider -> extract JSON -> validate with Pydantic
  -> if the answer is badly formatted, try once more -> else return a clean error.
"""
import logging
from typing import TypeVar

from pydantic import BaseModel, ValidationError

from app.ai.exceptions import AIInvalidResponseError
from app.ai.parsing import extract_json
from app.ai.prompts import (
    DESCRIPTION_SYSTEM_PROMPT,
    SUMMARY_SYSTEM_PROMPT,
    build_description_prompt,
    build_summary_prompt,
)
from app.ai.providers import get_provider
from app.schemas.ai import DescriptionResponse, GeneratedDescription, SummaryResponse, TaskSummary

logger = logging.getLogger(__name__)

MAX_ATTEMPTS = 2  # first try + one retry when the AI answer is badly formatted

SchemaT = TypeVar("SchemaT", bound=BaseModel)


def _ask_for_json(provider, system_prompt: str, user_prompt: str, schema: type[SchemaT]) -> SchemaT:
    """Call the AI and return its answer validated against `schema`.

    Provider errors (timeout, HTTP error...) are raised by the provider and
    are NOT retried. Only badly formatted answers are retried.
    """
    for attempt in range(1, MAX_ATTEMPTS + 1):
        raw_text = provider.complete(system_prompt, user_prompt)
        try:
            return schema.model_validate(extract_json(raw_text))
        except (ValueError, ValidationError) as exc:
            logger.warning("AI answer was invalid (attempt %s/%s): %s", attempt, MAX_ATTEMPTS, exc)

    raise AIInvalidResponseError()


def generate_task_description(title: str) -> DescriptionResponse:
    """Option A: title -> description + checklist."""
    provider = get_provider()
    result = _ask_for_json(
        provider, DESCRIPTION_SYSTEM_PROMPT, build_description_prompt(title), GeneratedDescription
    )
    return DescriptionResponse(
        title=title,
        provider=provider.name,
        model=provider.model,
        **result.model_dump(),
    )


def summarize_task(task_id: int, title: str, description: str | None) -> SummaryResponse:
    """Option B: title + description -> short summary + key points."""
    provider = get_provider()
    result = _ask_for_json(
        provider, SUMMARY_SYSTEM_PROMPT, build_summary_prompt(title, description), TaskSummary
    )
    return SummaryResponse(
        task_id=task_id,
        provider=provider.name,
        model=provider.model,
        **result.model_dump(),
    )
