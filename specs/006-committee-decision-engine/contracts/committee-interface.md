# Contract: `aic.committee` Package Public Interface

This feature's "interface" is the Python import surface `aic.committee` exposes to future
consumers (a future application/CLI layer, tests). There is no network API, CLI, or UI in
scope, and no existing contract is modified — this feature reuses `aic.research`'s
`LLMProvider`/`LLMCompletion`/`OpenAIProvider` contracts (004) verbatim rather than
redefining them.

## Import contract

```python
from aic.committee import (
    CommitteeAdjudicationContext,
    CommitteeDecisionDraft,
    build_prompt,
    generate_decision,
)
```

- Every name above MUST be importable directly from `aic.committee`.
- Importing `aic.committee` MUST succeed with no network access and no OpenAI API key
  required — construction of an `OpenAIProvider` (from `aic.research`) may require a key,
  but merely importing `aic.committee` MUST NOT.

## `generate_decision` contract

```python
def generate_decision(
    context: CommitteeAdjudicationContext, provider: LLMProvider
) -> CommitteeDecision: ...
```

- `provider` MUST accept any conforming `aic.research.provider.LLMProvider` implementation
  (including `aic.research.OpenAIProvider` and a test's `FakeLLMProvider`) — this feature
  MUST NOT define or require a second, incompatible provider protocol.
- MUST validate the provider's raw response against `CommitteeDecisionDraft` before further
  processing; an invalid response MUST raise an explicit error (FR-004).
- MUST resolve every `supporting_evidence_ids` entry against
  `context.investment_case.evidence`; an unresolvable ID MUST raise an explicit error, and
  no partial `CommitteeDecision` is ever returned in that case (FR-005).
- MUST NOT perform, request, or infer any financial calculation — `context.dcf_result`'s
  figures are never recomputed (FR-006).
- MUST NOT produce a recommendation by averaging `bull_assessment` and `bear_assessment`'s
  confidence or conclusions; the composed `rationale` MUST include the draft's
  `key_disagreements` section (FR-007).
- MUST restrict `recommendation` to the existing `Recommendation` enum (FR-008).
- MUST propagate provider errors (timeouts, rate limits, network failures) to the caller
  explicitly — MUST NOT substitute a fabricated or default `CommitteeDecision` (FR-013).
- MUST log token usage and latency for every invocation (research.md "Cost/latency
  measurement").
- MUST return the existing `CommitteeDecision` domain model unmodified in shape — this
  feature MUST NOT add fields to it or subclass it.

## `CommitteeDecisionDraft` contract

- Every field listed in data-model.md is required (no defaults) and the model forbids
  extra/unknown fields — matching the strict JSON-schema structured-output mode used by
  `OpenAIProvider` (see `aic.research.draft.ThesisDraft` for the established pattern this
  feature follows).
- Contains a separate field for each constitution-listed Committee Chair responsibility
  (central thesis, disagreements, valuation summary, downside risks, invalidation
  conditions) — omitting any one of them from the LLM's response is a schema-validation
  failure, not a silent gap (research.md).

## Non-goals of this contract

- No CLI entry point is defined by this feature.
- No network-facing API is defined by this feature.
- No LangGraph node, graph, or multi-agent orchestration symbol is exported.
- No report/document rendering is exported — 005-investment-committee-report already
  renders whatever `CommitteeDecision` it is given, regardless of how it was produced.
- No Bull/Bear assessment *generation* is exported — `bull_assessment`/`bear_assessment`
  are accepted as already-produced input, never created by this feature.
- No new `LLMProvider`/`LLMCompletion`/`OpenAIProvider` definition — these are imported from
  `aic.research`, not redefined.
