from aic.committee.context import CommitteeAdjudicationContext
from aic.domain import AnalysisAssessment

_SYSTEM_PROMPT = (
    "You are the chair of an investment committee. Given a company's investment case "
    "(thesis and evidence), an already-computed discounted cash flow (DCF) valuation, and "
    "independently-produced bull and bear assessments, adjudicate a committee decision.\n\n"
    "Rules:\n"
    "- Do not perform, request, or infer any financial calculation. Valuation figures are "
    "supplied to you as already-computed, read-only context.\n"
    "- Do not simply average the bull and bear assessments' confidence or conclusions. "
    "You must explicitly identify where they disagree and explain how you weighed each "
    "point.\n"
    "- You must identify: the central investment thesis, the key disagreements between the "
    "bull and bear cases, how the valuation bears on the decision, the downside risks, and "
    "the invalidation conditions — each as its own separate field.\n"
    "- Restrict your recommendation to exactly one of: BUY, WATCH, AVOID.\n"
    "- Reference supporting evidence only by its evidence_id from the supplied evidence "
    "list. Never invent an evidence_id.\n"
    "- If you do not fully adopt the bull or the bear position, record the unadopted "
    "position as dissent. If the two sides are materially aligned, leave dissent empty "
    "rather than inventing a disagreement."
)


def _render_evidence(context: CommitteeAdjudicationContext) -> str:
    entries = context.investment_case.evidence
    if not entries:
        return "(no evidence supplied)"
    lines = [
        f"- evidence_id={item.evidence_id} source={item.source!r} title={item.title!r} "
        f"type={item.evidence_type.value} excerpt={item.excerpt!r}"
        for item in entries
    ]
    return "\n".join(lines)


def _render_assessment(assessment: AnalysisAssessment) -> str:
    return (
        f"conclusion={assessment.conclusion!r} confidence={assessment.confidence!r}\n"
        f"arguments={assessment.arguments!r}\n"
        f"assumptions={assessment.assumptions!r}\n"
        f"risks={assessment.risks!r}"
    )


def _render_dcf_result(context: CommitteeAdjudicationContext) -> str:
    result = context.dcf_result
    return (
        f"enterprise_value={result.enterprise_value!r}\n"
        f"equity_value={result.equity_value!r}\n"
        f"implied_value_per_share={result.implied_value_per_share!r}\n"
        f"terminal_value={result.terminal_value!r}\n"
        f"pv_terminal_value={result.pv_terminal_value!r}"
    )


def build_prompt(context: CommitteeAdjudicationContext) -> tuple[str, str]:
    company = context.investment_case.company
    thesis = context.investment_case.thesis
    user_prompt = (
        f"Company: {company.name} ({company.ticker}), {company.exchange}, "
        f"{company.sector} / {company.industry}, {company.country}\n\n"
        f"Investment thesis summary: {thesis.summary!r}\n"
        f"Thesis key assumptions: {thesis.key_assumptions!r}\n"
        f"Thesis key risks: {thesis.key_risks!r}\n"
        f"Thesis invalidation conditions: {thesis.invalidation_conditions!r}\n\n"
        f"Evidence:\n{_render_evidence(context)}\n\n"
        f"DCF result (read-only, already computed):\n{_render_dcf_result(context)}\n\n"
        f"Bull assessment:\n{_render_assessment(context.bull_assessment)}\n\n"
        f"Bear assessment:\n{_render_assessment(context.bear_assessment)}"
    )
    return _SYSTEM_PROMPT, user_prompt
