# Implementation Plan: End-to-End Investment Committee Workflow & MVP Completion

**Branch**: `009-e2e-investment-workflow` | **Date**: 2026-08-13 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/009-e2e-investment-workflow/spec.md`

## Summary

Add a new `aic.workflow` sub-package with a single orchestration entry point,
`run_investment_workflow`, that calls every existing stage — DCF (003), research/thesis
(004), Bull/Bear (007), committee adjudication (006), and report composition (005) — in the
dependency-correct order (valuation before both research and Bull/Bear, contradicting the
spec's own illustrative arrow-diagram, per its Assumptions), reusing one LLM provider
instance across all four LLM-calling stages, and letting each stage's own exception
propagate unchanged on failure. Two small, additive, backward-compatible fields are added to
the existing `CommitteeReport` (005) to represent both the Bull and the Bear assessment,
closing a real integration-point gap discovered during this plan (see Constitution Check).
The unused `src/aic/agents/prompts/` scaffolding is removed. No new financial calculation,
no new provider abstraction, no LangGraph, no persistence.

## Technical Context

**Language/Version**: Python 3.12+ (matches the existing repository baseline)

**Primary Dependencies**: Pydantic v2 (existing); no new dependency. Reuses
`aic.dcf.compute_dcf`/`to_valuation_result` (003), `aic.research.generate_thesis` (004),
`aic.bullbear.generate_bull_assessment`/`generate_bear_assessment` (007),
`aic.committee.generate_decision` (006), and `aic.report.CommitteeReport`/
`render_report_document` (005) — all unchanged in their own public contracts, except the two
additive `CommitteeReport` fields noted above

**Storage**: N/A — no persistence (FR-014)

**Testing**: pytest; end-to-end tests use one fake `LLMProvider` (reused across all four
LLM-calling stages, exactly as production code will) with per-stage configurable
responses/failures, so User Story 2's per-stage-failure scenarios can be exercised without
real network access. Every new test file in `tests/unit/workflow/` uses a
`workflow`-qualified basename from the start (same lesson as 006/007 — neither
`tests/unit/workflow/` nor any existing test directory is a Python package, so basenames
must stay globally unique across all of them)

**Target Platform**: Same as the existing repository — local developer machine, Windows
PowerShell as the primary documented/verified shell

**Project Type**: Single Python package; this feature adds a `workflow` sub-package under
the existing `aic` package, makes one small additive change to the existing
`aic.report.report`/`aic.report.document` modules, and removes the unused
`src/aic/agents/` directory

**Performance Goals**: N/A — no throughput requirement stated; the workflow's latency is the
sum of its four sequential LLM calls plus one deterministic DCF computation, none of which
this feature changes

**Constraints**: No new financial calculation, valuation methodology, or investment-analysis
logic (FR-012); no new LLM provider abstraction — one provider instance reused across every
stage (FR-013); no persistence, UI, API, autonomous agents, or multi-agent orchestration
beyond the existing sequential sequence (FR-014); every existing test's assertions must
remain unchanged (FR-016); the currently-unused `aic/agents/prompts/` scaffolding must be
resolved, not left as a second, parallel, diverging prompt-definition mechanism (FR-017)

**Scale/Scope**: One new sub-package, `aic.workflow` (`WorkflowInput`, `WorkflowResult`,
`run_investment_workflow`); two new optional fields added to the existing `CommitteeReport`;
one existing directory (`src/aic/agents/`) removed entirely

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle / Section | Applies to this feature? | Status | Notes |
|---|---|---|---|
| I. Evidence Before Opinion | Yes | PASS | Every stage's own existing evidence-traceability mechanism is reused unchanged; the workflow adds no new evidence-handling logic |
| II. LLM Proposes, Code Computes | Yes | PASS | The workflow performs zero calculation of its own — DCF (003) remains the sole valuation source, computed exactly once and passed through unchanged (FR-002, FR-009) |
| III. Structured Outputs Only | Yes | PASS | Every stage's own existing structured-output validation is reused unchanged; the workflow introduces no new untyped interface between stages |
| IV. Bull/Bear Symmetry | Yes | PASS | Reuses 007's independent-call guarantee unchanged — the workflow does not alter how or when Bull/Bear are generated relative to each other |
| V. Explicit Assumptions | Yes | PASS | Thesis, Bull, and Bear assumptions all flow through to the final report unchanged |
| VI. Deterministic Valuation | Yes — this feature makes it end-to-end for the first time | PASS | DCF (003) is computed exactly once per workflow run and reused as read-only context by every later stage — no stage recomputes or introduces a second valuation (FR-002, FR-009) |
| VII. Traceability | Yes — this feature closes a real gap | PASS | FR-008 (evidence) and FR-010 (the committee decision's `valuation_reference`, left unset by 006 for lack of a `ValuationResult` at the time) are both implemented end-to-end here for the first time |
| VIII. Minimal Architecture, No Premature Infrastructure | Yes | PASS | No new dependency; every stage is reused unchanged in its own contract; the `CommitteeReport` change is two additive, backward-compatible fields, not a rewrite; no LangGraph (see research.md) |
| IX. No RAG in MVP | Yes | PASS | No retrieval or document ingestion is introduced |
| X. Provider Abstraction | Yes | PASS | One `LLMProvider` instance (from `aic.research`) is passed to and reused by all four LLM-calling stages — no second abstraction (FR-013) |
| Architecture & Agent Design Constraints — "Do not put investment logic inside... LangGraph nodes"; "reconcile agent/prompt definitions... avoid a parallel unused architecture" | Yes | PASS | No LangGraph is introduced (research.md); the unused `src/aic/agents/prompts/*.md` scaffolding — confirmed by search to be imported nowhere in `src/` or `tests/` — is removed rather than left as a second, diverging prompt-definition mechanism (FR-017) |
| Quality, Observability & Development Workflow — cost/latency measurement for agent features | Yes, transitively | PASS | Every LLM call the workflow makes already logs its own cost/latency inside the stage that makes it (004, 006, 007); the orchestrator adds no new LLM call of its own, so no new logging is needed |
| *(Integration-point completeness — this spec's own FR-007/"Ensure the final CommitteeDecision is correctly represented in the CommitteeReport")* | Yes — discovered during this plan | **Gap found; addressed in design** | `CommitteeReport.assessment` (005) is a single `AnalysisAssessment` field, designed before Bull/Bear existed as two independent outputs (007). This workflow produces both a Bull and a Bear assessment; passing only one into `assessment` would silently discard the other from the final report — a real information-loss bug, not a cosmetic gap. Resolved by adding two new, optional (`= None`), backward-compatible fields, `bull_assessment` and `bear_assessment`, to `CommitteeReport`; `assessment` itself is left required and unchanged (still populated, with the Bull assessment, to preserve every pre-existing caller/test unmodified — FR-016), and `render_report_document` renders two distinct labeled sections when both new fields are present, falling back to its exact pre-existing single-section rendering otherwise. See research.md. |

**Constitution gap note**: The single row above marked "Gap found" is a real
integration-point defect this plan discovered — not a constitution-principle gap like 004's
or 006's — but is reported with the same rigor for the same reason: silently choosing one
assessment over the other, or leaving it undecided until implementation, would either lose
information or produce inconsistent behavior across implementers. The resolution is
additive and backward-compatible, so no existing test's assertions change (FR-016). No
entries are required in Complexity Tracking — this is a scope-authorized fix (the spec
explicitly asks this feature to "resolve inconsistencies between existing models and
integration points"), not an unjustified deviation.

## Project Structure

### Documentation (this feature)

```text
specs/009-e2e-investment-workflow/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md         # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
│   └── workflow-interface.md
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
src/
└── aic/
    ├── __init__.py            # Existing — unchanged
    ├── settings.py             # Existing — unchanged
    ├── agents/                  # Existing — REMOVED by this feature (FR-017; confirmed
    │   └── prompts/*.md          # unused anywhere in src/ or tests/ before removal)
    ├── domain/                 # Existing (002-domain-model) — unchanged
    ├── dcf/                     # Existing (003-dcf-valuation-engine) — unchanged; this
    │   └── ...                  # feature imports compute_dcf/to_valuation_result
    ├── research/                 # Existing (004-investment-research-thesis) — unchanged;
    │   └── ...                    # this feature imports generate_thesis, LLMProvider
    ├── bullbear/                  # Existing (007-bull-bear-generation) — unchanged; this
    │   └── ...                     # feature imports generate_bull_assessment,
    │                                # generate_bear_assessment
    ├── committee/                  # Existing (006-committee-decision-engine) — unchanged;
    │   └── ...                      # this feature imports generate_decision
    ├── report/                      # Existing (005-investment-committee-report) —
    │   ├── report.py                 # MODIFIED: two new optional fields on
    │   │                              # CommitteeReport (bull_assessment, bear_assessment)
    │   └── document.py                # MODIFIED: render_report_document renders both
    │                                   # when present, unchanged single-section rendering
    │                                   # otherwise (backward compatible; FR-016)
    └── workflow/                        # New in this feature
        ├── __init__.py                   # Re-exports: WorkflowInput, WorkflowResult,
        │                                 # run_investment_workflow
        ├── input.py                        # WorkflowInput (company, financial_snapshots,
        │                                   # evidence, dcf_assumptions)
        ├── result.py                         # WorkflowResult (dcf_result, thesis,
        │                                     # bull_assessment, bear_assessment, decision,
        │                                     # report, document)
        └── orchestrator.py                     # run_investment_workflow(input, provider)
                                                 # -> WorkflowResult — the only new
                                                 # behavioral code in this feature; every
                                                 # step delegates to an existing stage

tests/
└── unit/
    ├── test_smoke.py            # Existing — unchanged
    ├── domain/                  # Existing — unchanged
    ├── dcf/                      # Existing — unchanged
    ├── research/                  # Existing — unchanged
    ├── bullbear/                   # Existing — unchanged
    ├── committee/                   # Existing — unchanged
    ├── report/                       # Existing (005) — plus one new file:
    │   └── test_report_dual_assessment.py  # NEW: bull_assessment/bear_assessment
    │                                         # backward-compat + dual-section rendering
    │                                         # (does not modify any existing test file)
    └── workflow/                              # New in this feature
        ├── workflow_fakes.py                    # FakeLLMProvider, configurable per-stage
        │                                        # (content or error), named to avoid a
        │                                        # collision with every other test
        │                                        # directory's own fakes module
        ├── test_workflow_input.py
        ├── test_workflow_result.py
        ├── test_workflow_orchestrator.py           # the complete happy-path, plus every
        │                                           # per-stage-failure scenario (US2)
        └── test_workflow_no_network_dependency.py
```

**Structure Decision**: Single-project, `src`-layout (unchanged). This feature adds one new
sibling sub-package, `aic.workflow`, alongside every existing one — and, uniquely among
features 004-008, is explicitly authorized by its own spec to make small, additive,
backward-compatible modifications to an existing package (`aic.report`) and to remove
genuinely dead code (`aic/agents/`), rather than only adding new files.

## Complexity Tracking

*No unjustified Constitution Check violations. The one Gap-found row above is a
scope-authorized integration fix, not a complexity deviation requiring justification.*
