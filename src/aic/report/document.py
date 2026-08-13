from aic.domain import AnalysisAssessment, Evidence
from aic.report.report import CommitteeReport


def _render_list(items: list[str]) -> str:
    if not items:
        return "(none)"
    return "\n".join(f"- {item}" for item in items)


def _render_evidence(items: list[Evidence]) -> str:
    if not items:
        return "(none)"
    return "\n".join(
        f"- [{item.evidence_type.value}] {item.title} ({item.source}, "
        f"{item.retrieved_date.isoformat()}): {item.excerpt}"
        for item in items
    )


def _render_financial_snapshots(report: CommitteeReport) -> str:
    lines = [
        f"- as_of={snapshot.as_of.isoformat()} "
        f"revenue={snapshot.revenue!r} operating_income={snapshot.operating_income!r} "
        f"net_income={snapshot.net_income!r} free_cash_flow={snapshot.free_cash_flow!r} "
        f"cash={snapshot.cash!r} debt={snapshot.debt!r} "
        f"shares_outstanding={snapshot.shares_outstanding!r}"
        for snapshot in report.financial_snapshots
    ]
    return "\n".join(lines)


def _render_dcf_valuation(report: CommitteeReport) -> str:
    result = report.dcf_result
    per_year = "\n".join(
        f"- year={year.year} fcff={year.fcff!r} pv_fcff={year.pv_fcff!r}"
        for year in result.per_year
    )
    return (
        f"Enterprise value: {result.enterprise_value!r}\n"
        f"Equity value: {result.equity_value!r}\n"
        f"Implied value per share: {result.implied_value_per_share!r}\n"
        f"Terminal value: {result.terminal_value!r}\n"
        f"PV of terminal value: {result.pv_terminal_value!r}\n\n"
        f"Per-year free cash flow:\n{per_year}"
    )


def _render_dissent(dissent: list[str]) -> str:
    if not dissent:
        return "No dissent recorded."
    return "\n".join(f"- {item}" for item in dissent)


def _render_assessment_body(assessment: AnalysisAssessment) -> str:
    return (
        f"{assessment.conclusion}\n\n"
        f"Confidence: {assessment.confidence}\n\n"
        "### Arguments\n\n"
        f"{_render_list(assessment.arguments)}\n\n"
        "### Assumptions\n\n"
        f"{_render_list(assessment.assumptions)}\n\n"
        "### Risks\n\n"
        f"{_render_list(assessment.risks)}"
    )


def _render_assessment_section(report: CommitteeReport) -> str:
    if report.bull_assessment is not None and report.bear_assessment is not None:
        return (
            "## Bull Case Assessment\n\n"
            f"{_render_assessment_body(report.bull_assessment)}\n\n"
            "## Bear Case Assessment\n\n"
            f"{_render_assessment_body(report.bear_assessment)}"
        )
    return "## Committee Assessment\n\n" f"{_render_assessment_body(report.assessment)}"


def render_report_document(report: CommitteeReport) -> str:
    company = report.company
    thesis = report.thesis
    decision = report.decision
    return (
        f"# Investment Committee Report: {company.name} ({company.ticker})\n\n"
        f"{company.exchange}, {company.sector} / {company.industry}, {company.country}\n\n"
        "## Financial Snapshots\n\n"
        f"{_render_financial_snapshots(report)}\n\n"
        "## Investment Thesis\n\n"
        f"{thesis.summary}\n\n"
        "### Supporting Evidence\n\n"
        f"{_render_evidence(thesis.supporting_evidence)}\n\n"
        "### Key Assumptions\n\n"
        f"{_render_list(thesis.key_assumptions)}\n\n"
        "### Key Risks\n\n"
        f"{_render_list(thesis.key_risks)}\n\n"
        "### Invalidation Conditions\n\n"
        f"{_render_list(thesis.invalidation_conditions)}\n\n"
        "## DCF Valuation\n\n"
        f"{_render_dcf_valuation(report)}\n\n"
        f"{_render_assessment_section(report)}\n\n"
        "## Committee Decision\n\n"
        f"Recommendation: {decision.recommendation.value}\n\n"
        f"Rationale: {decision.rationale}\n\n"
        "### Dissent\n\n"
        f"{_render_dissent(decision.dissent)}\n"
    )
