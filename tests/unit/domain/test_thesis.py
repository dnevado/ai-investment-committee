from datetime import date
from uuid import uuid4

import pytest
from pydantic import ValidationError

from aic.domain import Evidence, EvidenceType, InvestmentThesis


def _evidence() -> Evidence:
    return Evidence(
        evidence_id=uuid4(),
        source="10-K",
        title="FY2025 Annual Report",
        excerpt="Revenue grew 12% YoY",
        retrieved_date=date(2026, 1, 5),
        evidence_type=EvidenceType.FACT,
    )


def test_valid_construction() -> None:
    thesis = InvestmentThesis(
        summary="Durable moat in EUV lithography",
        supporting_evidence=[_evidence()],
        key_assumptions=["EUV demand persists"],
        key_risks=["Export restrictions"],
        invalidation_conditions=["Major customer cancels multi-year order"],
    )
    assert thesis.summary == "Durable moat in EUV lithography"
    assert len(thesis.supporting_evidence) == 1
    assert thesis.key_assumptions == ["EUV demand persists"]
    assert thesis.key_risks == ["Export restrictions"]
    assert thesis.invalidation_conditions == ["Major customer cancels multi-year order"]


def test_defaults_to_empty_collections() -> None:
    thesis = InvestmentThesis(summary="Minimal thesis")
    assert thesis.supporting_evidence == []
    assert thesis.key_assumptions == []
    assert thesis.key_risks == []
    assert thesis.invalidation_conditions == []


def test_required_field_validation() -> None:
    with pytest.raises(ValidationError):
        InvestmentThesis()


def test_round_trip_serialization() -> None:
    thesis = InvestmentThesis(
        summary="Durable moat in EUV lithography",
        supporting_evidence=[_evidence()],
        key_assumptions=["EUV demand persists"],
        key_risks=["Export restrictions"],
        invalidation_conditions=["Major customer cancels multi-year order"],
    )
    restored = InvestmentThesis.model_validate(thesis.model_dump())
    assert restored == thesis
