from uuid import uuid4

import pytest
from pydantic import ValidationError

from aic.domain import CommitteeDecision, Recommendation


def _valid_kwargs() -> dict:
    return {
        "decision_id": uuid4(),
        "recommendation": Recommendation.WATCH,
        "rationale": "Valuation stretched relative to near-term catalysts",
        "referenced_evidence": [uuid4()],
        "dissent": ["One member favored BUY given backlog strength"],
    }


def test_valid_construction_without_valuation_reference() -> None:
    decision = CommitteeDecision(**_valid_kwargs())
    assert decision.valuation_reference is None
    assert decision.referenced_thesis is None


def test_valid_construction_with_valuation_reference() -> None:
    kwargs = _valid_kwargs()
    kwargs["valuation_reference"] = uuid4()
    decision = CommitteeDecision(**kwargs)
    assert decision.valuation_reference is not None


@pytest.mark.parametrize(
    "missing_field", ["decision_id", "recommendation", "rationale"]
)
def test_required_field_validation(missing_field: str) -> None:
    kwargs = _valid_kwargs()
    del kwargs[missing_field]
    with pytest.raises(ValidationError):
        CommitteeDecision(**kwargs)


@pytest.mark.parametrize(
    "recommendation", [Recommendation.BUY, Recommendation.WATCH, Recommendation.AVOID]
)
def test_accepts_every_defined_recommendation(recommendation: Recommendation) -> None:
    kwargs = _valid_kwargs()
    kwargs["recommendation"] = recommendation
    decision = CommitteeDecision(**kwargs)
    assert decision.recommendation == recommendation


def test_rejects_invalid_recommendation() -> None:
    kwargs = _valid_kwargs()
    kwargs["recommendation"] = "STRONG_BUY"
    with pytest.raises(ValidationError):
        CommitteeDecision(**kwargs)


def test_decision_timestamp_is_utc() -> None:
    decision = CommitteeDecision(**_valid_kwargs())
    assert decision.decision_timestamp.tzinfo is not None


def test_round_trip_serialization() -> None:
    kwargs = _valid_kwargs()
    kwargs["valuation_reference"] = uuid4()
    decision = CommitteeDecision(**kwargs)
    restored = CommitteeDecision.model_validate(decision.model_dump())
    assert restored == decision
