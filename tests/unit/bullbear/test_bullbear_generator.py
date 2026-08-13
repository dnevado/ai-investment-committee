from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest
from bullbear_fakes import FakeLLMProvider
from pydantic import ValidationError

from aic.bullbear import (
    BullBearContext,
    generate_bear_assessment,
    generate_bull_assessment,
)
from aic.domain import (
    Company,
    Evidence,
    EvidenceType,
    FinancialSnapshot,
    InvestmentCase,
    InvestmentThesis,
    Money,
    ValuationResult,
)


def _evidence() -> Evidence:
    return Evidence(
        evidence_id=uuid4(),
        source="10-K",
        title="FY2025 Annual Report",
        excerpt="Revenue grew 12% YoY",
        retrieved_date=date(2026, 1, 5),
        evidence_type=EvidenceType.FACT,
    )


def _context(evidence: list[Evidence]) -> BullBearContext:
    company = Company(
        company_id=uuid4(),
        ticker="ASML",
        name="ASML Holding",
        exchange="AEX",
        country="NL",
        sector="Technology",
        industry="Semiconductor Equipment",
    )
    snapshot = FinancialSnapshot(
        as_of=date(2026, 3, 31),
        revenue=Money(amount=Decimal(6500000000), currency="EUR"),
    )
    thesis = InvestmentThesis(
        summary="Durable moat in EUV lithography", supporting_evidence=evidence
    )
    case = InvestmentCase(
        case_id=uuid4(),
        company=company,
        financial_snapshots=[snapshot],
        thesis=thesis,
        evidence=evidence,
    )
    valuation = ValuationResult(
        valuation_id=uuid4(),
        method="DCF (FCFF)",
        valuation_date=date(2026, 3, 31),
        estimated_value=Money(amount=Decimal("850.00"), currency="EUR"),
        confidence=0.7,
    )
    return BullBearContext(investment_case=case, valuation_result=valuation)


def _bull_draft_content(evidence_ids: list[str]) -> dict:
    return {
        "conclusion": "ASML is positioned to outperform on structural EUV demand.",
        "confidence": 0.75,
        "arguments": [
            "Monopoly position in EUV lithography",
            "Multi-year order backlog",
        ],
        "assumptions": ["EUV demand persists"],
        "risks": ["Execution risk on capacity expansion"],
        "supporting_evidence_ids": evidence_ids,
    }


def _bear_draft_content(evidence_ids: list[str]) -> dict:
    return {
        "conclusion": "Export restrictions could materially impair growth.",
        "confidence": 0.4,
        "arguments": ["Geopolitical export controls are tightening"],
        "assumptions": ["China demand normalizes"],
        "risks": ["Loss of a major customer", "Multi-year order cancellation"],
        "supporting_evidence_ids": evidence_ids,
    }


# --- Bull role -------------------------------------------------------------


def test_generate_bull_assessment_with_valid_draft_resolves_traceable_evidence() -> (
    None
):
    evidence = _evidence()
    context = _context([evidence])
    provider = FakeLLMProvider(
        content=_bull_draft_content([str(evidence.evidence_id)]),
        prompt_tokens=120,
        completion_tokens=80,
        latency_ms=40.0,
    )

    assessment = generate_bull_assessment(context, provider)

    assert (
        assessment.conclusion
        == "ASML is positioned to outperform on structural EUV demand."
    )
    assert assessment.confidence == 0.75
    assert assessment.arguments == [
        "Monopoly position in EUV lithography",
        "Multi-year order backlog",
    ]
    assert assessment.assumptions == ["EUV demand persists"]
    assert assessment.risks == ["Execution risk on capacity expansion"]
    assert assessment.supporting_evidence == [evidence.evidence_id]


def test_generate_bull_assessment_rejects_untraceable_evidence_id() -> None:
    context = _context([_evidence()])
    provider = FakeLLMProvider(content=_bull_draft_content([str(uuid4())]))

    with pytest.raises(ValueError, match="unknown evidence_id"):
        generate_bull_assessment(context, provider)


def test_generate_bull_assessment_rejects_schema_invalid_response() -> None:
    context = _context([_evidence()])
    provider = FakeLLMProvider(content={"conclusion": "missing every other field"})

    with pytest.raises(ValidationError):
        generate_bull_assessment(context, provider)


def test_generate_bull_assessment_rejects_confidence_outside_bounds() -> None:
    context = _context([_evidence()])
    content = _bull_draft_content([])
    content["confidence"] = 1.5
    provider = FakeLLMProvider(content=content)

    with pytest.raises(ValidationError):
        generate_bull_assessment(context, provider)


def test_generate_bull_assessment_propagates_provider_error_without_fabricating() -> (
    None
):
    context = _context([_evidence()])
    provider = FakeLLMProvider(error=TimeoutError("provider timed out"))

    with pytest.raises(TimeoutError, match="provider timed out"):
        generate_bull_assessment(context, provider)


# --- Bear role ---------------------------------------------------------------


def test_generate_bear_assessment_with_valid_draft_resolves_traceable_evidence() -> (
    None
):
    evidence = _evidence()
    context = _context([evidence])
    provider = FakeLLMProvider(
        content=_bear_draft_content([str(evidence.evidence_id)]),
        prompt_tokens=110,
        completion_tokens=70,
        latency_ms=35.0,
    )

    assessment = generate_bear_assessment(context, provider)

    assert (
        assessment.conclusion == "Export restrictions could materially impair growth."
    )
    assert assessment.confidence == 0.4
    assert assessment.arguments == ["Geopolitical export controls are tightening"]
    assert assessment.assumptions == ["China demand normalizes"]
    assert assessment.risks == [
        "Loss of a major customer",
        "Multi-year order cancellation",
    ]
    assert assessment.supporting_evidence == [evidence.evidence_id]


def test_generate_bear_assessment_rejects_untraceable_evidence_id() -> None:
    context = _context([_evidence()])
    provider = FakeLLMProvider(content=_bear_draft_content([str(uuid4())]))

    with pytest.raises(ValueError, match="unknown evidence_id"):
        generate_bear_assessment(context, provider)


def test_generate_bear_assessment_rejects_schema_invalid_response() -> None:
    context = _context([_evidence()])
    provider = FakeLLMProvider(content={"conclusion": "missing every other field"})

    with pytest.raises(ValidationError):
        generate_bear_assessment(context, provider)


def test_generate_bear_assessment_rejects_confidence_outside_bounds() -> None:
    context = _context([_evidence()])
    content = _bear_draft_content([])
    content["confidence"] = -0.1
    provider = FakeLLMProvider(content=content)

    with pytest.raises(ValidationError):
        generate_bear_assessment(context, provider)


def test_generate_bear_assessment_propagates_provider_error_without_fabricating() -> (
    None
):
    context = _context([_evidence()])
    provider = FakeLLMProvider(error=TimeoutError("provider timed out"))

    with pytest.raises(TimeoutError, match="provider timed out"):
        generate_bear_assessment(context, provider)


# --- Independence ------------------------------------------------------------


def test_bull_and_bear_generation_are_independent() -> None:
    evidence = _evidence()
    context = _context([evidence])
    bull_provider = FakeLLMProvider(
        content=_bull_draft_content([str(evidence.evidence_id)])
    )
    bear_provider = FakeLLMProvider(
        content=_bear_draft_content([str(evidence.evidence_id)])
    )

    bull = generate_bull_assessment(context, bull_provider)
    bear = generate_bear_assessment(context, bear_provider)

    assert len(bull_provider.calls) == 1
    assert len(bear_provider.calls) == 1
    bear_call = bear_provider.calls[0]
    bull_call = bull_provider.calls[0]
    assert bull.conclusion not in bear_call["system_prompt"]
    assert bull.conclusion not in bear_call["user_prompt"]
    assert bear.conclusion not in bull_call["system_prompt"]
    assert bear.conclusion not in bull_call["user_prompt"]
    for argument in bull.arguments:
        assert argument not in bear_call["user_prompt"]
    for argument in bear.arguments:
        assert argument not in bull_call["user_prompt"]
