from datetime import date
from decimal import Decimal
from uuid import uuid4

from committee_fakes import FakeLLMProvider

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


def _context() -> CommitteeAdjudicationContext:
    evidence = Evidence(
        evidence_id=uuid4(),
        source="10-K",
        title="FY2025 Annual Report",
        excerpt="Revenue grew 12% YoY",
        retrieved_date=date(2026, 1, 5),
        evidence_type=EvidenceType.FACT,
    )
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
        summary="Durable moat in EUV lithography", supporting_evidence=[evidence]
    )
    case = InvestmentCase(
        case_id=uuid4(),
        company=company,
        financial_snapshots=[snapshot],
        thesis=thesis,
        evidence=[evidence],
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
        conclusion="Bull case.",
        confidence=0.8,
        supporting_evidence=[evidence.evidence_id],
    )
    bear = AnalysisAssessment(
        assessment_id=uuid4(),
        conclusion="Bear case.",
        confidence=0.3,
        supporting_evidence=[evidence.evidence_id],
    )
    return CommitteeAdjudicationContext(
        investment_case=case,
        dcf_result=dcf_result,
        bull_assessment=bull,
        bear_assessment=bear,
    )


def _draft_content(*, dissent: list[str]) -> dict:
    return {
        "central_thesis": "ASML holds a durable moat in EUV lithography.",
        "key_disagreements": ["Bull and Bear diverge on export-risk severity."],
        "valuation_summary": "DCF implies modest upside.",
        "downside_risks": ["Export restrictions"],
        "invalidation_conditions": ["Major customer cancels multi-year order"],
        "recommendation": "WATCH",
        "confidence": 0.55,
        "dissent": dissent,
        "supporting_evidence_ids": [],
    }


def test_dissent_is_preserved_when_present() -> None:
    context = _context()
    provider = FakeLLMProvider(
        content=_draft_content(
            dissent=["Bear case underweights structural EUV demand."]
        )
    )

    decision = generate_decision(context, provider)

    assert decision.dissent == ["Bear case underweights structural EUV demand."]


def test_dissent_is_empty_when_assessments_are_aligned() -> None:
    context = _context()
    provider = FakeLLMProvider(content=_draft_content(dissent=[]))

    decision = generate_decision(context, provider)

    assert decision.dissent == []
