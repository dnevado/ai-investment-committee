from uuid import uuid4

import pytest
from pydantic import ValidationError

from aic.domain import AnalysisAssessment


def _valid_kwargs() -> dict:
    return {
        "assessment_id": uuid4(),
        "conclusion": "Strong upside on lithography demand",
        "confidence": 0.7,
        "arguments": ["Backlog at record highs"],
        "supporting_evidence": [uuid4()],
        "assumptions": ["No major export restriction change"],
        "risks": ["China demand softening"],
    }


def test_valid_construction() -> None:
    assessment = AnalysisAssessment(**_valid_kwargs())
    assert assessment.conclusion == "Strong upside on lithography demand"
    assert assessment.confidence == 0.7


@pytest.mark.parametrize("missing_field", ["assessment_id", "conclusion", "confidence"])
def test_required_field_validation(missing_field: str) -> None:
    kwargs = _valid_kwargs()
    del kwargs[missing_field]
    with pytest.raises(ValidationError):
        AnalysisAssessment(**kwargs)


@pytest.mark.parametrize("confidence", [0.0, 0.5, 1.0])
def test_accepts_confidence_within_bounds(confidence: float) -> None:
    kwargs = _valid_kwargs()
    kwargs["confidence"] = confidence
    assessment = AnalysisAssessment(**kwargs)
    assert assessment.confidence == confidence


@pytest.mark.parametrize("confidence", [-0.01, 1.01, -1.0, 2.0])
def test_rejects_confidence_outside_bounds(confidence: float) -> None:
    kwargs = _valid_kwargs()
    kwargs["confidence"] = confidence
    with pytest.raises(ValidationError):
        AnalysisAssessment(**kwargs)


def test_is_role_agnostic() -> None:
    assessment = AnalysisAssessment(**_valid_kwargs())
    assert "Bull" not in type(assessment).__name__
    assert "Bear" not in type(assessment).__name__
    for field_name in type(assessment).model_fields:
        assert "bull" not in field_name.lower()
        assert "bear" not in field_name.lower()


def test_round_trip_serialization() -> None:
    assessment = AnalysisAssessment(**_valid_kwargs())
    restored = AnalysisAssessment.model_validate(assessment.model_dump())
    assert restored == assessment
