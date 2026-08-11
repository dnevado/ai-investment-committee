# Implementation Plan: Deterministic DCF Valuation Engine

**Branch**: `003-dcf-valuation-engine` | **Date**: 2026-08-10 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/003-dcf-valuation-engine/spec.md`

## Summary

Implement a pure, deterministic FCFF-based DCF calculation engine in a new `aic.dcf`
sub-package: `DCFAssumptions` (a validated Pydantic input bundle — per-year forecast,
constant Operating Margin/Tax Rate, WACC, Terminal Growth Rate, Cash, Debt, Shares
Outstanding), `DCFResult` (the deterministic output — per-year FCFF/PV(FCFF), Terminal
Value, PV(Terminal Value), Enterprise Value, Equity Value, Implied Value Per Share), and
a pure function `compute_dcf(assumptions) -> DCFResult`. All monetary fields reuse the
existing `Money` type; the result is convertible to the existing `ValuationResult`. No
LLM call, no I/O, no persistence, no new dependency — exact `Decimal` arithmetic
throughout, rounded only at the final reported values (round-half-up, 2 decimal places).

## Technical Context

**Language/Version**: Python 3.12+ (matches the existing repository baseline)

**Primary Dependencies**: Pydantic v2 (`pydantic>=2.0`, already a runtime dependency);
`decimal` (Python standard library) for all arithmetic — no new third-party dependency
is introduced by this feature

**Storage**: N/A — pure calculation, no persistence

**Testing**: pytest, including a dedicated test reproducing the spec's canonical
Reference Case exactly, plus validation-rejection tests for every FR-014–FR-019 rule

**Target Platform**: Same as the existing repository — local developer machine, Windows
PowerShell as the primary documented/verified shell

**Project Type**: Single Python package; this feature adds a `dcf` sub-package under the
existing `aic` package, alongside (not inside) the existing `aic.domain` sub-package

**Performance Goals**: N/A — no performance-sensitive or high-throughput requirement
stated; forecast periods are small (single-digit to low-double-digit years) by nature

**Constraints**: No network or file I/O (FR-023); no dependency on OpenAI, LangChain,
LangGraph, AWS/boto3, or any market-data SDK, and no LLM call anywhere (FR-024); fully
deterministic, no randomness (FR-025); exact `Decimal` arithmetic only, never binary
floating-point (FR-021); final reported monetary values rounded to 2 decimal places with
round-half-up, intermediate values left unrounded until that step (FR-022); every
monetary input/output in one calculation shares one explicit currency (FR-020)

**Scale/Scope**: Two new Pydantic models (`DCFAssumptions` incl. a nested `ForecastYear`
line item; `DCFResult` incl. a nested per-year `YearResult`) plus one pure calculation
function and one `ValuationResult`-conversion helper, entirely within a new `aic.dcf`
sub-package — no application, agent, CLI, or persistence code

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle / Section | Applies to this feature? | Status | Notes |
|---|---|---|---|
| I. Evidence Before Opinion | No — no investment claims produced | N/A | Out of scope by design |
| II. LLM Proposes, Code Computes | Yes — this feature *is* the "code computes" half | PASS | All arithmetic is deterministic Python/`Decimal`; no LLM call anywhere (FR-024, FR-025) |
| III. Structured Outputs Only | Yes | PASS | `DCFAssumptions`/`DCFResult` are typed Pydantic models; no free-form text |
| IV. Bull/Bear Symmetry | No — no agents in this feature | N/A | Out of scope by design |
| V. Explicit Assumptions | Yes | PASS | Every input is an explicit, named field; missing assumptions are rejected, never invented (FR-018) |
| VI. Deterministic Valuation | Yes — this feature is the principle's primary implementation | PASS | "Financial calculations MUST be implemented in Python... independently testable, decoupled from any LLM call" — directly and fully satisfied |
| VII. Traceability | No — inputs are caller-supplied structured values, not sourced external facts | N/A | Traceability of the underlying evidence is the concern of `ValuationResult.assumption_evidence_refs` (001-domain-model), one layer up from this engine |
| VIII. Minimal Architecture, No Premature Infrastructure | Yes | PASS | No new dependency, no persistence, no infrastructure |
| IX. No RAG in MVP | N/A | PASS | No document ingestion or retrieval involved |
| X. Provider Abstraction | Yes | PASS | FR-024 makes zero LLM/provider dependency a testable requirement of the engine itself |
| Architecture & Agent Design Constraints ("LangGraph... nodes MUST NOT contain DCF formulas") | Yes | PASS | This feature *is* the module a future LangGraph node would call into — the formulas live here, not in orchestration code, satisfying the constraint the constitution places on future graph nodes |
| Quality, Observability & Development Workflow | Yes | PASS | Canonical Reference Case test (SC-001) plus explicit rejection tests for every validation rule map directly to the constitution's testing expectations |

No violations identified. No entries required in Complexity Tracking.

## Project Structure

### Documentation (this feature)

```text
specs/003-dcf-valuation-engine/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md         # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
│   └── dcf-engine-interface.md
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
src/
└── aic/
    ├── __init__.py            # Existing — unchanged
    ├── settings.py             # Existing — unchanged
    ├── agents/                 # Existing pre-existing prompt scaffolding — untouched, out of scope
    │   └── prompts/
    ├── domain/                 # Existing (002-domain-model) — unchanged; this feature imports
    │   └── ...                 # `Money` and `ValuationResult` from here but modifies nothing
    └── dcf/                     # New in this feature
        ├── __init__.py         # Re-exports: DCFAssumptions, ForecastYear, DCFResult,
        │                        # YearResult, compute_dcf, to_valuation_result
        ├── assumptions.py       # DCFAssumptions, ForecastYear (input models + validation)
        ├── result.py             # DCFResult, YearResult (output models)
        └── engine.py              # compute_dcf() pure function; to_valuation_result() adapter

tests/
└── unit/
    ├── test_smoke.py            # Existing — unchanged
    ├── domain/                  # Existing (002-domain-model) — unchanged
    └── dcf/                      # New in this feature
        ├── test_assumptions.py   # Validation-rejection tests (FR-014–FR-020)
        └── test_engine.py         # Reference Case + calculation/determinism tests
```

**Structure Decision**: Single-project, `src`-layout (unchanged). This feature adds a new
sibling sub-package, `aic.dcf`, distinct from `aic.domain` — the calculation engine is
business logic/computation, not a pure data contract, so it does not belong inside
`aic.domain` (which remains validation-only, per 002's design). `aic.dcf` depends on
`aic.domain` (`Money`, `ValuationResult`) but nothing in `aic.domain` is modified. The
name `dcf` (not `valuation`) was chosen deliberately to avoid colliding with the existing
`aic.domain.valuation` module (which defines the shape-only `ValuationResult`) — see
research.md for the full naming rationale.

## Complexity Tracking

*No Constitution Check violations — this section intentionally left empty.*
