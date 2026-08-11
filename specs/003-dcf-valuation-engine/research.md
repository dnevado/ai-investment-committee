# Phase 0 Research: Deterministic DCF Valuation Engine

Every Technical Context item was resolvable from the spec (including its Clarifications
session), the constitution, and the existing 002-domain-model baseline. No open
`NEEDS CLARIFICATION` markers remain.

## Decision: A new `aic.dcf` sub-package, not `aic.domain`

- **Decision**: Place `DCFAssumptions`, `ForecastYear`, `DCFResult`, `YearResult`, and
  `compute_dcf()` in a new sibling sub-package `src/aic/dcf/`, not inside
  `src/aic/domain/`.
- **Rationale**: `aic.domain` (002-domain-model) is deliberately computation-free — pure
  typed data plus validation, no financial calculation (its own FR-017 equivalent). This
  feature is the opposite: it *is* the calculation. Constitution Principle II ("LLM
  Proposes, Code Computes") and the "Business logic... MUST live in domain/application
  modules" architecture rule both point to a distinct module for computation, keeping
  `aic.domain`'s "shape only, no calculation" property intact for every future consumer.
  The name `dcf` (rather than `valuation`) was chosen specifically to avoid colliding
  with the already-existing `aic.domain.valuation` module, which defines the shape-only
  `ValuationResult` — `aic.valuation` would have been a plausible name in isolation, but
  reads ambiguously right next to `aic.domain.valuation` in the same codebase.
- **Alternatives considered**: Adding the calculation function directly inside
  `aic.domain.valuation` (the existing `ValuationResult` module) — rejected, since it
  would silently turn a previously computation-free module into one with business logic,
  contradicting 002's established design and its own FR-017. A generic
  `aic.valuation` package name — rejected for the naming-collision reason above.

## Decision: `Decimal` arithmetic, computed via Python's `decimal` module directly

- **Decision**: All arithmetic (EBIT, NOPAT, FCFF, discounting, terminal value,
  aggregation) is performed using `decimal.Decimal`, using Python's default decimal
  context (28 significant digits of precision) with no explicit context override.
  Discount factors `(1 + rate) ** year` use Python's native `Decimal.__pow__`, which is
  exact for the integer exponents this feature always uses (forecast year indices).
- **Rationale**: FR-021 requires exact decimal arithmetic, never binary floating-point,
  consistent with the `Money` type's `Decimal` amount from 002-domain-model. 28
  significant digits is far more precision than any realistic financial input needs, so
  the default context requires no tuning. Because every exponent in this feature is a
  small positive integer (the forecast year number, or `N`), `Decimal ** int` is computed
  by repeated exact multiplication — no transcendental/irrational-approximation step is
  ever needed, so no precision loss occurs before the final, deliberate rounding step.
- **Alternatives considered**: `float` — rejected outright by FR-021 (binary
  floating-point representation error is exactly what this feature must avoid). A custom
  `decimal.Context` with higher/lower precision — rejected as unnecessary; the default
  28-digit context already exceeds what any realistic monetary or rate value requires.

## Decision: Rounding policy implementation

- **Decision**: A single internal helper rounds a `Decimal` to 2 decimal places using
  `ROUND_HALF_UP` (`Decimal.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)`), applied
  **only** at the point each value is placed into the final `DCFResult` (per-year FCFF
  and PV(FCFF), Terminal Value, PV(Terminal Value), Enterprise Value, Equity Value,
  Implied Value Per Share). Every intermediate computation (e.g., the running sum of
  PV(FCFF) that feeds into Enterprise Value) uses the full-precision, unrounded value.
- **Rationale**: Directly implements FR-022 and matches the worked Reference Case in
  spec.md, which was computed exactly this way (e.g., Enterprise Value sums the
  *unrounded* per-year PV(FCFF) values, not the values as individually displayed to 2
  decimal places). Rounding every field independently as it's produced, rather than only
  at final construction, would compound rounding error across the multi-step pipeline —
  exactly what FR-022 prohibits.
- **Alternatives considered**: Rounding each per-year PV(FCFF) immediately after
  computing it, then summing the rounded values for Enterprise Value — rejected; produces
  a very slightly different Enterprise Value than the spec's Reference Case in the
  general case (they happen to agree in the worked example, but the *policy*, not a
  coincidence, must be the definition — see spec.md Reference Case). Banker's rounding
  (`ROUND_HALF_EVEN`) instead of `ROUND_HALF_UP` — rejected; FR-022 explicitly specifies
  round-half-up.

## Decision: Rates and counts stay plain `Decimal`, not `Money`

- **Decision**: Operating Margin, Tax Rate, WACC, and Terminal Growth Rate are plain
  `Decimal` (dimensionless fractions, e.g. `Decimal("0.10")` for 10%). Shares Outstanding
  is also a plain `Decimal` (a count, not a monetary amount).
- **Rationale**: `Money` bundles an amount with a currency; a rate or a share count has
  no currency, so wrapping it in `Money` would be meaningless and would violate FR-020's
  "monetary inputs/outputs share one currency" framing by implying these fields need a
  currency too. This mirrors 002-domain-model's own precedent — `FinancialSnapshot.
  shares_outstanding` is a plain `Decimal`, not `Money`, for exactly this reason.
- **Alternatives considered**: A dedicated `Rate` or `Percentage` value type — rejected
  as unnecessary complexity for an MVP explicitly scoped to be "the smallest
  implementation capable of validating the product hypothesis"; a plain, range-validated
  `Decimal` field is sufficient and directly matches how `FinancialSnapshot` already
  handles its one non-monetary numeric field.

## Decision: Validation lives on `DCFAssumptions` itself, not deferred to `compute_dcf`

- **Decision**: All of FR-014 through FR-020 (WACC > terminal growth, WACC > 0, forecast
  length ≥ 1, shares outstanding > 0, no missing required fields, single shared
  currency) are enforced as Pydantic field/model validators on `DCFAssumptions`, so an
  invalid assumption set can never be constructed in the first place.
  `compute_dcf(assumptions: DCFAssumptions) -> DCFResult` can therefore trust its input
  is already valid, and only needs a final defensive check that no computed intermediate
  or output value is non-finite (FR-019) before constructing `DCFResult`.
- **Rationale**: Matches 002-domain-model's established pattern exactly (e.g.,
  `FinancialSnapshot`'s cross-metric currency-consistency `model_validator`) — invalid
  data is rejected at construction time, not at first use. This keeps `compute_dcf` a
  simple, pure, easy-to-test function: valid input in, deterministic result out, with no
  validation branching cluttering the arithmetic.
- **Alternatives considered**: Validating inside `compute_dcf` instead of on the model —
  rejected because it would allow an "invalid" `DCFAssumptions` instance to exist
  transiently (contradicting the "construction fails explicitly" pattern established for
  every other domain model in this codebase) and would mix validation logic into the
  calculation function.

## Decision: `ValuationResult` compatibility via an explicit adapter function

- **Decision**: `aic.dcf.engine` exposes `to_valuation_result(result: DCFResult, *,
  valuation_id: UUID, valuation_date: date, method: str = "DCF (FCFF)", confidence:
  float, assumption_evidence_refs: list[UUID] = []) -> ValuationResult`, which maps
  `DCFResult.implied_value_per_share` into `ValuationResult.estimated_value` and carries
  the caller-supplied identity/metadata fields `ValuationResult` requires (per
  002-domain-model, identifiers are caller-supplied, never auto-generated).
- **Rationale**: Directly satisfies FR-026 ("directly usable as, or losslessly
  convertible to, `ValuationResult.estimated_value`") without polluting the pure
  `compute_dcf` function with `ValuationResult`-specific metadata (`valuation_id`,
  `confidence`, evidence references) that a DCF calculation itself has no way to know.
- **Alternatives considered**: Having `compute_dcf` return a `ValuationResult` directly —
  rejected, since `ValuationResult` requires fields (`valuation_id`, `confidence`,
  evidence references) that are not DCF-calculation outputs and would force
  `compute_dcf` to either fabricate them or accept them as pass-through parameters,
  muddying its signature; a separate adapter keeps each function's responsibility clean.
