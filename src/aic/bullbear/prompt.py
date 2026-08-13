from aic.bullbear.context import BullBearContext

_BULL_SYSTEM_PROMPT = (
    "You are the Bull analyst on an investment committee. Given a company's investment "
    "case (thesis and evidence) and an already-computed valuation, identify the strongest "
    "credible upside case.\n\n"
    "Rules:\n"
    "- Do not perform, request, or infer any financial calculation. The valuation is "
    "supplied to you as already-computed, read-only context.\n"
    "- Your arguments must include the catalysts and the conditions required for the "
    "investment to outperform.\n"
    "- Your risks field should capture caveats or risks to the upside case itself, not the "
    "downside case as a whole.\n"
    "- Reference supporting evidence only by its evidence_id from the supplied evidence "
    "list. Never invent an evidence_id.\n"
    "- Do not produce an investment recommendation (BUY/WATCH/AVOID) or a committee "
    "decision — that is not your role."
)

_BEAR_SYSTEM_PROMPT = (
    "You are the Bear analyst on an investment committee. Given a company's investment "
    "case (thesis and evidence) and an already-computed valuation, independently challenge "
    "the investment thesis with the strongest credible downside case.\n\n"
    "Rules:\n"
    "- Do not perform, request, or infer any financial calculation. The valuation is "
    "supplied to you as already-computed, read-only context.\n"
    "- Your risks field must capture the downside risks, adverse scenarios, and conditions "
    "that would invalidate the thesis.\n"
    "- Your arguments must present the core case against the thesis.\n"
    "- Reference supporting evidence only by its evidence_id from the supplied evidence "
    "list. Never invent an evidence_id.\n"
    "- Do not produce an investment recommendation (BUY/WATCH/AVOID) or a committee "
    "decision — that is not your role."
)


def _render_evidence(context: BullBearContext) -> str:
    entries = context.investment_case.evidence
    if not entries:
        return "(no evidence supplied)"
    lines = [
        f"- evidence_id={item.evidence_id} source={item.source!r} title={item.title!r} "
        f"type={item.evidence_type.value} excerpt={item.excerpt!r}"
        for item in entries
    ]
    return "\n".join(lines)


def _render_thesis(context: BullBearContext) -> str:
    thesis = context.investment_case.thesis
    return (
        f"summary={thesis.summary!r}\n"
        f"key_assumptions={thesis.key_assumptions!r}\n"
        f"key_risks={thesis.key_risks!r}\n"
        f"invalidation_conditions={thesis.invalidation_conditions!r}"
    )


def _render_valuation(context: BullBearContext) -> str:
    result = context.valuation_result
    return (
        f"method={result.method!r} valuation_date={result.valuation_date.isoformat()} "
        f"estimated_value={result.estimated_value!r} confidence={result.confidence!r}"
    )


def _render_context(context: BullBearContext) -> str:
    company = context.investment_case.company
    return (
        f"Company: {company.name} ({company.ticker}), {company.exchange}, "
        f"{company.sector} / {company.industry}, {company.country}\n\n"
        f"Investment thesis:\n{_render_thesis(context)}\n\n"
        f"Evidence:\n{_render_evidence(context)}\n\n"
        f"Valuation (read-only, already computed):\n{_render_valuation(context)}"
    )


def build_bull_prompt(context: BullBearContext) -> tuple[str, str]:
    return _BULL_SYSTEM_PROMPT, _render_context(context)


def build_bear_prompt(context: BullBearContext) -> tuple[str, str]:
    return _BEAR_SYSTEM_PROMPT, _render_context(context)
