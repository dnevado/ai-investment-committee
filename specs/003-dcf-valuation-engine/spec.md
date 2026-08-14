# Feature Specification: Deterministic DCF Valuation Engine

**Feature Branch**: `003-dcf-valuation-engine`

**Created**: 2026-08-10

**Status**: Draft

**Input**: User description: "A deterministic Python DCF engine that calculates intrinsic equity value from explicit financial assumptions. FCFF-based MVP: explicit N-year forecast, WACC discounting, Gordon Growth terminal value, Enterprise Value, Equity Value, Implied Value Per Share. Completely independent of OpenAI, LangChain, LangGraph, AWS, market-data providers, and external I/O — the LLM never performs financial arithmetic; the engine receives validated structured inputs and computes deterministically in Python. Must reject economically incoherent or missing assumptions explicitly rather than inventing them, define its own precision/rounding policy, include a canonical reference case for independent verification, and produce a result compatible with the existing AIC `ValuationResult` domain contract."

## Clarifications

### Session 2026-08-10

- Q: Are Operating Margin and Tax Rate single values applied to every forecast year, or does the caller supply one value per forecast year (like Revenue)? → A: Single constant value applied to every forecast year.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Compute Enterprise Value, Equity Value, and Implied Value Per Share (Priority: P1)

A developer building the AIC valuation workflow needs to turn a complete, explicit set of
financial assumptions (a multi-year FCFF forecast, a discount rate, a terminal growth rate, and
balance-sheet figures) into a deterministic Enterprise Value, Equity Value, and Implied Value Per
Share — with no LLM involved in the arithmetic.

**Why this priority**: This is the entire product hypothesis of the feature. Without a working,
correct calculation, nothing else in this feature has value.

**Independent Test**: Supply a complete, valid set of assumptions and confirm the engine returns
an Enterprise Value, Equity Value, and Implied Value Per Share that match hand-computed values for
the same inputs.

**Acceptance Scenarios**:

1. **Given** a complete set of valid assumptions (per-year revenue, D&A, capital expenditure, and
   change in net working capital for an explicit forecast period; operating margin; tax rate;
   WACC; terminal growth rate; cash; debt; shares outstanding), **When** the engine computes a
   result, **Then** it returns the per-year FCFF, per-year present value of FCFF, terminal value,
   present value of terminal value, Enterprise Value, Equity Value, and Implied Value Per Share.
2. **Given** the same valid assumptions, **When** the calculation is run multiple times, **Then**
   every run produces byte-identical output (fully deterministic, no randomness).
3. **Given** valid assumptions, **When** the engine computes a result, **Then** every monetary
   output value is expressed with an explicit currency, consistent with the currency of the
   monetary inputs.

---

### User Story 2 - Reject Invalid or Economically Incoherent Assumptions Explicitly (Priority: P2)

A developer needs the engine to refuse to produce a number at all when the supplied assumptions
are missing, incomplete, or economically incoherent (e.g., a discount rate that does not exceed
the terminal growth rate) — rather than silently producing a misleading result.

**Why this priority**: A DCF engine that can be coerced into producing a plausible-looking but
meaningless number is more dangerous than one that produces no number at all. This directly
depends on User Story 1's calculation existing first.

**Independent Test**: Supply assumption sets that each violate exactly one validation rule (e.g.,
WACC equal to terminal growth, zero shares outstanding, an empty forecast period, a missing
required assumption) and confirm each is rejected with an explicit, specific error and no
numeric result is produced.

**Acceptance Scenarios**:

1. **Given** a WACC that is not strictly greater than the terminal growth rate, **When** the
   engine attempts a calculation, **Then** it fails explicitly and produces no result.
2. **Given** a WACC that is zero or negative, **When** the engine attempts a calculation, **Then**
   it fails explicitly and produces no result.
3. **Given** an empty forecast period (zero years), **When** the engine attempts a calculation,
   **Then** it fails explicitly and produces no result.
4. **Given** shares outstanding that is zero or negative, **When** the engine attempts a
   calculation, **Then** it fails explicitly and produces no result.
5. **Given** an assumption set with one required value missing, **When** the engine attempts a
   calculation, **Then** it fails explicitly rather than substituting an invented default.
6. **Given** an assumption set where the monetary inputs do not all share the same currency,
   **When** the engine attempts a calculation, **Then** it fails explicitly.

---

### User Story 3 - Verify Engine Correctness Against a Canonical Reference Case (Priority: P3)

A developer or reviewer needs a small, documented, hand-verifiable example — known inputs and
known expected outputs — to independently confirm the engine's implementation matches this
specification, without having to trust the implementation alone.

**Why this priority**: Establishes trust and a regression baseline, but only matters once the
calculation (Story 1) and its guardrails (Story 2) already exist.

**Independent Test**: Feed the documented reference case's inputs into the engine and confirm
every output value matches the documented expected outputs exactly (to the stated rounding
precision).

**Acceptance Scenarios**:

1. **Given** the reference case's documented inputs (see Reference Case section below), **When**
   the engine computes a result, **Then** every output value (per-year FCFF, per-year PV(FCFF),
   terminal value, PV(terminal value), Enterprise Value, Equity Value, Implied Value Per Share)
   matches the documented expected value exactly.

---

### Edge Cases

- What happens when the forecast period is exactly one year? Enterprise Value is the present
  value of that single year's FCFF plus the present value of the terminal value computed from
  that same year's FCFF — the formulas apply unchanged with N = 1.
- What happens when a forecast year's FCFF is negative (e.g., capital expenditure exceeds NOPAT
  plus D&A)? This is allowed and not an error — it simply contributes a negative present value to
  Enterprise Value, reflecting a real (if unusual) business situation. **Amended by feature
  010 (`specs/010-valuation-plausibility-guard/spec.md`)**: this only holds for an *interim*
  (non-terminal) forecast year. A non-positive FCFF in the *terminal* forecast year — the
  year that anchors the perpetuity-growth terminal value — is rejected as an error, because a
  non-positive sustaining cash flow makes the terminal value economically meaningless.
- What happens when Debt exceeds Enterprise Value plus Cash, producing a negative Equity Value or
  a negative Implied Value Per Share? This is allowed and not an error — it is a valid (if
  alarming) output reflecting the supplied assumptions, not a condition this feature treats as
  invalid input.
- What happens when the terminal growth rate is negative (a declining perpetuity)? This is
  allowed — only "terminal growth rate strictly less than WACC" is enforced, not a minimum value.
- What happens when an intermediate or final computed value would be NaN or infinite (e.g., a
  pathological combination that produces division by zero despite passing the WACC/terminal
  growth check)? The engine fails explicitly rather than returning a non-finite number.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The engine SHALL accept an explicit, multi-year forecast covering the entire
  forecast period, with per-year Revenue, per-year Depreciation & Amortization, per-year Capital
  Expenditure, and per-year Change in Net Working Capital each expressed as a `Money` value (the
  existing domain type), all sharing one common currency.
- **FR-002**: The engine SHALL accept Operating Margin and Tax Rate as single, constant
  dimensionless rates, each applied uniformly to every year of the explicit forecast period (not
  a per-year series).
- **FR-003**: The engine SHALL accept a single WACC (discount rate) and a single Terminal Growth
  Rate, each as an explicit dimensionless rate applying to the whole forecast.
- **FR-004**: The engine SHALL accept Cash and Debt as `Money` values (same currency as the
  forecast) and Shares Outstanding as an explicit positive count.
- **FR-005**: For each forecast year, the engine SHALL compute EBIT = Revenue × Operating Margin.
- **FR-006**: For each forecast year, the engine SHALL compute NOPAT = EBIT × (1 − Tax Rate).
- **FR-007**: For each forecast year, the engine SHALL compute
  FCFF = NOPAT + D&A − Capital Expenditure − Change in Net Working Capital.
- **FR-008**: For each forecast year, the engine SHALL compute
  PV(FCFF) = FCFF ÷ (1 + WACC)^year, where `year` is the 1-indexed forecast year number.
- **FR-009**: The engine SHALL compute
  Terminal Value = FCFF_final × (1 + Terminal Growth Rate) ÷ (WACC − Terminal Growth Rate), using
  the final explicit forecast year's FCFF.
- **FR-010**: The engine SHALL compute PV(Terminal Value) = Terminal Value ÷ (1 + WACC)^N, where
  `N` is the total number of explicit forecast years.
- **FR-011**: The engine SHALL compute
  Enterprise Value = (sum of PV(FCFF) across every forecast year) + PV(Terminal Value).
- **FR-012**: The engine SHALL compute Equity Value = Enterprise Value + Cash − Debt.
- **FR-013**: The engine SHALL compute
  Implied Value Per Share = Equity Value ÷ Shares Outstanding.
- **FR-014**: The engine SHALL reject a calculation where WACC is not strictly greater than the
  Terminal Growth Rate, with an explicit error identifying the conflict.
- **FR-015**: The engine SHALL reject a calculation where WACC is not strictly positive.
- **FR-016**: The engine SHALL reject a calculation with zero explicit forecast years.
- **FR-017**: The engine SHALL reject a calculation where Shares Outstanding is not strictly
  positive.
- **FR-018**: The engine SHALL reject a calculation with any required assumption missing —
  never substituting an invented default value for material financial input.
- **FR-019**: The engine SHALL reject any calculation whose input or computed intermediate/output
  values include a NaN or infinite number, with an explicit error.
- **FR-020**: All monetary inputs (Revenue, D&A, Capital Expenditure, Change in Net Working
  Capital, Cash, Debt) and all monetary outputs (per-year PV(FCFF), Terminal Value, PV(Terminal
  Value), Enterprise Value, Equity Value, Implied Value Per Share) SHALL share one common,
  explicit currency; a mismatch SHALL be rejected explicitly.
- **FR-021**: All arithmetic SHALL be performed using exact decimal arithmetic, never binary
  floating-point, consistent with the existing `Money`/domain-model convention.
- **FR-022**: Final reported monetary output values SHALL be rounded to 2 decimal places using
  round-half-up; intermediate calculation values SHALL NOT be rounded before that final step, to
  avoid compounding rounding error across the multi-step calculation.
- **FR-023**: The engine SHALL perform no network or file I/O.
- **FR-024**: The engine SHALL have no dependency on OpenAI, LangChain, LangGraph, AWS/boto3
  SDKs, or any market-data provider SDK, and SHALL NOT call or depend on an LLM in any way.
- **FR-025**: The engine SHALL implement no probabilistic, stochastic, or Monte Carlo logic — the
  same inputs SHALL always produce the same outputs.
- **FR-026**: The engine's Implied Value Per Share output SHALL be directly usable as (or
  losslessly convertible to) the existing `ValuationResult.estimated_value` field (a `Money`
  value), without requiring any additional financial computation outside the engine.

### Key Entities

- **DCFAssumptions**: The complete, explicit input bundle for one calculation — the per-year
  forecast (Revenue, D&A, Capital Expenditure, Change in Net Working Capital), Operating Margin,
  Tax Rate, WACC, Terminal Growth Rate, Cash, Debt, and Shares Outstanding.
- **DCFResult**: The complete, deterministic output of one calculation — per-year FCFF, per-year
  PV(FCFF), Terminal Value, PV(Terminal Value), Enterprise Value, Equity Value, and Implied Value
  Per Share.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Given the documented Reference Case's inputs, the engine reproduces every documented
  expected output value exactly (to the stated 2-decimal-place rounding), 100% of the time.
- **SC-002**: 100% of calculation attempts where WACC does not strictly exceed the terminal growth
  rate are rejected explicitly, with zero numeric result ever produced.
- **SC-003**: 100% of calculation attempts with non-positive WACC, non-positive Shares
  Outstanding, or a zero-length forecast period are rejected explicitly.
- **SC-004**: 100% of calculation attempts with a missing required assumption are rejected
  explicitly rather than silently substituting a default value.
- **SC-005**: Running the same valid inputs through the engine any number of times produces
  identical output every time (100% deterministic).
- **SC-006**: Zero NaN or infinite values ever appear in a successful calculation's output.
- **SC-007**: The engine can be exercised end-to-end (assumptions in, result out) with zero
  network calls and zero file I/O.

## Reference Case (Verification Example)

A 3-year forecast, all monetary values in USD. Computed using full-precision intermediate values
(no rounding until the final reported figures); final values rounded to 2 decimal places with
round-half-up (FR-021/FR-022).

**Inputs**:

| Assumption | Value |
|---|---|
| Forecast years | 3 |
| Revenue (Year 1 / 2 / 3) | 1,000.00 / 1,100.00 / 1,210.00 |
| D&A (each year) | 50.00 |
| Capital Expenditure (each year) | 60.00 |
| Change in Net Working Capital (each year) | 10.00 |
| Operating Margin (constant) | 20% (0.20) |
| Tax Rate (constant) | 25% (0.25) |
| WACC | 10% (0.10) |
| Terminal Growth Rate | 2% (0.02) |
| Cash | 200.00 |
| Debt | 150.00 |
| Shares Outstanding | 100 |

**Expected outputs**:

| Value | Year 1 | Year 2 | Year 3 |
|---|---|---|---|
| EBIT (Revenue × 0.20) | 200.00 | 220.00 | 242.00 |
| NOPAT (EBIT × 0.75) | 150.00 | 165.00 | 181.50 |
| FCFF (NOPAT + 50 − 60 − 10) | 130.00 | 145.00 | 161.50 |
| PV(FCFF) | 118.18 | 119.83 | 121.34 |

- **Terminal Value** = 161.50 × 1.02 ÷ 0.08 = **2,059.13**
- **PV(Terminal Value)** = 2,059.125 ÷ 1.331 = **1,547.05**
- **Enterprise Value** = 118.1818... + 119.8347... + 121.3373... + 1,547.0511... = **1,906.40**
- **Equity Value** = 1,906.40... + 200.00 − 150.00 = **1,956.40**
- **Implied Value Per Share** = 1,956.40... ÷ 100 = **19.56**

## Assumptions

- **Per-year flow items are supplied explicitly, not derived**: Revenue, D&A, Capital
  Expenditure, and Change in Net Working Capital are each supplied as an explicit value for every
  forecast year (not synthesized from a single base value plus a growth rate) — consistent with
  "explicit financial assumptions" and "no invented assumptions," and the smallest implementation
  capable of validating the product hypothesis.
- **Tax Rate bounds**: Tax Rate is assumed to be constrained to the range [0, 1] (0%–100%) — a
  reasonable, low-impact default for a coherent tax rate, not explicitly stated by the source
  description.
- **Operating Margin sign**: Operating Margin is not artificially bounded to a positive range — a
  forecast year with a negative operating margin (a loss-making year) is realistic and not
  rejected by this feature.
- **No upper bound on WACC**: Only "strictly positive" is enforced; an unusually high discount
  rate (e.g., for a very risky venture) is not treated as invalid by this feature.
- **Single-currency scope**: This feature does not perform currency conversion; every monetary
  input and output in one calculation must already share one currency (FR-020), consistent with
  the "no FX conversion" exclusion in the source description.
- **No persistence, CLI, or API surface**: This feature is a pure domain/application calculation
  component, consistent with the constitution's Deterministic Valuation principle and the
  project's "no premature infrastructure" guidance — it is not wired into any CLI, API, or
  storage layer here.
- **Precision/rounding policy is authoritative**: FR-021/FR-022 (exact decimal arithmetic
  throughout; final output values rounded to 2 decimal places with round-half-up; intermediates
  left unrounded) is the definitive policy for this feature, per the explicit request to decide
  this in the specification rather than leave it to implementation choice.
