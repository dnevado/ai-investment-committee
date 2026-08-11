from aic.research.context import ResearchContext

_SYSTEM_PROMPT = (
    "You are an investment research assistant. Given a company's financial snapshots, "
    "supporting evidence, and an already-computed discounted cash flow (DCF) valuation, "
    "synthesize a structured investment thesis.\n\n"
    "Rules:\n"
    "- Do not perform, request, or infer any financial calculation. Valuation figures are "
    "supplied to you as already-computed, read-only context.\n"
    "- Reference supporting evidence only by its evidence_id from the supplied evidence "
    "list. Never invent an evidence_id, and never reproduce or paraphrase evidence content "
    "as if it were new evidence.\n"
    "- Do not produce an investment recommendation (BUY/WATCH/AVOID) or any Bull/Bear "
    "committee assessment.\n"
    "- Respond with a summary, key assumptions, key risks, and invalidation conditions "
    "grounded only in the supplied context."
)


def _render_evidence(context: ResearchContext) -> str:
    entries = context.investment_case.evidence
    if not entries:
        return "(no evidence supplied)"
    lines = [
        f"- evidence_id={item.evidence_id} source={item.source!r} title={item.title!r} "
        f"type={item.evidence_type.value} excerpt={item.excerpt!r}"
        for item in entries
    ]
    return "\n".join(lines)


def _render_financial_snapshots(context: ResearchContext) -> str:
    lines = [
        f"- as_of={snapshot.as_of.isoformat()} "
        f"revenue={snapshot.revenue!r} operating_income={snapshot.operating_income!r} "
        f"net_income={snapshot.net_income!r} free_cash_flow={snapshot.free_cash_flow!r} "
        f"cash={snapshot.cash!r} debt={snapshot.debt!r} "
        f"shares_outstanding={snapshot.shares_outstanding!r}"
        for snapshot in context.investment_case.financial_snapshots
    ]
    return "\n".join(lines)


def _render_dcf_result(context: ResearchContext) -> str:
    result = context.dcf_result
    return (
        f"enterprise_value={result.enterprise_value!r}\n"
        f"equity_value={result.equity_value!r}\n"
        f"implied_value_per_share={result.implied_value_per_share!r}\n"
        f"terminal_value={result.terminal_value!r}\n"
        f"pv_terminal_value={result.pv_terminal_value!r}"
    )


def build_prompt(context: ResearchContext) -> tuple[str, str]:
    company = context.investment_case.company
    user_prompt = (
        f"Company: {company.name} ({company.ticker}), {company.exchange}, "
        f"{company.sector} / {company.industry}, {company.country}\n\n"
        f"Financial snapshots:\n{_render_financial_snapshots(context)}\n\n"
        f"Evidence:\n{_render_evidence(context)}\n\n"
        f"DCF result (read-only, already computed):\n{_render_dcf_result(context)}"
    )
    return _SYSTEM_PROMPT, user_prompt
