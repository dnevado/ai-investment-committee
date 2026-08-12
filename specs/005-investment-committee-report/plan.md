# Implementation Plan: Investment Committee Report

**Branch**: `005-investment-committee-report` | **Date**: 2026-08-12 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/005-investment-committee-report/spec.md`

## Summary

Add a new `aic.report` sub-package that composes an already-produced `Company`, one or more
`FinancialSnapshot`s, an `InvestmentThesis` (with its supporting evidence), a `DCFResult`
(003-dcf-valuation-engine), an `AnalysisAssessment`, and a `CommitteeDecision` into one
validated `CommitteeReport`, then deterministically renders it into a Markdown document. No
new financial calculation, LLM call, persistence, API, UI, or scheduling is introduced —
this feature is a pure, typed composition-and-rendering step that closes the MVP's
end-to-end workflow.

## Technical Context

**Language/Version**: Python 3.12+ (matches the existing repository baseline)

**Primary Dependencies**: Pydantic v2 (existing) — no new third-party dependency; this
feature makes no LLM call and therefore does not need `openai` or any provider abstraction

**Storage**: N/A — no persistence (FR-011)

**Testing**: pytest; every test constructs the composed domain entities directly (no fake
provider needed — this feature has no external dependency to fake)

**Target Platform**: Same as the existing repository — local developer machine, Windows
PowerShell as the primary documented/verified shell

**Project Type**: Single Python package; this feature adds a `report` sub-package under the
existing `aic` package; no existing file is modified

**Performance Goals**: N/A — no throughput requirement stated

**Constraints**: No new financial calculation or valuation method (FR-003, FR-010); no
persistence (FR-011); no API, UI, scheduling, or market-data integration (FR-012); no
existing domain entity or the DCF engine is modified (FR-013); a missing required input
SHALL fail explicitly rather than produce a partial report (FR-007, FR-014); rendering the
same report twice SHALL be byte-identical (FR-009)

**Scale/Scope**: One new sub-package, `aic.report` (`CommitteeReport` and
`render_report_document`) — no other existing file is touched

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle / Section | Applies to this feature? | Status | Notes |
|---|---|---|---|
| I. Evidence Before Opinion | Yes | PASS | The thesis's and assessment's supporting evidence are presented exactly as supplied (FR-002, FR-004); nothing is added or reinterpreted |
| II. LLM Proposes, Code Computes | No LLM call in this feature at all | N/A | Per spec Assumptions, this feature introduces no new LLM call — narrative content is whatever prior features (e.g., 004) already produced; assembly and rendering are pure Python |
| III. Structured Outputs Only | Yes | PASS | `CommitteeReport` is a typed Pydantic model; the document is rendered only from its validated fields, never from untyped text |
| IV. Bull/Bear Symmetry | Not introduced by this feature | N/A | This feature composes whatever `AnalysisAssessment`/`CommitteeDecision` it is given; Bull/Bear agent generation is a separate, not-yet-built iteration per CLAUDE.md's MVP sequence |
| V. Explicit Assumptions | Yes | PASS | The thesis's `key_assumptions` and the assessment's `assumptions` are presented unchanged (FR-002, FR-004) |
| VI. Deterministic Valuation | Yes — this feature's central constraint | PASS | Every valuation figure comes from the existing `DCFResult` (003) unchanged; no new calculation is performed (FR-003, FR-010) |
| VII. Traceability | Yes | PASS | Evidence retains its source metadata; financial snapshots are presented as-supplied without reconciling currencies/periods across snapshots (spec Edge Cases) |
| VIII. Minimal Architecture, No Premature Infrastructure | Yes | PASS | No new dependency; `CommitteeReport` is a direct, validated Pydantic bundle — no separate "assemble" service, mirroring 004's `ResearchContext` precedent |
| IX. No RAG in MVP | Yes | PASS | No retrieval or document ingestion is introduced |
| X. Provider Abstraction | No provider involved | N/A | This feature has no external provider to abstract — it is pure composition and rendering |
| Architecture & Agent Design Constraints | Yes | PASS | Composition logic lives in an application-level module (`aic.report`), not in a CLI, adapter, or LangGraph node; this is not an agent — not every task warrants one |
| Quality, Observability & Development Workflow — "Agent features MUST additionally include... cost measurement, and latency measurement" | No — this feature makes no LLM call | N/A | The constitution's agent-feature testing/measurement requirements apply only to features that call an LLM; this feature has none, so no gap exists here (unlike 004) |

**No constitution gaps found.** No entries are required in Complexity Tracking.

## Project Structure

### Documentation (this feature)

```text
specs/005-investment-committee-report/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md         # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
│   └── report-interface.md
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
src/
└── aic/
    ├── __init__.py            # Existing — unchanged
    ├── settings.py             # Existing — unchanged (no new dependency to configure)
    ├── domain/                 # Existing (002-domain-model) — unchanged; this feature
    │   └── ...                 # imports Company, FinancialSnapshot, InvestmentThesis,
    │                            # AnalysisAssessment, CommitteeDecision from here
    ├── dcf/                     # Existing (003-dcf-valuation-engine) — unchanged; this
    │   └── ...                  # feature imports DCFResult from here, read-only
    ├── research/                 # Existing (004-investment-research-thesis) — unchanged
    │   └── ...                   # (not directly used by this feature's own code — the
    │                              # thesis it composes may have been produced by it)
    └── report/                    # New in this feature
        ├── __init__.py            # Re-exports: CommitteeReport, render_report_document
        ├── report.py               # CommitteeReport (Company + FinancialSnapshot(s) +
        │                            # InvestmentThesis + DCFResult + AnalysisAssessment +
        │                            # CommitteeDecision bundle; direct Pydantic
        │                            # construction is the "assembly" step)
        └── document.py              # render_report_document(report) -> str
                                       # (deterministic Markdown)

tests/
└── unit/
    ├── test_smoke.py            # Existing — unchanged
    ├── domain/                  # Existing (002-domain-model) — unchanged
    ├── dcf/                      # Existing (003-dcf-valuation-engine) — unchanged
    ├── research/                  # Existing (004-investment-research-thesis) — unchanged
    └── report/                     # New in this feature
        ├── test_report.py          # required-field validation, round-trip construction
        └── test_report_document.py   # deterministic rendering; dissent present vs. absent;
                                       # empty-evidence rendering
```

**Structure Decision**: Single-project, `src`-layout (unchanged). This feature adds one new
sibling sub-package, `aic.report`, alongside `aic.domain`, `aic.dcf`, and `aic.research` —
none of which is modified. `report` depends on `domain` (`Company`, `FinancialSnapshot`,
`InvestmentThesis`, `AnalysisAssessment`, `CommitteeDecision`) and `dcf` (`DCFResult`),
never the reverse, and does not depend on `research` at all (it composes whatever thesis it
is given, regardless of how that thesis was produced). No existing file is touched.

## Complexity Tracking

*No Constitution Check violations requiring justification — this section intentionally left
empty.*
