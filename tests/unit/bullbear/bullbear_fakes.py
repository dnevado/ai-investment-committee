from typing import Any

from pydantic import BaseModel

from aic.research.provider import LLMCompletion


class FakeLLMProvider:
    def __init__(
        self,
        *,
        content: dict[str, Any] | None = None,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        latency_ms: float = 0.0,
        error: Exception | None = None,
    ) -> None:
        self._content = content
        self._prompt_tokens = prompt_tokens
        self._completion_tokens = completion_tokens
        self._latency_ms = latency_ms
        self._error = error
        self.calls: list[dict[str, Any]] = []

    def complete_structured(
        self, *, system_prompt: str, user_prompt: str, schema: type[BaseModel]
    ) -> LLMCompletion:
        self.calls.append({"system_prompt": system_prompt, "user_prompt": user_prompt})
        if self._error is not None:
            raise self._error
        assert self._content is not None
        return LLMCompletion(
            content=self._content,
            prompt_tokens=self._prompt_tokens,
            completion_tokens=self._completion_tokens,
            latency_ms=self._latency_ms,
        )
