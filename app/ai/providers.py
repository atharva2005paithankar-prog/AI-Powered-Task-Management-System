"""Talks to the AI providers over plain HTTPS using httpx.

Each provider class knows ONE thing: how to send a system prompt and a user
prompt to that company's API and return the reply text. Everything else
(prompts, JSON validation, retries) is in service.py, so switching provider
is only a change in the .env file.
"""
import logging

import httpx

from app.ai.exceptions import (
    AIInvalidResponseError,
    AINotConfiguredError,
    AIProviderError,
    AITimeoutError,
)
from app.ai.mock import MockProvider
from app.config import get_settings

logger = logging.getLogger(__name__)


class BaseProvider:
    name = "base"
    default_model = ""

    def __init__(self, api_key: str, model: str, timeout: float):
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        raise NotImplementedError

    def _post(self, url: str, headers: dict, payload: dict) -> dict:
        """Send the request and turn every kind of failure into one of our AI errors."""
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(url, headers=headers, json=payload)
        except httpx.TimeoutException as exc:
            logger.error("%s request timed out", self.name)
            raise AITimeoutError() from exc
        except httpx.HTTPError as exc:
            logger.error("%s request failed: %s", self.name, exc.__class__.__name__)
            raise AIProviderError("Could not reach the AI service.") from exc

        if response.status_code >= 400:
            # The full body goes to the log only. The client gets a short message.
            logger.error("%s returned HTTP %s: %s", self.name, response.status_code, response.text[:300])
            raise AIProviderError(f"The AI service returned an error (HTTP {response.status_code}).")

        try:
            return response.json()
        except ValueError as exc:
            raise AIInvalidResponseError("The AI service sent a response that is not JSON.") from exc


class GeminiProvider(BaseProvider):
    name = "gemini"
    default_model = "gemini-2.5-flash"

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
        headers = {"x-goog-api-key": self.api_key, "Content-Type": "application/json"}
        payload = {
            "systemInstruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
            "generationConfig": {"temperature": 0.4, "responseMimeType": "application/json"},
        }
        data = self._post(url, headers, payload)
        try:
            parts = data["candidates"][0]["content"]["parts"]
            return "".join(part.get("text", "") for part in parts)
        except (KeyError, IndexError, TypeError) as exc:
            raise AIInvalidResponseError() from exc


class OpenAIProvider(BaseProvider):
    name = "openai"
    default_model = "gpt-4o-mini"

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        url = "https://api.openai.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "response_format": {"type": "json_object"},
        }
        data = self._post(url, headers, payload)
        try:
            return data["choices"][0]["message"]["content"] or ""
        except (KeyError, IndexError, TypeError) as exc:
            raise AIInvalidResponseError() from exc


class AnthropicProvider(BaseProvider):
    name = "anthropic"
    default_model = "claude-haiku-5-5"

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "max_tokens": 1024,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_prompt}],
        }
        data = self._post(url, headers, payload)
        try:
            blocks = data["content"]
            return "".join(block.get("text", "") for block in blocks if block.get("type") == "text")
        except (KeyError, TypeError, AttributeError) as exc:
            raise AIInvalidResponseError() from exc


PROVIDERS = {
    "gemini": GeminiProvider,
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
}


def get_provider():
    """Build the provider chosen by AI_PROVIDER in the .env file."""
    settings = get_settings()
    name = settings.ai_provider.strip().lower()

    if name == "mock":
        return MockProvider()

    provider_class = PROVIDERS.get(name)
    if provider_class is None:
        logger.error("Unknown AI_PROVIDER '%s'. Use one of: %s, mock", name, ", ".join(PROVIDERS))
        raise AINotConfiguredError()
    if not settings.ai_api_key:
        logger.error("AI_API_KEY is empty. Add it to the .env file.")
        raise AINotConfiguredError()

    return provider_class(
        api_key=settings.ai_api_key,
        model=settings.ai_model or provider_class.default_model,
        timeout=settings.ai_timeout_seconds,
    )
