from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest
from committee_fakes import FakeLLMProvider
from pydantic import ValidationError

from aic.committee import CommitteeAdjudicationContext, generate_decision
from aic.dcf import DCFAssumptions, ForecastYear, compute_dcf
from aic.domain import (
    AnalysisAssessment,
    Company,
    Evidence,
    EvidenceType,
    FinancialSnapshot,
    InvestmentCase,
    InvestmentThesis,
    Money,
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


def _context(evidence: list[Evidence]) -> CommitteeAdjudicationContext:
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
    thesis = InvestmentThesis(summary="Durable moat in EUV lithography", supporting_evidence=evidence)
    case = InvestmentCase(
        case_id=uuid4(),
        company=company,
        financial_snapshots=[snapshot],
        thesis=thesis,
        evidence=evidence,
    )
    forecast = [
        ForecastYear(
            revenue=Money(amount=Decimal(1000), currency="EUR"),
            depreciation_and_amortization=Money(amount=Decimal(0), currency="EUR"),
            capital_expenditure=Money(amount=Decimal(0), currency="EUR"),
            change_in_net_working_capital=Money(amount=Decimal(0), currency="EUR"),
        )
    ]
    assumptions = DCFAssumptions(
        forecast=forecast,
        operating_margin=Decimal("0.5"),
        tax_rate=Decimal(0),
        wacc=Decimal("0.10"),
        terminal_growth_rate=Decimal(0),
        cash=Money(amount=Decimal(0), currency="EUR"),
        debt=Money(amount=Decimal(0), currency="EUR"),
        shares_outstanding=Decimal(10),
    )
    dcf_result = compute_dcf(assumptions)
    bull = AnalysisAssessment(
        assessment_id=uuid4(),
        conclusion="Structural EUV demand supports a premium multiple.",
        confidence=0.75,
        supporting_evidence=[item.evidence_id for item in evidence],
    )
    bear = AnalysisAssessment(
        assessment_id=uuid4(),
        conclusion="Export restrictions could impair growth.",
        confidence=0.4,
        supporting_evidence=[item.evidence_id for item in evidence],
    )
    return CommitteeAdjudicationContext(
        investment_case=case, dcf_result=dcf_result, bull_assessment=bull, bear_assessment=bear
    )


def _valid_draft_content(evidence_ids: list[str]) -> dict:
    return {
        "central_thesis": "ASML holds a durable moat in EUV lithography.",
        "key_disagreements": ["Bull weighs demand durability higher than Bear weighs export risk."],
        "valuation_summary": "DCF implies upside versus current levels.",
        "downside_risks": ["Export restrictions"],
        "invalidation_conditions": ["Major customer cancels multi-year order"],
        "recommendation": "WATCH",
        "confidence": 0.6,
        "dissent": ["Bear case underweights structural demand."],
        "supporting_evidence_ids": evidence_ids,
    }


def test_generate_decision_with_valid_draft_resolves_evidence_and_composes_rationale() -> None:
    evidence = _evidence()
    context = _context([evidence])
    provider = FakeLLMProvider(
        content=_valid_draft_content([str(evidence.evidence_id)]),
        prompt_tokens=140,
        completion_tokens=95,
        latency_ms=55.0,
    )

    decision = generate_decision(context, provider)

    assert decision.recommendation.value == "WATCH"
    assert decision.referenced_evidence == [evidence.evidence_id]
    assert decision.referenced_thesis == context.investment_case.thesis
    assert decision.dissent == ["Bear case underweights structural demand."]
    assert decision.valuation_reference is None
    assert "ASML holds a durable moat in EUV lithography." in decision.rationale
    assert "Bull weighs demand durability higher than Bear weighs export risk." in decision.rationale
    assert "DCF implies upside versus current levels." in decision.rationale
    assert "Export restrictions" in decision.rationale
    assert "Major customer cancels multi-year order" in decision.rationale
    assert "0.6" in decision.rationale


def test_generate_decision_rejects_untraceable_evidence_id() -> None:
    context = _context([_evidence()])
    provider = FakeLLMProvider(content=_valid_draft_content([str(uuid4())]))

    with pytest.raises(ValueError, match="unknown evidence_id"):
        generate_decision(context, provider)


def test_generate_decision_rejects_schema_invalid_response() -> None:
    context = _context([_evidence()])
    provider = FakeLLMProvider(content={"central_thesis": "missing every other field"})

    with pytest.raises(ValidationError):
        generate_decision(context, provider)


def test_generate_decision_rejects_recommendation_outside_enum() -> None:
    context = _context([_evidence()])
    content = _valid_draft_content([])
    content["recommendation"] = "MAYBE"
    provider = FakeLLMProvider(content=content)

    with pytest.raises(ValidationError):
        generate_decision(context, provider)


def test_generate_decision_propagates_provider_error_without_fabricating_decision() -> None:
    context = _context([_evidence()])
    provider = FakeLLMProvider(error=TimeoutError("provider timed out"))

    with pytest.raises(TimeoutError, match="provider timed out"):
        generate_decision(context, provider)
