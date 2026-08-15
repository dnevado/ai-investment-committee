from datetime import date
from decimal import Decimal
from uuid import uuid4

from aic.dcf import DCFResult, YearResult
from aic.domain import (
    AnalysisAssessment,
    CommitteeDecision,
    Company,
    Evidence,
    EvidenceType,
    FinancialSnapshot,
    InvestmentThesis,
    Money,
    ValuationResult,
)
from aic.domain.enums import Recommendation
from aic.report import CommitteeReport
from aic.workflow import WorkflowResult


def make_evidence(
    evidence_type: EvidenceType = EvidenceType.FACT, title: str = "Revenue"
) -> Evidence:
    return Evidence(
        evidence_id=uuid4(),
        source="10-K",
        title=title,
        excerpt="Revenue grew 12% YoY",
        retrieved_date=date(2026, 1, 5),
        evidence_type=evidence_type,
    )


def make_workflow_result(evidence_items: list[Evidence]) -> WorkflowResult:
    company = Company(
        company_id=uuid4(),
        ticker="AMZN",
        name="Amazon.com, Inc.",
        exchange="NASDAQ",
        country="US",
        sector="Technology",
        industry="Internet Retail / Cloud",
    )
    snapshot = FinancialSnapshot(
        as_of=date(2026, 3, 31),
        revenue=Money(amount=Decimal(1000), currency="USD"),
    )
    year = YearResult(
        year=1,
        fcff=Money(amount=Decimal(100), currency="USD"),
        pv_fcff=Money(amount=Decimal(90), currency="USD"),
    )
    dcf_result = DCFResult(
        per_year=[year],
        terminal_value=Money(amount=Decimal(1000), currency="USD"),
        pv_terminal_value=Money(amount=Decimal(900), currency="USD"),
        enterprise_value=Money(amount=Decimal(990), currency="USD"),
        equity_value=Money(amount=Decimal(950), currency="USD"),
        implied_value_per_share=Money(amount=Decimal("75.07"), currency="USD"),
    )
    thesis = InvestmentThesis(
        summary="Durable moat in cloud and advertising.",
        supporting_evidence=evidence_items,
        key_assumptions=["Cloud demand persists"],
        key_risks=["Margin compression"],
        invalidation_conditions=["Major customer loss"],
    )
    bull = AnalysisAssessment(
        assessment_id=uuid4(),
        conclusion="Structural growth supports upside.",
        confidence=0.75,
        arguments=["AWS growth"],
        supporting_evidence=[item.evidence_id for item in evidence_items],
        assumptions=["Cloud demand persists"],
        risks=["Execution risk"],
    )
    bear = AnalysisAssessment(
        assessment_id=uuid4(),
        conclusion="Valuation already prices in growth.",
        confidence=0.4,
        arguments=["Multiple compression risk"],
        supporting_evidence=[item.evidence_id for item in evidence_items],
        assumptions=["Rates stay elevated"],
        risks=["Order cancellation"],
    )
    decision = CommitteeDecision(
        decision_id=uuid4(),
        recommendation=Recommendation.WATCH,
        rationale=(
            "Central thesis: Durable moat.\n\n"
            "Valuation: DCF implies fair value near current levels.\n\n"
            "Conviction: 0.82"
        ),
        referenced_evidence=[item.evidence_id for item in evidence_items],
        valuation_reference=uuid4(),
    )
    report = CommitteeReport(
        company=company,
        financial_snapshots=[snapshot],
        thesis=thesis,
        dcf_result=dcf_result,
        assessment=bull,
        bull_assessment=bull,
        bear_assessment=bear,
        decision=decision,
    )
    valuation_result = ValuationResult(
        valuation_id=decision.valuation_reference,
        method="DCF (FCFF)",
        valuation_date=snapshot.as_of,
        estimated_value=dcf_result.implied_value_per_share,
        confidence=1.0,
    )
    return WorkflowResult(
        dcf_result=dcf_result,
        valuation_result=valuation_result,
        thesis=thesis,
        bull_assessment=bull,
        bear_assessment=bear,
        decision=decision,
        report=report,
        document="rendered document",
    )
