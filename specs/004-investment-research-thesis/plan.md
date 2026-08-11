# Implementation Plan: Investment Research & Thesis Generation

**Branch**: `004-investment-research-thesis` | **Date**: 2026-08-11 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/004-investment-research-thesis/spec.md`

## Summary

Add a new `aic.research` sub-package that assembles an `InvestmentCase` and a `DCFResult`
into a structured `ResearchContext`, calls OpenAI (through a swappable `LLMProvider`
protocol) to produce a narrow LLM-facing `ThesisDraft` (summary, assumption/risk/
invalidation text, and evidence *references* only — no reproduced evidence content, no
numbers), resolves those references against the real input `Evidence` objects to build
the existing `InvestmentThesis` domain model unchanged, and deterministically renders it
to a Markdown document. Credentials come from a new optional field on the existing
`AppSettings`. No LangGraph, no recommendation/Bull-Bear content, no persistence. Tests
run entirely against a fake provider — zero real OpenAI calls.

## Technical Context

**Language/Version**: Python 3.12+ (matches the existing repository baseline)

**Primary Dependencies**: Pydantic v2 (existing); `openai` (the official OpenAI Python
SDK) — **new** dependency, explicitly sanctioned by the constitution's baseline
technology list ("OpenAI as the initial LLM provider"); `pydantic-settings` (existing,
for the new API-key setting); Python's standard-library `logging` for cost/latency
measurement (see Constitution Check note below)

**Storage**: N/A — no persistence (FR-014)

**Testing**: pytest, using a fake `LLMProvider` test double for all of this feature's own
tests (FR-003, SC-003); a small number of tests for the OpenAI adapter itself mock the
`openai` SDK client directly (still zero real network calls)

**Target Platform**: Same as the existing repository — local developer machine, Windows
PowerShell as the primary documented/verified shell

**Project Type**: Single Python package; this feature adds a `research` sub-package
under the existing `aic` package, and makes one small addition to the existing
`aic.settings` module

**Performance Goals**: N/A — no throughput requirement stated; OpenAI response latency is
external and outside this feature's control

**Constraints**: No LangGraph or multi-agent orchestration (FR-008); no persistence
(FR-014); OpenAI credentials only via `aic.settings`, never hardcoded (FR-009, FR-010);
the LLM's raw response is never trusted directly — validated against a typed schema
before use (FR-004); every `supporting_evidence` entry must be traceable to the supplied
input, enforced structurally rather than by fuzzy content-matching (FR-005; see research.md);
no financial calculation performed by or requested of the LLM (FR-006); document
rendering is deterministic Python code, not a second LLM call (FR-011, FR-012)

**Scale/Scope**: One new sub-package, `aic.research` (`ResearchContext`, `ThesisDraft`,
`LLMProvider` protocol, `OpenAIProvider` adapter, prompt construction, the
`generate_thesis` orchestration function, and a Markdown document renderer), plus one new
optional field on the existing `AppSettings` — no other existing file is modified

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle / Section | Applies to this feature? | Status | Notes |
|---|---|---|---|
| I. Evidence Before Opinion | Yes — this is the first feature where it governs a real LLM call | PASS | `supporting_evidence` is structurally restricted to the supplied input's `Evidence` objects (FR-005); the LLM cannot introduce unsourced "facts" into that field |
| II. LLM Proposes, Code Computes | Yes — directly enforced | PASS | The LLM-facing `ThesisDraft` schema has no numeric/financial field at all; DCF figures come from `DCFResult` read-only (FR-006) |
| III. Structured Outputs Only | Yes | PASS | The LLM's raw response is validated against `ThesisDraft` before any further processing; raw text is never trusted as application state (FR-004) |
| IV. Bull/Bear Symmetry | No — explicitly out of scope | N/A | FR-007 forbids Bull/Bear or committee content in this feature |
| V. Explicit Assumptions | Yes | PASS | `key_assumptions` remains a required part of the output `InvestmentThesis` |
| VI. Deterministic Valuation | No new calculation introduced | N/A | `DCFResult` is consumed read-only (FR-006); no valuation math added |
| VII. Traceability | Yes — the feature's central mechanism | PASS | Evidence references are resolved against the real input `Evidence` objects; an unresolvable reference is rejected explicitly (FR-005) |
| VIII. Minimal Architecture, No Premature Infrastructure | Yes | PASS | One new sanctioned dependency (`openai`, already named in the constitution's baseline stack — not "unnecessary"); no persistence, no new infrastructure layer beyond one protocol + one adapter |
| IX. No RAG in MVP | Yes | PASS | No document ingestion/retrieval; structured context is passed directly to the model, exactly the pattern the constitution's "No RAG in MVP" principle describes as acceptable |
| X. Provider Abstraction | Yes — the principle this feature operationalizes for the first time | PASS | `LLMProvider` is a protocol; `OpenAIProvider` is one swappable implementation; every test in this feature runs against a fake implementation (FR-003) |
| Architecture & Agent Design Constraints ("Research: establish evidence"; "Do not put investment logic inside OpenAI adapters") | Yes | PASS | This feature is a scoped slice of the constitution's "Research" agent responsibility, implemented as an application service (`generate_thesis`), not a domain model; `OpenAIProvider` contains only transport logic — the evidence-resolution/validation logic lives in `generate_thesis`, not the adapter |
| Quality, Observability & Development Workflow — "Agent features MUST additionally include... cost measurement, and latency measurement" | Yes — this is the first agent-facing (LLM-calling) feature in the codebase | **Gap found; addressed in design** | spec.md's FRs do not mention cost/latency measurement — the constitution's Quality Principles section requires it for agent features regardless. Resolved minimally: `OpenAIProvider` captures token usage and elapsed latency from the API response and `generate_thesis` logs them (via `logging`, no new persistence/observability subsystem) — see research.md "Cost/latency measurement" for the full rationale |

**Constitution gap note**: The single row above marked "Gap found" reflects a requirement
the constitution states as a MUST for agent features that spec.md's functional
requirements did not capture. Per the constitution's authority over this plan, a minimal,
proportionate resolution (structured logging of token usage and latency, no new
subsystem) is included in this plan's scope rather than silently skipped. No other gate
failures were found; no entries are required in Complexity Tracking (this is an addition
resolving a constitutional gap, not a complexity-increasing deviation requiring
justification).

## Project Structure

### Documentation (this feature)

```text
specs/004-investment-research-thesis/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md         # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
│   └── research-interface.md
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
src/
└── aic/
    ├── __init__.py            # Existing — unchanged
    ├── settings.py             # Existing — MODIFIED: adds one optional `openai_api_key` field
    ├── agents/                 # Existing pre-existing prompt scaffolding — untouched, out of scope
    │   └── prompts/
    ├── domain/                 # Existing (002-domain-model) — unchanged; this feature imports
    │   └── ...                 # `InvestmentCase`, `InvestmentThesis`, `Evidence` from here
    ├── dcf/                     # Existing (003-dcf-valuation-engine) — unchanged; this feature
    │   └── ...                  # imports `DCFResult` from here, read-only
    └── research/                 # New in this feature
        ├── __init__.py          # Re-exports: ResearchContext, ThesisDraft, LLMProvider,
        │                         # LLMCompletion, OpenAIProvider, generate_thesis,
        │                         # render_thesis_document
        ├── context.py            # ResearchContext (InvestmentCase + DCFResult bundle)
        ├── draft.py                # ThesisDraft (the LLM-facing intermediate schema —
        │                            # evidence references, not evidence content)
        ├── provider.py               # LLMProvider protocol; LLMCompletion (content +
        │                             # token usage + latency)
        ├── openai_provider.py         # OpenAIProvider — the concrete `openai` SDK adapter
        ├── prompt.py                   # build_prompt(context) -> (system, user); pure,
        │                               # deterministic prompt construction
        ├── generator.py                  # generate_thesis(context, provider) ->
        │                                 # InvestmentThesis — validates the draft,
        │                                 # resolves evidence references, logs cost/latency
        └── document.py                    # render_thesis_document(thesis) -> str
                                            # (deterministic Markdown)

tests/
└── unit/
    ├── test_smoke.py            # Existing — unchanged
    ├── domain/                  # Existing (002-domain-model) — unchanged
    ├── dcf/                      # Existing (003-dcf-valuation-engine) — unchanged
    └── research/                  # New in this feature
        ├── fakes.py               # FakeLLMProvider test double (implements LLMProvider)
        ├── test_context.py
        ├── test_prompt.py
        ├── test_generator.py       # valid generation, untraceable-evidence rejection,
        │                           # provider-error propagation, schema-validation failure
        ├── test_document.py         # deterministic rendering
        └── test_openai_provider.py   # adapter request/response mapping, `openai` SDK
                                       # client mocked — zero real network calls
```

**Structure Decision**: Single-project, `src`-layout (unchanged). This feature adds one
new sibling sub-package, `aic.research`, alongside `aic.domain` and `aic.dcf` — neither of
which is modified. `research` depends on both `domain` (`InvestmentCase`,
`InvestmentThesis`, `Evidence`) and `dcf` (`DCFResult`), never the reverse. The only
existing file touched is `src/aic/settings.py`, which gains one optional field.

## Complexity Tracking

*No Constitution Check violations requiring justification — this section intentionally
left empty. (The one Constitution Check row marked "Gap found" is a scope addition
resolving a constitutional requirement gap, not a complexity deviation.)*
