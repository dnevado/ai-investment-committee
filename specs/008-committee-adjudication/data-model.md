# Phase 1 Data Model: Committee Adjudication Layer

No new entity or schema is introduced by this feature. This document maps each entity named
in `spec.md`'s Key Entities section to the existing type that already satisfies it, all
defined in 006-committee-decision-engine (`specs/006-committee-decision-engine/data-model.md`
has the full field-level definition; only the mapping is repeated here).

## CommitteeAdjudicationContext

- **Satisfying type**: `aic.committee.context.CommitteeAdjudicationContext`
- **Fields**: `investment_case: InvestmentCase`, `dcf_result: DCFResult`,
  `bull_assessment: AnalysisAssessment`, `bear_assessment: AnalysisAssessment` — exactly the
  four inputs this spec's FR-001 requires assembled into one structured, typed context.

## CommitteeDecisionDraft

- **Satisfying type**: `aic.committee.draft.CommitteeDecisionDraft`
- **Fields**: `central_thesis`, `key_disagreements`, `valuation_summary`, `downside_risks`,
  `invalidation_conditions`, `recommendation`, `confidence` (bounded 0–1), `dissent`,
  `supporting_evidence_ids` — this is the exact schema this spec's FR-004 requires the LLM's
  raw response be validated against, and its `key_disagreements` field is what this spec's
  FR-007 ("key points of agreement/disagreement") maps onto.

## InvestmentDecision (this spec's name for the final output)

- **Satisfying type**: `aic.domain.CommitteeDecision` (002-domain-model), returned unchanged
  by `aic.committee.generator.generate_decision`.
- **Fields**: `decision_id`, `recommendation`, `rationale`, `decision_timestamp`,
  `referenced_evidence: list[UUID]`, `referenced_thesis`, `valuation_reference`, `dissent`.
- **Note**: See `research.md` "InvestmentDecision maps to the existing `CommitteeDecision`
  domain entity" for why no new type is introduced. This is already the exact type
  005-investment-committee-report's `CommitteeReport.decision` field consumes, satisfying
  this spec's FR-018/SC-008 with zero adapter code.

## Computation / control flow

Identical to 006-committee-decision-engine's own `generate_decision` control flow — see
`specs/006-committee-decision-engine/data-model.md` "Computation / control flow" for the
full sequence (prompt construction → provider call → logging → draft validation → evidence
resolution → rationale composition → `CommitteeDecision` construction). No step is added,
removed, or altered by this feature.

## Relationship to existing entities

```text
InvestmentCase (002) ──┐
                         ├─▶ CommitteeAdjudicationContext ──▶ generate_decision ──▶ CommitteeDecision (002)
DCFResult (003) ────────┤         (= this spec's "InvestmentDecision")                    │
bull AnalysisAssessment ┤                                                                 │
  (002) ────────────────┤                                                                 ▼
bear AnalysisAssessment ┘                                                    consumed unchanged by
  (002)                                                                005-investment-committee-report
```
