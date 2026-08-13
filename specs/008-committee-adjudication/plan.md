# Implementation Plan: Committee Adjudication Layer

**Branch**: `008-committee-adjudication` | **Date**: 2026-08-13 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/008-committee-adjudication/spec.md`

## Summary

Every functional requirement in this feature's spec is already satisfied by the existing,
implemented, tested, and converged `aic.committee` package
(006-committee-decision-engine): `CommitteeAdjudicationContext` (context.py),
`CommitteeDecisionDraft` (draft.py), the adjudication prompt (prompt.py), and
`generate_decision` (generator.py), which reuses `aic.research`'s `LLMProvider` abstraction,
validates supporting-evidence IDs against the supplied investment case, propagates provider
errors without fabricating a decision, records dissent when the Chair does not fully adopt
one side, and returns the existing `CommitteeDecision` domain entity unchanged — the exact
entity `CommitteeReport` (005) already consumes as its `decision` field, with no adapter
needed. This plan does **not** introduce a new source package. It documents the mapping from
this spec's requirements to that existing implementation and points Phase 1 artifacts at it,
consistent with the constitution's Minimal Architecture and Scope Discipline principles,
which forbid introducing a second, parallel implementation of logic that already exists and
is already proven correct.

## Technical Context

**Language/Version**: Python 3.12+ (matches the existing repository baseline; no new code,
so no new version requirement)

**Primary Dependencies**: None new. The satisfying implementation (`aic.committee`) already
depends only on Pydantic v2 and `openai` (both existing, added in
004-investment-research-thesis), reusing `aic.research`'s `LLMProvider`/`LLMCompletion`/
`OpenAIProvider` verbatim.

**Storage**: N/A — no persistence (FR-015), matching the existing implementation.

**Testing**: pytest. The existing `tests/unit/committee/` suite (16 tests) already exercises
every acceptance scenario in this spec via a fake `LLMProvider` — see Phase 1 mapping in
`quickstart.md`.

**Target Platform**: Same as the existing repository — local developer machine, Windows
PowerShell as the primary documented/verified shell.

**Project Type**: Single Python package. No new sub-package is added; this plan targets the
existing `src/aic/committee/` sub-package.

**Performance Goals**: N/A — no throughput requirement stated; unchanged from the existing
implementation.

**Constraints**: Identical to 006-committee-decision-engine's own constraints (no LangGraph;
no persistence; credentials only via `aic.settings`; LLM response validated before use;
evidence traceability enforced structurally; no financial calculation by the LLM; no
averaging of bull/bear positions) — all already satisfied by the code this plan reuses.

**Scale/Scope**: Zero new files. This plan's only artifacts are its own documentation
(`research.md`, `data-model.md`, `contracts/`, `quickstart.md`) mapping this spec onto the
existing `aic.committee` implementation.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle / Section | Applies to this feature? | Status | Notes |
|---|---|---|---|
| I. Evidence Before Opinion | Yes | PASS | Satisfied by the existing `aic.committee.generator.generate_decision`'s evidence-ID resolution against `context.investment_case.evidence` |
| II. LLM Proposes, Code Computes | Yes | PASS | Satisfied by the existing `CommitteeDecisionDraft` schema (no financial field beyond bounded `confidence`) and read-only `DCFResult` consumption |
| III. Structured Outputs Only | Yes | PASS | Satisfied by the existing `CommitteeDecisionDraft.model_validate` step before any further processing |
| IV. Bull/Bear Symmetry | Yes — this feature's central purpose | PASS | Satisfied by the existing implementation's structural requirement that `key_disagreements` be a separate required field, and by FR-007's non-averaging requirement, already enforced |
| V. Explicit Assumptions | Yes | PASS | Satisfied — bull/bear `assumptions` and the thesis's `key_assumptions` remain reachable via `referenced_thesis` on the existing `CommitteeDecision` output |
| VI. Deterministic Valuation | No new calculation introduced | PASS | `DCFResult` consumed read-only, unchanged from the existing implementation |
| VII. Traceability | Yes | PASS | Satisfied by the existing evidence-ID resolution mechanism |
| VIII. Minimal Architecture, No Premature Infrastructure | Yes — this is the deciding principle for this plan | PASS | Building a second, parallel package (e.g., `aic.adjudication`) that duplicates `aic.committee`'s already-correct logic 1:1 would itself be a violation of this principle — introducing unjustified complexity and a second implementation that can drift from the first. The constitution-compliant choice is reuse, not duplication. See Complexity Tracking. |
| IX. No RAG in MVP | Yes | PASS | No retrieval/ingestion, unchanged |
| X. Provider Abstraction | Yes | PASS | Satisfied — the existing implementation reuses `aic.research`'s `LLMProvider` protocol verbatim; this spec's own FR-003 explicitly forbids introducing a new one |
| Scope Discipline — "modify only necessary files... avoid speculative abstractions... preserve existing behavior" | Yes | PASS | Reuse requires editing zero existing files and adding zero new source files |

**No constitution gaps found.** This plan's central finding — reuse, not reimplementation —
is itself the constitution-compliant outcome; see Complexity Tracking for why the
alternative (a new package) was rejected.

## Project Structure

### Documentation (this feature)

```text
specs/008-committee-adjudication/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md         # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
│   └── adjudication-interface.md
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
src/
└── aic/
    ├── domain/                 # Existing (002-domain-model) — unchanged; supplies
    │   └── ...                 # InvestmentCase, AnalysisAssessment, CommitteeDecision
    ├── dcf/                     # Existing (003-dcf-valuation-engine) — unchanged; supplies
    │   └── ...                  # DCFResult, consumed read-only
    ├── research/                 # Existing (004-investment-research-thesis) — unchanged;
    │   └── ...                    # supplies LLMProvider/LLMCompletion/OpenAIProvider
    ├── report/                    # Existing (005-investment-committee-report) — unchanged;
    │   └── ...                     # already consumes CommitteeDecision as-is
    └── committee/                  # Existing (006-committee-decision-engine) — UNCHANGED;
        ├── __init__.py              # this feature's spec is satisfied entirely by this
        ├── context.py                # already-implemented, already-tested package. No
        ├── draft.py                   # file under src/ is created or modified by this
        ├── prompt.py                   # plan.
        └── generator.py

tests/
└── unit/
    └── committee/                  # Existing (006-committee-decision-engine) — unchanged;
        └── ...                      # already exercises every acceptance scenario this
                                       # spec defines (see quickstart.md mapping)
```

**Structure Decision**: No new source or test files. Every file this feature's spec
describes by role (`CommitteeAdjudicationContext`, the adjudication prompt,
`CommitteeDecisionDraft`, evidence-ID validation, error propagation, dissent handling,
no-network tests) already exists under `src/aic/committee/` and `tests/unit/committee/` from
006-committee-decision-engine. This plan's Phase 1 artifacts (`data-model.md`, `contracts/`,
`quickstart.md`) document the mapping from this spec's requirements to that existing code,
rather than designing new components.

## Complexity Tracking

> Filled because this plan's central decision — reuse instead of new implementation —
> itself needs to be justified against the template's default expectation of new code.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|
| N/A — no constitution violation | This plan introduces no new package, dependency, or architectural component | Not applicable; the row below explains the alternative that was rejected in the *other* direction |
| (Rejected) New `aic.adjudication` package duplicating `aic.committee` | Would have matched a literal reading of "implement... the adjudication layer" as new work | Rejected because `aic.committee` (006) already implements, tests, and — per this session's `/speckit-converge` run — verifiably satisfies every functional requirement in this spec (evidence-ID validation, error propagation, dissent handling, non-averaging rationale, provider abstraction reuse, zero-network tests). A second implementation would duplicate deterministic logic the constitution's Minimal Architecture and Scope Discipline principles explicitly forbid introducing without demonstrated need, and would create two decision-adjudication code paths that could silently drift apart — a correctness risk with no offsetting benefit. |
