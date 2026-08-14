"""MVP acceptance gate for feature 009 (End-to-End Investment Committee Workflow),
exercised against the real Amazon FY2025 reference dataset (mvp_amazon_dataset.py).

Unlike mvp_amazon_validation.py (a one-call thesis demo), this script runs the
*complete* pipeline via aic.workflow.run_investment_workflow — research, thesis,
bull, bear, committee, report — and then independently verifies four things no
green pytest suite proves by itself:

  1. Reproducibility   - the same DCF inputs produce an equivalent valuation.
  2. Math consistency  - FCFF/terminal value/enterprise value/equity value/
                          value-per-share reconcile via their defining identities,
                          recomputed independently of aic.dcf's own internals.
  3. Traceability       - every material conclusion (thesis, bull, bear, decision)
                          only references evidence_ids that were actually supplied.
  4. Interpretability   - the final report is not just "OK": it contains the
                          concrete figures and sections a human would check.

Prints one [PASS]/[FAIL] line per check and a final "MVP ACCEPTANCE: PASS"/"FAIL"
verdict, exiting with status 1 if any check fails. Makes real OpenAI API calls
(research + bull + bear + committee = 4 calls) using AIC_OPENAI_API_KEY.
"""

import sys
from decimal import ROUND_HALF_UP, Decimal

from mvp_amazon_dataset import build_workflow_input

from aic.dcf import compute_dcf
from aic.research import OpenAIProvider
from aic.settings import get_settings
from aic.workflow import WorkflowResult, run_investment_workflow

_CENTS = Decimal("0.01")
_TOLERANCE = Decimal("0.01")

_failures: list[str] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    if condition:
        print(f"[PASS] {name}")
    else:
        message = f"[FAIL] {name}" + (f": {detail}" if detail else "")
        print(message)
        _failures.append(name)


def close_enough(a: Decimal, b: Decimal, tolerance: Decimal = _TOLERANCE) -> bool:
    return abs(a - b) <= tolerance


def round_money(amount: Decimal) -> Decimal:
    return amount.quantize(_CENTS, rounding=ROUND_HALF_UP)


def main() -> int:
    print("=" * 70)
    print("MVP ACCEPTANCE: AMAZON (feature 009)")
    print("=" * 70)

    # -- 1. Data loaded ------------------------------------------------------
    workflow_input = build_workflow_input()
    company = workflow_input.company
    evidence = workflow_input.evidence
    assumptions = workflow_input.dcf_assumptions
    evidence_ids = {item.evidence_id for item in evidence}

    check(
        "Amazon data loaded",
        bool(company.ticker == "AMZN" and workflow_input.financial_snapshots),
        f"ticker={company.ticker!r}, snapshots={len(workflow_input.financial_snapshots)}",
    )
    check(
        "Evidence linked",
        len(evidence) > 0 and all(item.source and item.excerpt for item in evidence),
        f"{len(evidence)} evidence items",
    )

    # -- 2. Reproducibility (same inputs -> same DCFResult) ------------------
    dcf_a = compute_dcf(assumptions)
    dcf_b = compute_dcf(assumptions)
    check(
        "DCF inputs valid",
        True,  # reaching this line means DCFAssumptions/compute_dcf did not raise
    )
    check(
        "DCF reproducible (same inputs -> same result)",
        dcf_a == dcf_b,
        "two independent compute_dcf calls on identical assumptions diverged",
    )

    # -- 3. Mathematical consistency (recomputed from raw assumptions) -------
    one = Decimal(1)
    all_fcff_reconcile = True
    for year_index, (item, year_result) in enumerate(
        zip(assumptions.forecast, dcf_a.per_year, strict=True), start=1
    ):
        ebit = item.revenue.amount * assumptions.operating_margin
        nopat = ebit * (one - assumptions.tax_rate)
        expected_fcff = (
            nopat
            + item.depreciation_and_amortization.amount
            - item.capital_expenditure.amount
            - item.change_in_net_working_capital.amount
        )
        if not close_enough(round_money(expected_fcff), year_result.fcff.amount):
            all_fcff_reconcile = False
            print(
                f"       year {year_index}: expected FCFF={round_money(expected_fcff)}, "
                f"got {year_result.fcff.amount}"
            )
    check("FCFF calculations reconcile", all_fcff_reconcile)

    fcff_final = (
        dcf_a.per_year[-1].fcff.amount
        # per_year is already rounded; recompute terminal value from the same
        # rounded figure compute_dcf effectively anchors the perpetuity on.
    )
    expected_terminal_value = (
        fcff_final
        * (one + assumptions.terminal_growth_rate)
        / (assumptions.wacc - assumptions.terminal_growth_rate)
    )
    check(
        "Terminal value reconciles",
        close_enough(round_money(expected_terminal_value), dcf_a.terminal_value.amount, Decimal("1.00")),
        f"expected≈{round_money(expected_terminal_value)}, got {dcf_a.terminal_value.amount}",
    )

    sum_pv_fcff = sum((year.pv_fcff.amount for year in dcf_a.per_year), Decimal(0))
    expected_enterprise_value = sum_pv_fcff + dcf_a.pv_terminal_value.amount
    check(
        "Enterprise value reconciles",
        close_enough(round_money(expected_enterprise_value), dcf_a.enterprise_value.amount, Decimal("0.05")),
        f"Σ PV(FCFF) + PV(TV) = {round_money(expected_enterprise_value)}, "
        f"got {dcf_a.enterprise_value.amount}",
    )

    expected_equity_value = dcf_a.enterprise_value.amount + assumptions.cash.amount - assumptions.debt.amount
    check(
        "Equity value reconciles",
        close_enough(round_money(expected_equity_value), dcf_a.equity_value.amount, Decimal("0.05")),
        f"EV + Cash - Debt = {round_money(expected_equity_value)}, got {dcf_a.equity_value.amount}",
    )

    expected_value_per_share = dcf_a.equity_value.amount / assumptions.shares_outstanding
    check(
        "Value/share reconciles",
        close_enough(round_money(expected_value_per_share), dcf_a.implied_value_per_share.amount),
        f"Equity / Shares = {round_money(expected_value_per_share)}, "
        f"got {dcf_a.implied_value_per_share.amount}",
    )

    # -- 4. Run the full pipeline (real OpenAI calls: research, bull, bear, committee) --
    settings = get_settings()
    if not settings.openai_api_key:
        print("[FAIL] AIC_OPENAI_API_KEY is not configured; cannot run the full pipeline.")
        _failures.append("pipeline execution")
        return _report(len(evidence))

    provider = OpenAIProvider(api_key=settings.openai_api_key)

    try:
        result: WorkflowResult = run_investment_workflow(workflow_input, provider)
    except Exception as exc:  # noqa: BLE001 - intentionally broad: this is a gate, not app code
        print(f"[FAIL] Pipeline execution: {exc}")
        _failures.append("pipeline execution")
        return _report(len(evidence))

    check(
        "DCF reused, not recomputed differently",
        result.dcf_result == dcf_a,
        "workflow's internal DCF result diverged from the standalone computation",
    )

    # -- 5. Traceability -------------------------------------------------------
    thesis_evidence_ids = {item.evidence_id for item in result.thesis.supporting_evidence}
    check(
        "Thesis evidence is traceable",
        thesis_evidence_ids.issubset(evidence_ids),
        f"unknown evidence_ids: {thesis_evidence_ids - evidence_ids}",
    )

    bull_evidence_ids = set(result.bull_assessment.supporting_evidence)
    check(
        "Bull case evidence is traceable",
        bull_evidence_ids.issubset(evidence_ids),
        f"unknown evidence_ids: {bull_evidence_ids - evidence_ids}",
    )

    bear_evidence_ids = set(result.bear_assessment.supporting_evidence)
    check(
        "Bear case evidence is traceable",
        bear_evidence_ids.issubset(evidence_ids),
        f"unknown evidence_ids: {bear_evidence_ids - evidence_ids}",
    )

    decision_evidence_ids = set(result.decision.referenced_evidence)
    check(
        "Committee decision is traceable",
        decision_evidence_ids.issubset(evidence_ids)
        and result.decision.valuation_reference == result.valuation_result.valuation_id,
        f"unknown evidence_ids: {decision_evidence_ids - evidence_ids}; "
        f"valuation_reference={result.decision.valuation_reference}, "
        f"valuation_id={result.valuation_result.valuation_id}",
    )

    # -- 6. Financial interpretability / final report ---------------------------
    value_per_share_str = str(result.dcf_result.implied_value_per_share.amount)
    report_has_key_figures = (
        bool(result.document)
        and value_per_share_str in result.document
        and "Bull Case Assessment" in result.document
        and "Bear Case Assessment" in result.document
        and result.decision.recommendation.value in result.document
    )
    check(
        "Final report generated",
        report_has_key_figures,
        "document missing implied value/share, Bull/Bear sections, or recommendation",
    )

    return _report(len(evidence), result)


def _report(evidence_count: int, result: WorkflowResult | None = None) -> int:
    print()
    if result is not None:
        print("Company:              Amazon.com, Inc. (AMZN)")
        print(f"Evidence supplied:    {evidence_count}")
        print(f"Enterprise Value:     {result.dcf_result.enterprise_value.amount}")
        print(f"Equity Value:         {result.dcf_result.equity_value.amount}")
        print(f"Value / Share:        {result.dcf_result.implied_value_per_share.amount}")
        print(f"Recommendation:       {result.decision.recommendation.value}")
        print(f"Conviction:           {result.decision.rationale.splitlines()[-1] if result.decision.rationale else ''}")
    print()
    if _failures:
        print(f"MVP ACCEPTANCE: FAIL ({len(_failures)} check(s) failed)")
        for name in _failures:
            print(f"  - {name}")
        return 1
    print("MVP ACCEPTANCE: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
