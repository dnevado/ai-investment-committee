from typing import Any

from pydantic import BaseModel

from aic.bullbear import AssessmentDraft
from aic.committee import CommitteeDecisionDraft
from aic.research import ThesisDraft
from aic.research.provider import LLMCompletion


class FakeLLMProvider:
    """A configurable fake that answers each of the workflow's four LLM calls
    (research, bull, bear, committee) by inspecting the requested schema (and, for
    the two calls sharing AssessmentDraft, the system_prompt's role marker).
    """

    def __init__(
        self,
        *,
        thesis_content: dict[str, Any] | None = None,
        bull_content: dict[str, Any] | None = None,
        bear_content: dict[str, Any] | None = None,
        committee_content: dict[str, Any] | None = None,
        thesis_error: Exception | None = None,
        bull_error: Exception | None = None,
        bear_error: Exception | None = None,
        committee_error: Exception | None = None,
    ) -> None:
        self._thesis_content = thesis_content
        self._bull_content = bull_content
        self._bear_content = bear_content
        self._committee_content = committee_content
        self._thesis_error = thesis_error
        self._bull_error = bull_error
        self._bear_error = bear_error
        self._committee_error = committee_error
        self.calls: list[dict[str, Any]] = []

    def complete_structured(
        self, *, system_prompt: str, user_prompt: str, schema: type[BaseModel]
    ) -> LLMCompletion:
        self.calls.append(
            {"schema": schema, "system_prompt": system_prompt, "user_prompt": user_prompt}
        )

        if schema is ThesisDraft:
            error, content = self._thesis_error, self._thesis_content
        elif schema is AssessmentDraft and "Bull" in system_prompt:
            error, content = self._bull_error, self._bull_content
        elif schema is AssessmentDraft:
            error, content = self._bear_error, self._bear_content
        elif schema is CommitteeDecisionDraft:
            error, content = self._committee_error, self._committee_content
        else:
            raise AssertionError(f"Unexpected schema requested: {schema}")

        if error is not None:
            raise error
        assert content is not None
        return LLMCompletion(content=content, prompt_tokens=100, completion_tokens=60, latency_ms=10.0)
