from aic.domain import InvestmentThesis


def _render_list(items: list[str]) -> str:
    if not items:
        return "(none)"
    return "\n".join(f"- {item}" for item in items)


def render_thesis_document(thesis: InvestmentThesis) -> str:
    evidence_lines = (
        "\n".join(
            f"- [{item.evidence_type.value}] {item.title} ({item.source}, "
            f"{item.retrieved_date.isoformat()}): {item.excerpt}"
            for item in thesis.supporting_evidence
        )
        or "(none)"
    )
    return (
        "# Investment Thesis\n\n"
        "## Summary\n\n"
        f"{thesis.summary}\n\n"
        "## Supporting Evidence\n\n"
        f"{evidence_lines}\n\n"
        "## Key Assumptions\n\n"
        f"{_render_list(thesis.key_assumptions)}\n\n"
        "## Key Risks\n\n"
        f"{_render_list(thesis.key_risks)}\n\n"
        "## Invalidation Conditions\n\n"
        f"{_render_list(thesis.invalidation_conditions)}\n"
    )
