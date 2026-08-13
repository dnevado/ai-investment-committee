from datetime import date
from decimal import Decimal
from uuid import uuid4

from aic.bullbear import BullBearContext, build_bear_prompt, build_bull_prompt
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


def _context() -> BullBearContext:
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
    valuation = ValuationResult(
        valuation_id=uuid4(),
        method="DCF (FCFF)",
        valuation_date=date(2026, 3, 31),
        estimated_value=Money(amount=Decimal("850.00"), currency="EUR"),
        confidence=0.7,
    )
    return BullBearContext(investment_case=case, valuation_result=valuation)


def test_build_bull_prompt_is_deterministic() -> None:
    context = _context()

    first = build_bull_prompt(context)
    second = build_bull_prompt(context)

    assert first == second


def test_build_bear_prompt_is_deterministic() -> None:
    context = _context()

    first = build_bear_prompt(context)
    second = build_bear_prompt(context)

    assert first == second


def test_build_bull_prompt_includes_company_evidence_and_valuation() -> None:
    context = _context()

    system_prompt, user_prompt = build_bull_prompt(context)

    assert "ASML" in user_prompt
    evidence_id = context.investment_case.evidence[0].evidence_id
    assert str(evidence_id) in user_prompt
    assert str(context.valuation_result.estimated_value.amount) in user_prompt
    assert "financial calculation" in system_prompt
    assert "Bull" in system_prompt


def test_build_bear_prompt_includes_company_evidence_and_valuation() -> None:
    context = _context()

    system_prompt, user_prompt = build_bear_prompt(context)

    assert "ASML" in user_prompt
    evidence_id = context.investment_case.evidence[0].evidence_id
    assert str(evidence_id) in user_prompt
    assert str(context.valuation_result.estimated_value.amount) in user_prompt
    assert "financial calculation" in system_prompt
    assert "Bear" in system_prompt


def test_bull_and_bear_prompts_differ() -> None:
    context = _context()

    bull_system, _ = build_bull_prompt(context)
    bear_system, _ = build_bear_prompt(context)

    assert bull_system != bear_system
