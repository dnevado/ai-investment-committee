# Implementation Plan: Investment Committee Decision Engine

**Branch**: `006-committee-decision-engine` | **Date**: 2026-08-13 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/006-committee-decision-engine/spec.md`

## Summary

Add a new `aic.committee` sub-package that assembles an `InvestmentCase`, a `DCFResult`, a
bull `AnalysisAssessment`, and a bear `AnalysisAssessment` into a structured
`CommitteeAdjudicationContext`, calls OpenAI (through 004-investment-research-thesis's
existing `LLMProvider` protocol and `OpenAIProvider` adapter, reused unchanged) to produce a
narrow LLM-facing `CommitteeDecisionDraft` (central thesis, disagreements, valuation
summary, downside risks, invalidation conditions, recommendation, confidence, dissent, and
evidence *references* only), resolves those references against the real input `Evidence`,
deterministically composes the final `rationale` text from the draft's separate sections in
Python, and constructs the existing `CommitteeDecision` domain model unchanged. No new
financial calculation, no LangGraph, no report rendering (005 already owns that), and no new
provider abstraction. Tests run entirely against a fake provider — zero real OpenAI calls.

## Technical Context

**Language/Version**: Python 3.12+ (matches the existing repository baseline)

**Primary Dependencies**: Pydantic v2 (existing); `openai` (existing, added in
004-investment-research-thesis) — **no new dependency**; this feature reuses
004's `LLMProvider`/`LLMCompletion`/`OpenAIProvider` from `aic.research` directly rather than
duplicating a second provider abstraction

**Storage**: N/A — no persistence (FR-014)

**Testing**: pytest, using a fake `LLMProvider` test double (mirrors 004's `FakeLLMProvider`,
duplicated locally in `tests/unit/committee/` following this project's established
per-test-directory convention, since test directories are not Python packages here); no new
test is needed for `OpenAIProvider` itself — it is already covered by 004's own
`test_openai_provider.py`

**Target Platform**: Same as the existing repository — local developer machine, Windows
PowerShell as the primary documented/verified shell

**Project Type**: Single Python package; this feature adds a `committee` sub-package under
the existing `aic` package; no existing file is modified (not even `aic.settings` — the
`openai_api_key` field 004 already added is reused as-is)

**Performance Goals**: N/A — no throughput requirement stated; OpenAI response latency is
external and outside this feature's control

**Constraints**: No LangGraph or multi-agent orchestration (FR-010); no persistence
(FR-014); OpenAI credentials only via the existing `aic.settings` (FR-011, FR-012); the
LLM's raw response is never trusted directly — validated against a typed schema before use
(FR-004); every referenced evidence entry must be traceable to the supplied input, enforced
structurally (FR-005; mirrors 004's mechanism); no financial calculation performed by or
requested of the LLM (FR-006); the decision SHALL NOT be produced by simply averaging the
bull and bear assessments (FR-007) — addressed by requiring the LLM-facing schema to
separately articulate disagreements, downside risks, and invalidation conditions rather than
trusting a single free-text field to cover them (see Constitution Check and research.md)

**Scale/Scope**: One new sub-package, `aic.committee` (`CommitteeAdjudicationContext`,
`CommitteeDecisionDraft`, `build_prompt`, `generate_decision`) — no other existing file is
modified

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle / Section | Applies to this feature? | Status | Notes |
|---|---|---|---|
| I. Evidence Before Opinion | Yes | PASS | `referenced_evidence` is structurally restricted to UUIDs traceable to the supplied `InvestmentCase.evidence` (FR-005); the LLM cannot introduce unsourced evidence references |
| II. LLM Proposes, Code Computes | Yes | PASS | The LLM-facing `CommitteeDecisionDraft` schema has no numeric/financial field beyond a bounded `confidence` float; DCF figures come from `DCFResult` read-only (FR-006); the final `rationale` string is composed by Python from the draft's validated sections, not generated as one untracked blob |
| III. Structured Outputs Only | Yes | PASS | The LLM's raw response is validated against `CommitteeDecisionDraft` before any further processing (FR-004) |
| IV. Bull/Bear Symmetry | Yes — this feature's central purpose | PASS | This feature *consumes* independently-produced bull/bear `AnalysisAssessment`s (their generation is a separate, out-of-scope feature per spec Assumptions) and requires the Chair to evaluate both without averaging (FR-007, FR-009) |
| V. Explicit Assumptions | Yes | PASS | The bull/bear assessments' own `assumptions` and the thesis's `key_assumptions` remain available via `referenced_thesis` on the output `CommitteeDecision`; this feature does not strip or hide them |
| VI. Deterministic Valuation | No new calculation introduced | PASS | `DCFResult` is consumed read-only (FR-006); no valuation math added |
| VII. Traceability | Yes | PASS | Evidence references are resolved against the real input `Evidence`; an unresolvable reference is rejected explicitly (FR-005) |
| VIII. Minimal Architecture, No Premature Infrastructure | Yes | PASS | Zero new dependencies; the existing `LLMProvider`/`OpenAIProvider` from 004 is reused directly rather than duplicated; `CommitteeDecision` is reused unchanged rather than extended |
| IX. No RAG in MVP | Yes | PASS | No document ingestion/retrieval; structured context is passed directly to the model |
| X. Provider Abstraction | Yes | PASS | Reuses 004's `LLMProvider` protocol verbatim; every test in this feature runs against a fake implementation (FR-003) |
| Architecture & Agent Design Constraints — "The Committee Chair MUST NOT simply average Bull and Bear outputs. It MUST identify the central investment thesis, supporting evidence, assumptions, disagreements, valuation, downside risks, and invalidation conditions, then produce a recommendation... with a conviction score and explanation." | Yes — this is the first feature implementing the Committee Chair agent | **Gap found; addressed in design** | spec.md's FRs require engaging with disagreements (FR-007) and restrict the recommendation enum (FR-008), but do not by themselves guarantee the Chair's reasoning *structurally* covers every element the constitution lists. Resolved by designing `CommitteeDecisionDraft` with a **separate, required field for each constitution-listed element** (central thesis, disagreements, valuation summary, downside risks, invalidation conditions) rather than one free-text `rationale` — Python then deterministically composes the final `CommitteeDecision.rationale` from all of them, so their presence is code-verified, not merely prompted for. See research.md. |
| Quality, Observability & Development Workflow — "Agent features MUST additionally include... cost measurement, and latency measurement" | Yes — this is an agent-facing (LLM-calling) feature | PASS | Reuses 004's `LLMCompletion`/logging pattern verbatim — `generate_decision` logs token usage and latency the same way `generate_thesis` does; no new mechanism needed |

**Constitution gap note**: The single row above marked "Gap found" reflects a requirement the
constitution states as a MUST for the Committee Chair specifically that spec.md's functional
requirements capture only partially (disagreement-engagement and enum-restriction, but not
the full element list). Per the constitution's authority over this plan, the resolution is
folded into this plan's data-model design (a richer `CommitteeDecisionDraft`) rather than
left as a prompting-only, unverifiable convention. No other gate failures were found; no
entries are required in Complexity Tracking.

## Project Structure

### Documentation (this feature)

```text
specs/006-committee-decision-engine/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md         # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
│   └── committee-interface.md
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
    │                            # CommitteeDecision, Recommendation from here
    ├── dcf/                     # Existing (003-dcf-valuation-engine) — unchanged; this
    │   └── ...                  # feature imports DCFResult from here, read-only
    ├── research/                 # Existing (004-investment-research-thesis) — unchanged;
    │   ├── provider.py            # this feature imports LLMProvider/LLMCompletion...
    │   └── openai_provider.py      # ...and OpenAIProvider from here, reused verbatim
    ├── report/                    # Existing (005-investment-committee-report) — unchanged;
    │   └── ...                     # this feature does not depend on it (report rendering
    │                                # already consumes whatever CommitteeDecision it is
    │                                # given, regardless of origin)
    └── committee/                  # New in this feature
        ├── __init__.py              # Re-exports: CommitteeAdjudicationContext,
        │                             # CommitteeDecisionDraft, build_prompt,
        │                             # generate_decision
        ├── context.py                 # CommitteeAdjudicationContext (InvestmentCase +
        │                              # DCFResult + bull AnalysisAssessment + bear
        │                              # AnalysisAssessment bundle)
        ├── draft.py                     # CommitteeDecisionDraft (the LLM-facing
        │                                # intermediate schema — central thesis,
        │                                # disagreements, valuation summary, downside
        │                                # risks, invalidation conditions, recommendation,
        │                                # confidence, dissent, evidence references)
        ├── prompt.py                      # build_prompt(context) -> (system, user);
        │                                  # pure, deterministic prompt construction
        └── generator.py                     # generate_decision(context, provider) ->
                                              # CommitteeDecision — validates the draft,
                                              # resolves evidence references, composes the
                                              # final rationale, logs cost/latency

tests/
└── unit/
    ├── test_smoke.py            # Existing — unchanged
    ├── domain/                  # Existing (002-domain-model) — unchanged
    ├── dcf/                      # Existing (003-dcf-valuation-engine) — unchanged
    ├── research/                  # Existing (004-investment-research-thesis) — unchanged
    ├── report/                     # Existing (005-investment-committee-report) — unchanged
    └── committee/                   # New in this feature
        ├── committee_fakes.py         # FakeLLMProvider test double (implements
        │                             # aic.research.provider.LLMProvider), local to this
        │                             # test directory, named to avoid a pytest
        │                             # module-name collision with tests/unit/research/
        │                             # (neither directory is a package — see 005's
        │                             # test_report_document.py precedent)
        ├── test_committee_context.py
        ├── test_committee_prompt.py
        ├── test_committee_generator.py # valid adjudication, untraceable-evidence
        │                              # rejection, provider-error propagation,
        │                              # schema-validation failure, recommendation
        │                              # restricted to the enum
        ├── test_dissent.py             # dissent present vs. absent
        └── test_committee_no_network_dependency.py  # zero-network-call verification
```

**Structure Decision**: Single-project, `src`-layout (unchanged). This feature adds one new
sibling sub-package, `aic.committee`, alongside `aic.domain`, `aic.dcf`, `aic.research`, and
`aic.report` — none of which is modified. `committee` depends on `domain`
(`InvestmentCase`, `AnalysisAssessment`, `CommitteeDecision`, `Recommendation`), `dcf`
(`DCFResult`), and `research` (`LLMProvider`, `LLMCompletion`, `OpenAIProvider` — reused, not
duplicated), never the reverse. `committee` does not depend on `report`, and `report` does
not need to change to consume a `CommitteeDecision` this feature produces.

## Complexity Tracking

*No Constitution Check violations requiring justification — this section intentionally left
empty. (The one Constitution Check row marked "Gap found" is a scope addition resolving a
constitutional requirement gap via richer data modeling, not a complexity-increasing
deviation requiring justification.)*
