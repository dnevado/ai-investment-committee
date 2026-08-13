from datetime import date
from decimal import Decimal
from uuid import uuid4

from aic.dcf import DCFAssumptions, ForecastYear, compute_dcf
from aic.domain import (
    AnalysisAssessment,
    CommitteeDecision,
    Company,
    Evidence,
    EvidenceType,
    FinancialSnapshot,
    InvestmentThesis,
    Money,
    Recommendation,
)
from aic.report import CommitteeReport, render_report_document


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


def _snapshot() -> FinancialSnapshot:
    return FinancialSnapshot(
        as_of=date(2026, 3, 31),
        revenue=Money(amount=Decimal(6500000000), currency="EUR"),
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


def _dcf_result() -> object:
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
    return compute_dcf(assumptions)


def _report(
    evidence: list[Evidence], dissent: list[str] | None = None
) -> CommitteeReport:
    thesis = InvestmentThesis(
        summary="Durable moat in EUV lithography",
        supporting_evidence=evidence,
        key_assumptions=["EUV demand persists"],
        key_risks=["Export restrictions"],
        invalidation_conditions=["Major customer cancels multi-year order"],
    )
    assessment = AnalysisAssessment(
        assessment_id=uuid4(),
        conclusion="Thesis is well-supported.",
        confidence=0.8,
        arguments=["Structural demand for EUV"],
        supporting_evidence=[item.evidence_id for item in evidence],
        assumptions=["EUV demand persists"],
        risks=["Export restrictions"],
    )
    decision = CommitteeDecision(
        decision_id=uuid4(),
        recommendation=Recommendation.WATCH,
        rationale="Attractive but priced for perfection.",
        referenced_thesis=thesis,
        dissent=dissent or [],
    )
    return CommitteeReport(
        company=_company(),
        financial_snapshots=[_snapshot()],
        thesis=thesis,
        dcf_result=_dcf_result(),
        assessment=assessment,
        decision=decision,
    )


def test_render_report_document_contains_exactly_the_report_content() -> None:
    evidence = _evidence()
    report = _report([evidence])

    document = render_report_document(report)

    assert report.company.name in document
    assert report.thesis.summary in document
    assert evidence.title in document
    assert evidence.excerpt in document
    assert report.thesis.key_assumptions[0] in document
    assert report.thesis.key_risks[0] in document
    assert report.thesis.invalidation_conditions[0] in document
    assert str(report.dcf_result.implied_value_per_share.amount) in document
    assert report.assessment.conclusion in document
    assert report.decision.recommendation.value in document
    assert report.decision.rationale in document


def test_render_report_document_is_deterministic() -> None:
    report = _report([_evidence()])

    first = render_report_document(report)
    second = render_report_document(report)

    assert first == second


def test_render_report_document_lists_dissent_when_present() -> None:
    report = _report([_evidence()], dissent=["Bear case underweights export risk."])

    document = render_report_document(report)

    assert "Bear case underweights export risk." in document
    assert "No dissent recorded." not in document


def test_render_report_document_states_no_dissent_when_absent() -> None:
    report = _report([_evidence()], dissent=[])

    document = render_report_document(report)

    assert "No dissent recorded." in document


def test_render_report_document_handles_empty_evidence_and_lists() -> None:
    report = _report([])

    document = render_report_document(report)

    assert "(none)" in document
