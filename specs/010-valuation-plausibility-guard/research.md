# Research: Valuation Plausibility Guard

## Decision 1: Reconciling feature 003's "negative FCFF is allowed" edge case

**Decision**: Feature 010 narrows feature 003's Edge Cases text. Negative FCFF in an
*interim* forecast year remains allowed and unchanged. Negative (or zero) FCFF in the
*terminal* forecast year — the year that anchors the perpetuity-growth terminal value — is
now rejected. `tests/unit/dcf/test_engine.py::test_negative_fcff_year_is_allowed` (a
single-forecast-year case, where that one year is necessarily both interim and terminal) is
rewritten to a multi-year forecast with a negative *interim* year and a positive terminal
year, preserving the original test's intent (interim losses are fine) without contradicting
the new guard. `specs/003-dcf-valuation-engine/spec.md`'s Edge Cases bullet is amended with
a note pointing to this feature.

**Rationale**: Confirmed directly with the user during planning (explicit user requirement
outranks a prior spec per the constitution's own conflict-resolution order). A single-year
DCF whose only year is negative has no "recovery" year to average against — the terminal
value is built directly off that negative number, which is the exact defect this feature
exists to close (Enterprise Value: -$351.5B on the Amazon dataset). An interim-year dip
followed by recovery (e.g., one heavy investment year) is a real, common, and already
correctly-modeled scenario (the PV sum already reflects it) and is explicitly preserved as
an Edge Case in spec.md.

**Alternatives considered**:
- *Only guard multi-year forecasts, leave single-year forecasts unchecked*: rejected —
  produces an arbitrary, inconsistent rule (a 1-year forecast is not inherently less
  "real" than a 3-year one; the whole point is that the terminal year anchors the perpetuity
  regardless of how many years precede it).
- *Leave 003 untouched and make the new guard opt-in/configurable*: rejected — defeats the
  purpose (silently accepting an implausible result is exactly what this feature must stop
  doing by default), and CLAUDE.md/constitution discourage feature flags for
  behavior that should just be correct.

## Decision 2: Guard conditions and error format

**Decision**: Inside `compute_dcf`, after computing `fcff_final` (already computed today)
and `enterprise_value` (already computed today), add two unconditional checks, in this
order:

1. `if fcff_final <= 0: raise ValueError(f"Terminal-year FCFF is not positive: {fcff_final}. ...")`
2. `if enterprise_value <= 0: raise ValueError(f"Enterprise value is not positive: {enterprise_value}. ...")`

Both checks run on the *unrounded* `Decimal` values already held in local variables,
before `DCFResult` is constructed — so a rejected computation never produces a partially-built
`DCFResult`. Each message names the check, states the offending computed figure, and
briefly states why it's rejected (satisfies FR-003/SC-003 without requiring a new custom
exception type — `ValueError` matches this module's existing convention, e.g.
`_round_money`'s non-finite check and `DCFAssumptions`'s `wacc`/currency validators).

**Rationale**: Reuses the exact mechanism (`ValueError`, raised eagerly, no new exception
hierarchy) already used elsewhere in this codebase for "reject before returning a usable
value" (Constitution VIII — minimal architecture; no new infrastructure). Checking
`fcff_final` before `enterprise_value` gives the more specific, more actionable error first
when both would fail (a broken terminal FCFF is the more direct/root cause; a downstream
negative EV largely reachable only through it or through extreme near-term losses is a
secondary net).

**Alternatives considered**:
- *A dedicated `ImplausibleValuationError` subclass*: rejected as unnecessary — no existing
  caller catches DCF errors selectively (compute_dcf's existing WACC/currency errors are
  also plain `ValueError`, and `run_investment_workflow` deliberately lets all stage errors
  propagate unmodified per 009's contract), so a new type adds a public API surface with no
  current consumer.
- *Returning a result with a `is_plausible: bool` flag instead of raising*: rejected — spec's
  FR-004/FR-009 explicitly require no `DCFResult`/downstream artifact to be producible from
  a failing computation; a flag-and-continue design would let a caller ignore the flag,
  reintroducing the exact silent-acceptance failure mode this feature exists to close.

## Decision 3: Rebalancing the Amazon reference dataset's capex assumption

**Decision**: In `scripts/mvp_amazon_validation.py`, fade the forecast capex-to-revenue
ratio down from a still-elevated 15% in Y1 to 12% in Y2 to 10% in Y3, instead of holding
FY2025's actual ~18.4% ratio flat across all three years. Revenue, D&A, and ΔNWC forecast
figures are unchanged (they were never the problem). This produces:

| Year | Revenue | Capex | Capex/Rev | FCFF |
|---|---|---|---|---|
| Y1 | $795,786M | $119,368M | 15.0% | ≈ +$8.1B |
| Y2 | $875,365M | $105,044M | 12.0% | ≈ +$35.2B |
| Y3 | $954,148M | $95,415M | 10.0% | ≈ +$57.5B |

resulting in Enterprise Value ≈ +$843B, Equity Value ≈ +$813B, and a strictly positive
implied value per share — passing FR-001/FR-002/FR-007 (the reference case must itself
clear the new guard). Operating margin (12%), tax rate (19.7%), WACC (9%), and terminal
growth (3%) are unchanged from the original dataset — they were not the source of the
defect.

**Rationale**: FY2025's ~18.4% capex/revenue ratio (and the cited 2026 guidance of an even
higher ~$220B) reflects a specific, disclosed, temporarily elevated AI-infrastructure
buildout cycle, not Amazon's steady-state capital intensity — Amazon's pre-surge
capex/revenue ratio ran closer to 10-13% in prior years. Fading the ratio down over the
3-year explicit forecast toward that more normal level is standard DCF modeling practice
for a company in an identified, disclosed investment cycle, and keeps every input evidenced
and labeled as a forward-looking ASSUMPTION (constitution Principle I/V/VII) rather than
inventing new "facts." This was presented to the user as the recommended option in an
earlier discussion this session (before the ad hoc question was superseded by moving this
work into the spec-driven flow); it remains the best-supported choice and requires no
further clarification per spec.md's own Assumptions section ("resolved during
planning/implementation, not a new valuation methodology").

**Alternatives considered**:
- *Raise operating margin instead of fading capex*: rejected as primary approach — would
  require a margin (~15%+) at the aggressive end of the cited analyst range merely to
  offset an assumption (flat elevated capex) that is itself not well-supported as a
  steady-state; fading capex is the more defensible single change.
- *Extend the explicit forecast horizon until FCFF turns positive*: rejected — a bigger
  change to this project's existing "N-year forecast + terminal value" convention than this
  feature's scope calls for; not requested.

## Decision 4: Scope of `scripts/mvp_amazon_validation.py` changes

**Decision**: Only the `assumptions.forecast[*].capital_expenditure` values and their
surrounding `ev_capex_actual`/assumption-related comments change. `ev_margin_assumption`,
`ev_wacc_assumption`, `ev_terminal_growth_assumption`, and all FACT/CALCULATION evidence
entries are unchanged. No new evidence entry is required (capex forecast reasoning is
additive detail on the existing `ev_capex_actual` evidence's excerpt).

**Rationale**: Minimizes the diff to exactly the figures that were wrong, per CLAUDE.md's
"only necessary files MUST be modified" and "no invented financial data" — the historical
actuals and other assumptions were already correct and evidenced; only the capex forecast
assumption's *design* was flawed.
