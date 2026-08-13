from uuid import uuid4

from aic.bullbear import (
    BullBearContext,
    generate_bear_assessment,
    generate_bull_assessment,
)
from aic.committee import CommitteeAdjudicationContext, generate_decision
from aic.dcf import compute_dcf, to_valuation_result
from aic.domain import InvestmentCase, InvestmentThesis
from aic.report import CommitteeReport, render_report_document
from aic.research import ResearchContext, generate_thesis
from aic.research.provider import LLMProvider
from aic.workflow.input import WorkflowInput
from aic.workflow.result import WorkflowResult

_VALUATION_CONFIDENCE = 1.0


def run_investment_workflow(input: WorkflowInput, provider: LLMProvider) -> WorkflowResult:
    dcf_result = compute_dcf(input.dcf_assumptions)

    placeholder_thesis = InvestmentThesis(summary="Pending research")
    initial_case = InvestmentCase(
        case_id=uuid4(),
        company=input.company,
        financial_snapshots=input.financial_snapshots,
        thesis=placeholder_thesis,
        evidence=input.evidence,
    )

    research_context = ResearchContext(investment_case=initial_case, dcf_result=dcf_result)
    thesis = generate_thesis(research_context, provider)

    case = initial_case.model_copy(update={"thesis": thesis})

    latest_snapshot_date = max(
        snapshot.as_of for snapshot in input.financial_snapshots
    )
    valuation_result = to_valuation_result(
        dcf_result,
        valuation_id=uuid4(),
        valuation_date=latest_snapshot_date,
        confidence=_VALUATION_CONFIDENCE,
    )

    bullbear_context = BullBearContext(
        investment_case=case, valuation_result=valuation_result
    )
    bull_assessment = generate_bull_assessment(bullbear_context, provider)
    bear_assessment = generate_bear_assessment(bullbear_context, provider)

    adjudication_context = CommitteeAdjudicationContext(
        investment_case=case,
        dcf_result=dcf_result,
        bull_assessment=bull_assessment,
        bear_assessment=bear_assessment,
    )
    decision = generate_decision(adjudication_context, provider)
    decision = decision.model_copy(
        update={"valuation_reference": valuation_result.valuation_id}
    )

    report = CommitteeReport(
        company=input.company,
        financial_snapshots=input.financial_snapshots,
        thesis=thesis,
        dcf_result=dcf_result,
        assessment=bull_assessment,
        bull_assessment=bull_assessment,
        bear_assessment=bear_assessment,
        decision=decision,
    )
    document = render_report_document(report)

    return WorkflowResult(
        dcf_result=dcf_result,
        valuation_result=valuation_result,
        thesis=thesis,
        bull_assessment=bull_assessment,
        bear_assessment=bear_assessment,
        decision=decision,
        report=report,
        document=document,
    )
