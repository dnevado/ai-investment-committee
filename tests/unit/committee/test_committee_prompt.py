from datetime import date
from decimal import Decimal
from uuid import uuid4

from aic.committee import CommitteeAdjudicationContext, build_prompt
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
    thesis = InvestmentThesis(summary="Durable moat in EUV lithography", supporting_evidence=[evidence])
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
        assessment_id=uuid4(), conclusion="Bull case.", confidence=0.75, supporting_evidence=[evidence.evidence_id]
    )
    bear = AnalysisAssessment(
        assessment_id=uuid4(), conclusion="Bear case.", confidence=0.4, supporting_evidence=[evidence.evidence_id]
    )
    return CommitteeAdjudicationContext(
        investment_case=case, dcf_result=dcf_result, bull_assessment=bull, bear_assessment=bear
    )


def test_build_prompt_is_deterministic() -> None:
    context = _context()

    first = build_prompt(context)
    second = build_prompt(context)

    assert first == second


def test_build_prompt_includes_company_evidence_dcf_and_bull_bear() -> None:
    context = _context()

    system_prompt, user_prompt = build_prompt(context)

    assert "ASML" in user_prompt
    evidence_id = context.investment_case.evidence[0].evidence_id
    assert str(evidence_id) in user_prompt
    assert str(context.dcf_result.implied_value_per_share.amount) in user_prompt
    assert "Bull case." in user_prompt
    assert "Bear case." in user_prompt
    assert "financial calculation" in system_prompt
    assert "average" in system_prompt.lower()
