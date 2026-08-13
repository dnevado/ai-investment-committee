# Contract: `aic.bullbear` Package Public Interface

This feature's "interface" is the Python import surface `aic.bullbear` exposes to future
consumers (006-committee-decision-engine, tests). There is no network API, CLI, or UI in
scope, and no existing contract is modified — this feature reuses `aic.research`'s
`LLMProvider`/`LLMCompletion`/`OpenAIProvider` contracts (004) verbatim rather than
redefining them.

## Import contract

```python
from aic.bullbear import (
    BullBearContext,
    AssessmentDraft,
    build_bull_prompt,
    build_bear_prompt,
    generate_bull_assessment,
    generate_bear_assessment,
)
```

- Every name above MUST be importable directly from `aic.bullbear`.
- Importing `aic.bullbear` MUST succeed with no network access and no OpenAI API key
  required — construction of an `OpenAIProvider` (from `aic.research`) may require a key,
  but merely importing `aic.bullbear` MUST NOT.

## `generate_bull_assessment` / `generate_bear_assessment` contract

```python
def generate_bull_assessment(
    context: BullBearContext, provider: LLMProvider
) -> AnalysisAssessment: ...
def generate_bear_assessment(
    context: BullBearContext, provider: LLMProvider
) -> AnalysisAssessment: ...
```

- `provider` MUST accept any conforming `aic.research.provider.LLMProvider`
  implementation (including `aic.research.OpenAIProvider` and a test's `FakeLLMProvider`) —
  this feature MUST NOT define or require a second, incompatible provider protocol
  (FR-005).
- Each function MUST perform its own independent call to `provider.complete_structured`.
  Neither function MUST read, receive, or otherwise depend on the other's
  `AnalysisAssessment`, `AssessmentDraft`, or `LLMCompletion` — calling one MUST NOT alter
  the prompt, context, or outcome of the other (FR-004).
- Each MUST validate the provider's raw response against `AssessmentDraft` before further
  processing; an invalid response MUST raise an explicit error (FR-006).
- Each MUST resolve every `supporting_evidence_ids` entry against
  `context.investment_case.evidence`; an unresolvable ID MUST raise an explicit error, and
  no partial `AnalysisAssessment` is ever returned in that case (FR-007).
- Each MUST reject a `confidence` value outside the existing bounded range (FR-008).
- Neither MUST perform, request, or infer any financial calculation —
  `context.valuation_result`'s figures are never recomputed (FR-009).
- Each MUST propagate provider errors (timeouts, rate limits, network failures) to the
  caller explicitly — MUST NOT substitute a fabricated or default `AnalysisAssessment`
  (FR-016).
- Each MUST log token usage and latency for its own invocation, distinguishable by role
  (research.md "Cost/latency measurement").
- Each MUST return the existing `AnalysisAssessment` domain model unmodified in shape —
  this feature MUST NOT add fields to it or subclass it, and MUST NOT introduce
  `BullAssessment`/`BearAssessment` types.

## `AssessmentDraft` contract

- Every field listed in data-model.md is required (no defaults) and the model forbids
  extra/unknown fields — matching the strict JSON-schema structured-output mode used by
  `OpenAIProvider` (see `aic.research.draft.ThesisDraft` / `aic.committee.draft.
  CommitteeDecisionDraft` for the established pattern this feature follows).
- The identical schema MUST be used for both the Bull and the Bear call — role is enforced
  by which prompt (`build_bull_prompt` vs. `build_bear_prompt`) is used, not by a
  schema-level distinction (research.md).

## Non-goals of this contract

- No CLI entry point is defined by this feature.
- No network-facing API is defined by this feature.
- No LangGraph node, graph, or multi-agent orchestration symbol is exported.
- No report/document rendering is exported.
- No `CommitteeDecision` generation or investment recommendation is exported — that remains
  006-committee-decision-engine's responsibility.
- No new `LLMProvider`/`LLMCompletion`/`OpenAIProvider` definition — these are imported from
  `aic.research`, not redefined.
- No `BullAssessment`/`BearAssessment` type — both roles produce the existing
  `AnalysisAssessment` unchanged.
