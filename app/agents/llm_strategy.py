from abc import ABC, abstractmethod
from typing import Any

import httpx

from app.core.config import settings
from app.core.exceptions import ConfigurationError, ExternalServiceError


class LLMStrategy(ABC):
    @abstractmethod
    def complete(self, messages: list[dict[str, str]]) -> str:
        """Generate a text completion for chat messages."""


class OpenRouterStrategy(LLMStrategy):
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
    ) -> None:
        self._api_key = api_key or settings.OPENROUTER_API_KEY
        self._base_url = (base_url or settings.OPENROUTER_BASE_URL).rstrip("/")
        self._model = model or settings.OPENROUTER_MODEL

    def complete(self, messages: list[dict[str, str]]) -> str:
        if not self._api_key:
            raise ConfigurationError(detail="OpenRouter API key is not configured.")

        try:
            response = httpx.post(
                f"{self._base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self._api_key}"},
                json={"model": self._model, "messages": messages},
                timeout=30,
            )
            response.raise_for_status()
            payload: dict[str, Any] = response.json()
            return str(payload["choices"][0]["message"]["content"])
        except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError) as error:
            raise ExternalServiceError(
                detail="OpenRouter completion failed."
            ) from error
