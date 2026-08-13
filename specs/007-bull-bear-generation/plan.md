# Implementation Plan: Bull/Bear Analysis Generation

**Branch**: `007-bull-bear-generation` | **Date**: 2026-08-13 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/007-bull-bear-generation/spec.md`

## Summary

Add a new `aic.bullbear` sub-package that assembles an `InvestmentCase` and a
`ValuationResult` into a structured `BullBearContext`, then exposes two independent
functions — `generate_bull_assessment` and `generate_bear_assessment` — each making its own
separate OpenAI call (through 004-investment-research-thesis's existing `LLMProvider`
protocol and `OpenAIProvider` adapter, reused unchanged) with a role-specific prompt, to
produce a shared LLM-facing `AssessmentDraft`. Evidence references are resolved against the
real input `Evidence`, and the existing `AnalysisAssessment` domain model (002) is
constructed unchanged. Neither generation call ever includes the other's output — role is
enforced entirely through which prompt is used, not through a different schema. No new
provider abstraction, no financial calculation, no report rendering, and no
`CommitteeDecision` generation. Tests run entirely against a fake provider — zero real
OpenAI calls.

## Technical Context

**Language/Version**: Python 3.12+ (matches the existing repository baseline)

**Primary Dependencies**: Pydantic v2 (existing); `openai` (existing, added in
004-investment-research-thesis) — **no new dependency**; this feature reuses 004's
`LLMProvider`/`LLMCompletion`/`OpenAIProvider` from `aic.research` directly rather than
duplicating a second provider abstraction

**Storage**: N/A — no persistence (FR-017)

**Testing**: pytest, using a fake `LLMProvider` test double (mirrors 004's
`FakeLLMProvider`); every test module and fixture in `tests/unit/bullbear/` is given a
`bullbear`-qualified basename from the start (`bullbear_fakes.py`,
`test_bullbear_context.py`, `test_bullbear_prompt.py`, `test_bullbear_generator.py`,
`test_bullbear_no_network_dependency.py`) to avoid the pytest module-name collisions that
had to be fixed after the fact in 006 (neither `tests/unit/research/` nor
`tests/unit/bullbear/` is a Python package, so identically-named modules across them would
collide during collection); no new test is needed for `OpenAIProvider` itself — it is
already covered by 004's own `test_openai_provider.py`

**Target Platform**: Same as the existing repository — local developer machine, Windows
PowerShell as the primary documented/verified shell

**Project Type**: Single Python package; this feature adds a `bullbear` sub-package under
the existing `aic` package; no existing file is modified

**Performance Goals**: N/A — no throughput requirement stated; OpenAI response latency is
external and outside this feature's control

**Constraints**: No new provider abstraction (FR-005); no duplicated DCF/valuation logic
(FR-010); no `CommitteeDecision` generation (FR-011); no report rendering (FR-012); no
external data ingestion, UI, API, or persistence (FR-013, FR-017); the LLM's raw response is
never trusted directly — validated against a typed schema before use (FR-006); every
supporting-evidence entry must be traceable to the supplied input, enforced structurally
(FR-007; mirrors 004/006's mechanism); confidence bounded within the existing range (FR-008);
no financial calculation performed by or requested of the LLM (FR-009); Bull and Bear
generation are two independent calls — neither includes the other's content (FR-004)

**Scale/Scope**: One new sub-package, `aic.bullbear` (`BullBearContext`, `AssessmentDraft`,
`build_bull_prompt`, `build_bear_prompt`, `generate_bull_assessment`,
`generate_bear_assessment`) — no other existing file is modified

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle / Section | Applies to this feature? | Status | Notes |
|---|---|---|---|
| I. Evidence Before Opinion | Yes | PASS | `supporting_evidence` is structurally restricted to `Evidence` UUIDs traceable to the supplied `InvestmentCase.evidence` (FR-007) for both roles |
| II. LLM Proposes, Code Computes | Yes | PASS | The LLM-facing `AssessmentDraft` schema has no financial field beyond a bounded `confidence` float; `ValuationResult` is consumed read-only (FR-009) |
| III. Structured Outputs Only | Yes | PASS | Each LLM's raw response is validated against `AssessmentDraft` before any further processing (FR-006) |
| IV. Bull/Bear Symmetry | Yes — this feature's entire purpose | PASS | Constitution text requires the Bull Agent to argue the strongest credible upside and the Bear Agent to argue the strongest credible downside via two roles — it does not list additional required structural sub-elements the way the Committee Chair's responsibilities are enumerated, so `AnalysisAssessment`'s existing `arguments`/`assumptions`/`risks` fields (guided by role-specific prompts) are sufficient without a richer intermediate schema; FR-004 enforces the two calls' independence directly |
| V. Explicit Assumptions | Yes | PASS | Each role's `assumptions` are populated as part of the reused `AnalysisAssessment` output |
| VI. Deterministic Valuation | No new calculation introduced | PASS | `ValuationResult` is consumed read-only (FR-009); no valuation math added |
| VII. Traceability | Yes | PASS | Evidence references are resolved against the real input `Evidence`; an unresolvable reference is rejected explicitly (FR-007) |
| VIII. Minimal Architecture, No Premature Infrastructure | Yes | PASS | Zero new dependencies; the existing `LLMProvider`/`OpenAIProvider` from 004 is reused directly rather than duplicated (FR-005); `AnalysisAssessment` is reused unchanged rather than split into `BullAssessment`/`BearAssessment` |
| IX. No RAG in MVP | Yes | PASS | No document ingestion/retrieval; structured context is passed directly to the model |
| X. Provider Abstraction | Yes | PASS | Reuses 004's `LLMProvider` protocol verbatim; every test in this feature runs against a fake implementation (FR-005) |
| Architecture & Agent Design Constraints — "Initial agents are Research, Bull, Bear, and Committee Chair" | Yes — this feature implements two of the four sanctioned agents | PASS | `generate_bull_assessment`/`generate_bear_assessment` are application services (functions), not domain models; each is single-purpose and independently testable |
| Quality, Observability & Development Workflow — "Agent features MUST additionally include... cost measurement, and latency measurement" | Yes — both generation paths call an LLM | PASS | Reuses 004's `LLMCompletion`/logging pattern verbatim for both `generate_bull_assessment` and `generate_bear_assessment` |

**No constitution gaps found.** No entries are required in Complexity Tracking.

## Project Structure

### Documentation (this feature)

```text
specs/007-bull-bear-generation/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md         # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
│   └── bullbear-interface.md
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
src/
└── aic/
    ├── __init__.py            # Existing — unchanged
    ├── settings.py             # Existing — unchanged (reuses 004's openai_api_key field)
    ├── domain/                 # Existing (002-domain-model) — unchanged; this feature
    │   └── ...                 # imports InvestmentCase, AnalysisAssessment,
    │                            # ValuationResult from here
    ├── dcf/                     # Existing (003-dcf-valuation-engine) — unchanged; not
    │   └── ...                  # depended on directly by this feature (it consumes the
    │                             # already-produced ValuationResult, not DCFResult)
    ├── research/                 # Existing (004-investment-research-thesis) — unchanged;
    │   ├── provider.py            # this feature imports LLMProvider/LLMCompletion...
    │   └── openai_provider.py      # ...and OpenAIProvider from here, reused verbatim
    ├── report/                    # Existing (005-investment-committee-report) — unchanged;
    │   └── ...                     # not depended on by this feature
    ├── committee/                  # Existing (006-committee-decision-engine) — unchanged;
    │   └── ...                      # this feature does not depend on it; 006 will consume
    │                                 # this feature's output as its own bull_assessment/
    │                                 # bear_assessment input, but that wiring happens on
    │                                 # 006's side (or a future caller), not here
    └── bullbear/                    # New in this feature
        ├── __init__.py               # Re-exports: BullBearContext, AssessmentDraft,
        │                              # build_bull_prompt, build_bear_prompt,
        │                              # generate_bull_assessment, generate_bear_assessment
        ├── context.py                  # BullBearContext (InvestmentCase + ValuationResult
        │                               # bundle)
        ├── draft.py                     # AssessmentDraft (the LLM-facing intermediate
        │                                # schema shared by both roles — conclusion,
        │                                # confidence, arguments, assumptions, risks,
        │                                # evidence references)
        ├── prompt.py                      # build_bull_prompt(context) -> (system, user);
        │                                  # build_bear_prompt(context) -> (system, user);
        │                                  # pure, deterministic, role-specific
        └── generator.py                     # generate_bull_assessment(context, provider)
                                              # -> AnalysisAssessment;
                                              # generate_bear_assessment(context, provider)
                                              # -> AnalysisAssessment; both call a shared
                                              # private _generate(...) helper for the
                                              # mechanical validate/resolve/construct steps
                                              # only — never for the LLM call itself, which
                                              # each performs independently with its own
                                              # role-specific prompt

tests/
└── unit/
    ├── test_smoke.py            # Existing — unchanged
    ├── domain/                  # Existing (002-domain-model) — unchanged
    ├── dcf/                      # Existing (003-dcf-valuation-engine) — unchanged
    ├── research/                  # Existing (004-investment-research-thesis) — unchanged
    ├── report/                     # Existing (005-investment-committee-report) — unchanged
    ├── committee/                   # Existing (006-committee-decision-engine) — unchanged
    └── bullbear/                     # New in this feature
        ├── bullbear_fakes.py           # FakeLLMProvider test double, local to this test
        │                               # directory, named to avoid a collision with
        │                               # tests/unit/research/fakes.py and
        │                               # tests/unit/committee/committee_fakes.py
        ├── test_bullbear_context.py
        ├── test_bullbear_prompt.py
        ├── test_bullbear_generator.py    # valid generation for both roles,
        │                                 # untraceable-evidence rejection,
        │                                 # schema-validation failure, provider-error
        │                                 # propagation, confidence-bounds rejection,
        │                                 # independence verification (Bear call excludes
        │                                 # Bull content, and vice versa)
        └── test_bullbear_no_network_dependency.py
```

**Structure Decision**: Single-project, `src`-layout (unchanged). This feature adds one new
sibling sub-package, `aic.bullbear`, alongside `aic.domain`, `aic.dcf`, `aic.research`,
`aic.report`, and `aic.committee` — none of which is modified. `bullbear` depends on
`domain` (`InvestmentCase`, `AnalysisAssessment`, `ValuationResult`) and `research`
(`LLMProvider`, `LLMCompletion`, `OpenAIProvider` — reused, not duplicated), never the
reverse. `bullbear` does not depend on `dcf`, `report`, or `committee`.

## Complexity Tracking

*No Constitution Check violations requiring justification — this section intentionally left
empty.*
