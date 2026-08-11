from typing import Any, Protocol

from pydantic import BaseModel


class LLMCompletion(BaseModel):
    content: dict[str, Any]
    prompt_tokens: int
    completion_tokens: int
    latency_ms: float


class LLMProvider(Protocol):
    def complete_structured(
        self, *, system_prompt: str, user_prompt: str, schema: type[BaseModel]
    ) -> LLMCompletion: ...
