import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from aic.research.draft import ThesisDraft
from aic.research.openai_provider import OpenAIProvider


def _fake_openai_response() -> SimpleNamespace:
    payload = {
        "summary": "Durable moat in EUV lithography.",
        "supporting_evidence_ids": [],
        "key_assumptions": ["EUV demand persists"],
        "key_risks": ["Export restrictions"],
        "invalidation_conditions": [],
    }
    message = SimpleNamespace(content=json.dumps(payload))
    choice = SimpleNamespace(message=message)
    usage = SimpleNamespace(prompt_tokens=120, completion_tokens=80)
    return SimpleNamespace(choices=[choice], usage=usage)


def test_openai_provider_maps_mocked_response_to_llm_completion() -> None:
    with patch("aic.research.openai_provider.OpenAI") as mock_openai_cls:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = _fake_openai_response()
        mock_openai_cls.return_value = mock_client

        provider = OpenAIProvider(api_key="test-key")
        completion = provider.complete_structured(
            system_prompt="system", user_prompt="user", schema=ThesisDraft
        )

    assert completion.content["summary"] == "Durable moat in EUV lithography."
    assert completion.prompt_tokens == 120
    assert completion.completion_tokens == 80
    assert completion.latency_ms >= 0
    mock_client.chat.completions.create.assert_called_once()
    mock_openai_cls.assert_called_once_with(api_key="test-key")


def test_openai_provider_rejects_blank_api_key() -> None:
    with pytest.raises(ValueError, match="api_key"):
        OpenAIProvider(api_key="")
