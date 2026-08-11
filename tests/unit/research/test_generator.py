from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest
from fakes import FakeLLMProvider
from pydantic import ValidationError

from aic.dcf import DCFAssumptions, ForecastYear, compute_dcf
from aic.domain import (
    Company,
    Evidence,
    EvidenceType,
    FinancialSnapshot,
    InvestmentCase,
    InvestmentThesis,
    Money,
)
from aic.research import ResearchContext, generate_thesis


def _evidence() -> Evidence:
    return Evidence(
        evidence_id=uuid4(),
        source="10-K",
        title="FY2025 Annual Report",
        excerpt="Revenue grew 12% YoY",
        retrieved_date=date(2026, 1, 5),
        evidence_type=EvidenceType.FACT,
    )


def _context(evidence: list[Evidence]) -> ResearchContext:
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
    case = InvestmentCase(
        case_id=uuid4(),
        company=company,
        financial_snapshots=[snapshot],
        thesis=InvestmentThesis(summary="placeholder"),
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
    return ResearchContext(investment_case=case, dcf_result=dcf_result)


def test_generate_thesis_with_valid_draft_resolves_traceable_evidence() -> None:
    evidence = _evidence()
    context = _context([evidence])
    provider = FakeLLMProvider(
        content={
            "summary": "Durable moat in EUV lithography.",
            "supporting_evidence_ids": [str(evidence.evidence_id)],
            "key_assumptions": ["EUV demand persists"],
            "key_risks": ["Export restrictions"],
            "invalidation_conditions": ["Major customer cancels multi-year order"],
        },
        prompt_tokens=120,
        completion_tokens=80,
        latency_ms=42.0,
    )

    thesis = generate_thesis(context, provider)

    assert thesis.summary == "Durable moat in EUV lithography."
    assert thesis.supporting_evidence == [evidence]
    assert thesis.key_assumptions == ["EUV demand persists"]
    assert thesis.key_risks == ["Export restrictions"]
    assert thesis.invalidation_conditions == ["Major customer cancels multi-year order"]


def test_generate_thesis_rejects_untraceable_evidence_id() -> None:
    context = _context([_evidence()])
    provider = FakeLLMProvider(
        content={
            "summary": "Fabricated claim.",
            "supporting_evidence_ids": [str(uuid4())],
        }
    )

    with pytest.raises(ValueError, match="unknown evidence_id"):
        generate_thesis(context, provider)


def test_generate_thesis_rejects_schema_invalid_response() -> None:
    context = _context([_evidence()])
    provider = FakeLLMProvider(content={"key_assumptions": ["missing summary field"]})

    with pytest.raises(ValidationError):
        generate_thesis(context, provider)


def test_generate_thesis_propagates_provider_error_without_fabricating_thesis() -> None:
    context = _context([_evidence()])
    provider = FakeLLMProvider(error=TimeoutError("provider timed out"))

    with pytest.raises(TimeoutError, match="provider timed out"):
        generate_thesis(context, provider)


def test_generate_thesis_logs_token_usage_and_latency(
    caplog: pytest.LogCaptureFixture,
) -> None:
    context = _context([_evidence()])
    provider = FakeLLMProvider(
        content={"summary": "No supporting detail yet."},
        prompt_tokens=120,
        completion_tokens=80,
        latency_ms=42.0,
    )

    with caplog.at_level("INFO", logger="aic.research.generator"):
        generate_thesis(context, provider)

    records = [r for r in caplog.records if r.message == "thesis generation completed"]
    assert len(records) == 1
    assert records[0].prompt_tokens == 120
    assert records[0].completion_tokens == 80
    assert records[0].latency_ms == 42.0


def test_generate_thesis_succeeds_with_zero_supplied_evidence() -> None:
    context = _context([])
    provider = FakeLLMProvider(
        content={
            "summary": "No supporting detail yet.",
            "supporting_evidence_ids": [],
        }
    )

    thesis = generate_thesis(context, provider)

    assert thesis.summary == "No supporting detail yet."
    assert thesis.supporting_evidence == []
