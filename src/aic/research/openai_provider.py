import json
import time
from typing import Any

from openai import OpenAI
from pydantic import BaseModel

from aic.research.provider import LLMCompletion


class OpenAIProvider:
    def __init__(self, *, api_key: str, model: str = "gpt-4o-mini") -> None:
        if not api_key:
            raise ValueError("OpenAIProvider requires a non-empty api_key")
        self._model = model
        self._client = OpenAI(api_key=api_key)

    def complete_structured(
        self, *, system_prompt: str, user_prompt: str, schema: type[BaseModel]
    ) -> LLMCompletion:
        start = time.perf_counter()
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": schema.__name__,
                    "schema": schema.model_json_schema(),
                    "strict": True,
                },
            },
        )
        latency_ms = (time.perf_counter() - start) * 1000

        raw_content = response.choices[0].message.content
        if raw_content is None:
            raise ValueError("OpenAI response contained no message content")
        content: dict[str, Any] = json.loads(raw_content)
        usage = response.usage
        return LLMCompletion(
            content=content,
            prompt_tokens=usage.prompt_tokens if usage else 0,
            completion_tokens=usage.completion_tokens if usage else 0,
            latency_ms=latency_ms,
        )
