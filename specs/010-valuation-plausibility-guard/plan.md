# Implementation Plan: Valuation Plausibility Guard

**Branch**: `010-valuation-plausibility-guard` | **Date**: 2026-08-14 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/010-valuation-plausibility-guard/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command; its definition describes the execution workflow.

## Summary

`compute_dcf` (003) currently returns any mathematically-computable `DCFResult` without
checking whether the result is economically meaningful. With a real-scale dataset (Amazon
FY2025 actuals) it is possible to supply an internally-consistent-looking assumption set
(operating margin, tax rate, WACC, terminal growth all individually valid) whose *computed*
terminal-year FCFF is negative, driving a deeply negative terminal value and enterprise
value — a result that would silently flow through research, bull/bear, committee
adjudication, and the final memo as if it were a legitimate valuation.

This feature adds two deterministic, unconditional guard checks to `compute_dcf` itself —
terminal-year FCFF must be strictly positive, and enterprise value must be strictly
positive — each raising a descriptive `ValueError` naming the failing figure. Because
`compute_dcf` already runs before any LLM call in `run_investment_workflow` (009), this
requires no orchestrator change: the guard's `ValueError` propagates and halts the pipeline
for free. The feature also rebuilds `scripts/mvp_amazon_validation.py`'s DCF assumptions so
the Amazon reference case passes both checks, and adds it as an automated, no-network
regression fixture (`tests/unit/dcf/test_amazon_reference_case.py`) alongside a
dedicated rejection-path test.

This supersedes part of feature 003's original Edge Cases text ("a forecast year's FCFF may
be negative... this is allowed and not an error") for the *terminal* year specifically, per
explicit user decision during planning (see research.md). Interim-year negative FCFF
remains allowed, unchanged.

## Technical Context

**Language/Version**: Python 3.12+ (matches repo-wide `pyproject.toml` target; no new
version requirement)

**Primary Dependencies**: None new. Reuses `pydantic` (already a dependency) only
incidentally — the guard itself is plain Python control flow inside `aic.dcf.engine`, not a
new Pydantic model, since it validates a *computed* result rather than a construction-time
input.

**Storage**: N/A — no persistence involved.

**Testing**: `pytest`, following this repo's existing no-network unit-test convention
(`tests/unit/dcf/`). `ruff check .` and `mypy src` MUST also pass (project convention).

**Target Platform**: Local CLI/script execution (Windows dev machine observed in this
session; no OS-specific behavior introduced).

**Project Type**: Single Python library/CLI project (existing `src/aic/` layout) — no new
project or service boundary.

**Performance Goals**: N/A — the guard is O(1) additional arithmetic comparisons on values
`compute_dcf` already computes; no measurable performance impact.

**Constraints**: MUST NOT change the DCF formula (FCFF, terminal value, enterprise value,
equity value, implied value per share) — Principle II/VI (LLM Proposes, Code Computes /
Deterministic Valuation) means this feature only adds a validation gate around the existing,
unchanged arithmetic. MUST NOT introduce a new dependency. MUST preserve
`test_negative_equity_value_and_implied_value_per_share_are_allowed` and
`test_negative_terminal_growth_rate_is_allowed` unmodified (only FR-001's terminal-FCFF
edge case and its regression test are being narrowed).

**Scale/Scope**: One module (`aic.dcf.engine`), one existing test file gaining/losing
specific cases, one new reference-case test file, one existing spec.md's Edge Cases note
amended, one existing validation script (`scripts/mvp_amazon_validation.py`) reworked.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Check | Result |
|---|---|---|
| I. Evidence Before Opinion | Guard doesn't touch evidence; Amazon reference dataset already classifies every figure FACT/CALCULATION/ASSUMPTION | PASS |
| II. LLM Proposes, Code Computes | Guard is pure deterministic Python inside `compute_dcf`; no LLM involvement | PASS |
| III. Structured Outputs Only | No new LLM-facing schema introduced | N/A |
| IV. Bull/Bear Symmetry | Not touched — guard fires before Bull/Bear ever run | N/A |
| V. Explicit Assumptions | Guard doesn't hide assumptions; it prevents a broken *result* of stated assumptions from being presented as a valid conclusion | PASS |
| VI. Deterministic Valuation | Guard adds a deterministic, unit-testable invariant to the existing deterministic engine; formula itself unchanged | PASS |
| VII. Traceability | Reference dataset preserves per-figure evidence metadata (FR-006) | PASS |
| VIII. Minimal Architecture | No new infrastructure; one function gains ~10 lines of validation | PASS |
| IX. No RAG in MVP | Not applicable | N/A |
| X. Provider Abstraction | Not touched | N/A |

**Gap found; addressed in design**: this feature narrows feature 003's Edge Cases text
("negative forecast-year FCFF is allowed and not an error") for the terminal-year case
specifically. This is a direct conflict between two ratified specs, not merely an
implementation detail. Resolved by explicit user decision during planning: feature 010
supersedes 003 on this point; 003's spec.md and its regression test are updated as part of
this feature's implementation (see research.md Decision 1), not silently overridden.

No unjustified violations. Complexity Tracking table below is empty (not needed).

## Project Structure

### Documentation (this feature)

```text
specs/010-valuation-plausibility-guard/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
src/aic/dcf/
├── engine.py             # compute_dcf gains the two guard checks (edited)
├── assumptions.py        # unchanged
└── result.py             # unchanged

tests/unit/dcf/
├── test_engine.py               # edited: narrow test_negative_fcff_year_is_allowed,
│                                 # add terminal-FCFF and enterprise-value rejection tests
└── test_amazon_reference_case.py  # new: Amazon reference dataset, no network, asserts
                                    # a plausible, strictly-positive end-to-end DCF result

scripts/
└── mvp_amazon_validation.py     # edited: rebalanced forecast assumptions so the
                                  # reference case passes the new guard

specs/003-dcf-valuation-engine/
└── spec.md                      # edited: Edge Cases note amended to record the
                                  # terminal-year narrowing and point to 010
```

**Structure Decision**: Single existing Python library/CLI project (`src/aic/`). No new
package, module boundary, or project is introduced — this is a targeted edit to the
existing `aic.dcf.engine` module plus test/fixture/script updates, consistent with
Constitution VIII (Minimal Architecture).

## Complexity Tracking

*No unjustified Constitution Check violations — table intentionally left empty.*
