from datetime import date
from decimal import Decimal
from uuid import uuid4

from workflow_fakes import FakeLLMProvider

from aic.dcf import DCFAssumptions, ForecastYear
from aic.domain import Company, Evidence, EvidenceType, FinancialSnapshot, Money
from aic.workflow import WorkflowInput, WorkflowResult, run_investment_workflow


def _result() -> WorkflowResult:
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
    workflow_input = WorkflowInput(
        company=company,
        financial_snapshots=[snapshot],
        evidence=[evidence],
        dcf_assumptions=assumptions,
    )
    evidence_ids = [str(evidence.evidence_id)]
    provider = FakeLLMProvider(
        thesis_content={
            "summary": "Durable moat in EUV lithography.",
            "supporting_evidence_ids": evidence_ids,
            "key_assumptions": [],
            "key_risks": [],
            "invalidation_conditions": [],
        },
        bull_content={
            "conclusion": "Outperform.",
            "confidence": 0.75,
            "arguments": [],
            "assumptions": [],
            "risks": [],
            "supporting_evidence_ids": evidence_ids,
        },
        bear_content={
            "conclusion": "Underperform risk.",
            "confidence": 0.4,
            "arguments": [],
            "assumptions": [],
            "risks": [],
            "supporting_evidence_ids": evidence_ids,
        },
        committee_content={
            "central_thesis": "Thesis.",
            "key_disagreements": [],
            "valuation_summary": "Summary.",
            "downside_risks": [],
            "invalidation_conditions": [],
            "recommendation": "WATCH",
            "confidence": 0.6,
            "dissent": [],
            "supporting_evidence_ids": evidence_ids,
        },
    )
    return run_investment_workflow(workflow_input, provider)


def test_workflow_result_exposes_every_intermediate() -> None:
    result = _result()

    assert result.dcf_result is not None
    assert result.valuation_result is not None
    assert result.thesis is not None
    assert result.bull_assessment is not None
    assert result.bear_assessment is not None
    assert result.decision is not None
    assert result.report is not None
    assert isinstance(result.document, str) and result.document


def test_round_trip_serialization() -> None:
    result = _result()

    restored = WorkflowResult.model_validate(result.model_dump())

    assert restored == result
