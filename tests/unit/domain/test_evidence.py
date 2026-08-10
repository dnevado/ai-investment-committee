from datetime import date
from uuid import uuid4

import pytest
from pydantic import ValidationError

from aic.domain import Evidence, EvidenceType


def _valid_kwargs() -> dict:
    return {
        "evidence_id": uuid4(),
        "source": "10-K",
        "title": "FY2025 Annual Report",
        "excerpt": "Revenue grew 12% YoY",
        "retrieved_date": date(2026, 1, 5),
        "evidence_type": EvidenceType.FACT,
    }


def test_valid_construction_without_url() -> None:
    evidence = Evidence(**_valid_kwargs())
    assert evidence.reference is None
    assert evidence.publication_date is None
    assert evidence.evidence_type == EvidenceType.FACT


@pytest.mark.parametrize(
    "evidence_type",
    [
        EvidenceType.FACT,
        EvidenceType.CALCULATION,
        EvidenceType.ASSUMPTION,
        EvidenceType.INTERPRETATION,
        EvidenceType.OPINION,
    ],
)
def test_accepts_every_defined_evidence_type(evidence_type: EvidenceType) -> None:
    kwargs = _valid_kwargs()
    kwargs["evidence_type"] = evidence_type
    evidence = Evidence(**kwargs)
    assert evidence.evidence_type == evidence_type


@pytest.mark.parametrize(
    "missing_field",
    ["evidence_id", "source", "title", "excerpt", "retrieved_date", "evidence_type"],
)
def test_required_field_validation(missing_field: str) -> None:
    kwargs = _valid_kwargs()
    del kwargs[missing_field]
    with pytest.raises(ValidationError):
        Evidence(**kwargs)


def test_rejects_out_of_set_evidence_type() -> None:
    kwargs = _valid_kwargs()
    kwargs["evidence_type"] = "BULLISH"
    with pytest.raises(ValidationError):
        Evidence(**kwargs)


def test_round_trip_serialization() -> None:
    evidence = Evidence(**_valid_kwargs())
    restored = Evidence.model_validate(evidence.model_dump())
    assert restored == evidence
