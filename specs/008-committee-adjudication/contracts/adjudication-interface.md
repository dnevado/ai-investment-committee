# Contract: Committee Adjudication Layer

This feature introduces no new import surface. Its contract is satisfied entirely by the
existing `aic.committee` package's public interface, defined in full at
`specs/006-committee-decision-engine/contracts/committee-interface.md`. This document states
only how this spec's requirements map onto that existing, unmodified contract.

## Import contract (existing, unchanged)

```python
from aic.committee import (
    CommitteeAdjudicationContext,
    CommitteeDecisionDraft,
    build_prompt,
    generate_decision,
)
```

- Every name above is already importable directly from `aic.committee`.
- Importing `aic.committee` already succeeds with no network access and no LLM provider
  credentials required (spec FR-003, satisfied).

## `generate_decision` — requirement mapping

| This spec's requirement | Satisfied by existing `generate_decision` behavior |
|---|---|
| FR-002 (LLM synthesizes case+valuation+assessments into a decision, reusing existing decision contract) | Returns `aic.domain.CommitteeDecision` unchanged |
| FR-003 (existing provider abstraction only, no new one) | Accepts any `aic.research.provider.LLMProvider` |
| FR-004 (raw response validated before trust) | `CommitteeDecisionDraft.model_validate(completion.content)` |
| FR-005 (evidence-ID validation, no fabrication) | Resolves `supporting_evidence_ids` against `context.investment_case.evidence`; raises on any unknown ID |
| FR-006 (no financial calculation by the LLM) | `dcf_result` consumed read-only; `CommitteeDecisionDraft` has no financial field beyond bounded `confidence` |
| FR-007 (rationale engages agreement/disagreement, not averaging) | Composed `rationale` includes `key_disagreements` as a required section |
| FR-008 (recommendation restricted to existing set) | `recommendation: Recommendation` — no other value is representable |
| FR-009 (dissent recorded when Chair overrules a side) | `dissent` passed through from the validated draft unchanged |
| FR-014 (provider errors propagate, never fabricated) | `provider.complete_structured` errors are not caught or suppressed — they propagate to the caller |
| FR-017 (read-only composition, no mutation of inputs) | No field of `context` or its nested entities is ever reassigned |
| FR-018 / SC-008 (consumable by the report layer, no new adapter) | Returns `aic.domain.CommitteeDecision`, the exact type `CommitteeReport.decision` already expects |

## Non-goals of this contract (inherited unchanged)

- No CLI entry point, network-facing API, LangGraph node, or multi-agent orchestration.
- No report/document rendering (005 already owns that).
- No new `LLMProvider`/`LLMCompletion`/`OpenAIProvider` definition.
- No new decision/adjudication-context type — this spec's `InvestmentDecision` and
  `CommitteeAdjudicationContext`/`CommitteeDecisionDraft` are the existing
  `CommitteeDecision`/`CommitteeAdjudicationContext`/`CommitteeDecisionDraft` types,
  unchanged.
