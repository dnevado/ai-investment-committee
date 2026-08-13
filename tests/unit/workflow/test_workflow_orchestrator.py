from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest
from pydantic import ValidationError
from workflow_fakes import FakeLLMProvider

from aic.dcf import DCFAssumptions, ForecastYear
from aic.domain import Company, Evidence, EvidenceType, FinancialSnapshot, Money
from aic.workflow import WorkflowInput, run_investment_workflow


def _evidence() -> Evidence:
    return Evidence(
        evidence_id=uuid4(),
        source="10-K",
        title="FY2025 Annual Report",
        excerpt="Revenue grew 12% YoY",
        retrieved_date=date(2026, 1, 5),
        evidence_type=EvidenceType.FACT,
    )


def _company() -> Company:
    return Company(
        company_id=uuid4(),
        ticker="ASML",
        name="ASML Holding",
        exchange="AEX",
        country="NL",
        sector="Technology",
        industry="Semiconductor Equipment",
    )


def _workflow_input(evidence: list[Evidence]) -> WorkflowInput:
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
    return WorkflowInput(
        company=_company(),
        financial_snapshots=[snapshot],
        evidence=evidence,
        dcf_assumptions=assumptions,
    )


def _thesis_content(evidence_ids: list[str]) -> dict:
    return {
        "summary": "Durable moat in EUV lithography.",
        "supporting_evidence_ids": evidence_ids,
        "key_assumptions": ["EUV demand persists"],
        "key_risks": ["Export restrictions"],
        "invalidation_conditions": ["Major customer cancels multi-year order"],
    }


def _bull_content(evidence_ids: list[str]) -> dict:
    return {
        "conclusion": "Outperform on structural EUV demand.",
        "confidence": 0.75,
        "arguments": ["Monopoly in EUV lithography"],
        "assumptions": ["EUV demand persists"],
        "risks": ["Execution risk"],
        "supporting_evidence_ids": evidence_ids,
    }


def _bear_content(evidence_ids: list[str]) -> dict:
    return {
        "conclusion": "Export restrictions could impair growth.",
        "confidence": 0.4,
        "arguments": ["Export controls tightening"],
        "assumptions": ["China demand normalizes"],
        "risks": ["Order cancellation"],
        "supporting_evidence_ids": evidence_ids,
    }


def _committee_content(evidence_ids: list[str]) -> dict:
    return {
        "central_thesis": "Durable moat, priced for perfection.",
        "key_disagreements": ["Bull weighs demand higher than Bear weighs export risk."],
        "valuation_summary": "DCF implies fair value near current levels.",
        "downside_risks": ["Export restrictions"],
        "invalidation_conditions": ["Major customer cancels multi-year order"],
        "recommendation": "WATCH",
        "confidence": 0.6,
        "dissent": [],
        "supporting_evidence_ids": evidence_ids,
    }


def _happy_path_provider(evidence: list[Evidence]) -> FakeLLMProvider:
    evidence_ids = [str(item.evidence_id) for item in evidence]
    return FakeLLMProvider(
        thesis_content=_thesis_content(evidence_ids),
        bull_content=_bull_content(evidence_ids),
        bear_content=_bear_content(evidence_ids),
        committee_content=_committee_content(evidence_ids),
    )


def test_run_investment_workflow_end_to_end() -> None:
    evidence = _evidence()
    workflow_input = _workflow_input([evidence])
    provider = _happy_path_provider([evidence])

    result = run_investment_workflow(workflow_input, provider)

    assert result.thesis.summary == "Durable moat in EUV lithography."
    assert result.decision.recommendation.value == "WATCH"
    assert result.decision.valuation_reference == result.valuation_result.valuation_id
    assert result.report.bull_assessment == result.bull_assessment
    assert result.report.bear_assessment == result.bear_assessment
    assert result.report.assessment == result.bull_assessment
    assert str(result.dcf_result.implied_value_per_share.amount) in result.document
    assert "Bull Case Assessment" in result.document
    assert "Bear Case Assessment" in result.document


def test_run_investment_workflow_traces_evidence_end_to_end() -> None:
    evidence = _evidence()
    workflow_input = _workflow_input([evidence])
    provider = _happy_path_provider([evidence])

    result = run_investment_workflow(workflow_input, provider)

    assert result.thesis.supporting_evidence == [evidence]
    assert result.bull_assessment.supporting_evidence == [evidence.evidence_id]
    assert result.bear_assessment.supporting_evidence == [evidence.evidence_id]
    assert result.decision.referenced_evidence == [evidence.evidence_id]


def test_run_investment_workflow_succeeds_with_zero_supplied_evidence() -> None:
    workflow_input = _workflow_input([])
    provider = _happy_path_provider([])

    result = run_investment_workflow(workflow_input, provider)

    assert result.thesis.supporting_evidence == []
    assert result.bull_assessment.supporting_evidence == []
    assert result.bear_assessment.supporting_evidence == []
    assert result.decision.referenced_evidence == []


def test_run_investment_workflow_reuses_single_dcf_computation_throughout() -> None:
    evidence = _evidence()
    workflow_input = _workflow_input([evidence])
    provider = _happy_path_provider([evidence])

    result = run_investment_workflow(workflow_input, provider)

    assert result.report.dcf_result == result.dcf_result
    assert result.valuation_result.estimated_value == result.dcf_result.implied_value_per_share
    for year in result.dcf_result.per_year:
        assert str(year.fcff.amount) in result.document


# --- Failure handling (US2) --------------------------------------------------


def test_invalid_dcf_assumptions_fail_before_any_llm_call() -> None:
    forecast = [
        ForecastYear(
            revenue=Money(amount=Decimal(1000), currency="EUR"),
            depreciation_and_amortization=Money(amount=Decimal(0), currency="EUR"),
            capital_expenditure=Money(amount=Decimal(0), currency="EUR"),
            change_in_net_working_capital=Money(amount=Decimal(0), currency="EUR"),
        )
    ]
    with pytest.raises(ValidationError, match="wacc"):
        DCFAssumptions(
            forecast=forecast,
            operating_margin=Decimal("0.5"),
            tax_rate=Decimal(0),
            wacc=Decimal("0.05"),
            terminal_growth_rate=Decimal("0.10"),
            cash=Money(amount=Decimal(0), currency="EUR"),
            debt=Money(amount=Decimal(0), currency="EUR"),
            shares_outstanding=Decimal(10),
        )


def test_research_stage_failure_halts_before_any_later_stage() -> None:
    evidence = _evidence()
    workflow_input = _workflow_input([evidence])
    provider = FakeLLMProvider(thesis_error=TimeoutError("research timed out"))

    with pytest.raises(TimeoutError, match="research timed out"):
        run_investment_workflow(workflow_input, provider)

    assert len(provider.calls) == 1


def test_bull_stage_failure_halts_before_bear_committee_or_report() -> None:
    evidence = _evidence()
    evidence_ids = [str(evidence.evidence_id)]
    workflow_input = _workflow_input([evidence])
    provider = FakeLLMProvider(
        thesis_content=_thesis_content(evidence_ids),
        bull_error=TimeoutError("bull generation timed out"),
    )

    with pytest.raises(TimeoutError, match="bull generation timed out"):
        run_investment_workflow(workflow_input, provider)

    assert len(provider.calls) == 2


def test_bear_stage_failure_halts_before_committee_or_report() -> None:
    evidence = _evidence()
    evidence_ids = [str(evidence.evidence_id)]
    workflow_input = _workflow_input([evidence])
    provider = FakeLLMProvider(
        thesis_content=_thesis_content(evidence_ids),
        bull_content=_bull_content(evidence_ids),
        bear_error=TimeoutError("bear generation timed out"),
    )

    with pytest.raises(TimeoutError, match="bear generation timed out"):
        run_investment_workflow(workflow_input, provider)

    assert len(provider.calls) == 3


def test_committee_stage_failure_halts_before_report() -> None:
    evidence = _evidence()
    evidence_ids = [str(evidence.evidence_id)]
    workflow_input = _workflow_input([evidence])
    provider = FakeLLMProvider(
        thesis_content=_thesis_content(evidence_ids),
        bull_content=_bull_content(evidence_ids),
        bear_content=_bear_content(evidence_ids),
        committee_error=TimeoutError("committee adjudication timed out"),
    )

    with pytest.raises(TimeoutError, match="committee adjudication timed out"):
        run_investment_workflow(workflow_input, provider)

    assert len(provider.calls) == 4
