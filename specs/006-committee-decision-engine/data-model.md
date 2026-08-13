# Phase 1 Data Model: Investment Committee Decision Engine

One new Pydantic model (`CommitteeAdjudicationContext`) and one LLM-facing intermediate
schema (`CommitteeDecisionDraft`). The `LLMProvider`/`LLMCompletion` protocol and
`OpenAIProvider` adapter are reused unchanged from `aic.research` (004). The feature's final
output reuses `CommitteeDecision` (002-domain-model) completely unchanged.

## CommitteeAdjudicationContext

| Field | Type | Required | Notes |
|---|---|---|---|
| `investment_case` | `InvestmentCase` (aic.domain) | Yes | Supplies `Company`, `InvestmentThesis`, and `Evidence` |
| `dcf_result` | `DCFResult` (aic.dcf) | Yes | Read-only valuation figures — never recomputed (FR-006) |
| `bull_assessment` | `AnalysisAssessment` (aic.domain) | Yes | The independently-produced upside case (generation out of scope; spec Assumptions) |
| `bear_assessment` | `AnalysisAssessment` (aic.domain) | Yes | The independently-produced downside case (generation out of scope; spec Assumptions) |

No validators beyond all four fields being required — this feature does not cross-validate
that `dcf_result`, `bull_assessment`, and `bear_assessment` all pertain to the same
`investment_case` (spec Edge Cases; spec Assumptions), consistent with 004/005's own
`ResearchContext`/`CommitteeReport` precedent.

## CommitteeDecisionDraft (LLM-facing intermediate schema — not a domain entity)

| Field | Type | Required | Notes |
|---|---|---|---|
| `central_thesis` | `str` | Yes | The Chair's synthesis of the investment thesis in adjudication context |
| `key_disagreements` | `list[str]` | Yes (may be empty) | Where the bull and bear assessments diverge, and how the Chair weighed each point (FR-007) |
| `valuation_summary` | `str` | Yes | How the DCF valuation bears on the decision — narrative framing only; the underlying figures are never recomputed (FR-006) |
| `downside_risks` | `list[str]` | Yes (may be empty) | Constitution-required element of the Chair's reasoning |
| `invalidation_conditions` | `list[str]` | Yes (may be empty) | Constitution-required element of the Chair's reasoning |
| `recommendation` | `Recommendation` (aic.domain enum) | Yes | Restricted to `BUY`/`WATCH`/`AVOID` — no other value is representable (FR-008) |
| `confidence` | `float`, `0 <= x <= 1` | Yes | LLM-proposed, Python-validated against the same bounded range already used for `AnalysisAssessment.confidence` |
| `dissent` | `list[str]` | Yes (may be empty) | The unadopted bull or bear position, when the Chair does not fully agree with one side (FR-009) |
| `supporting_evidence_ids` | `list[UUID]` | Yes (may be empty) | References into `CommitteeAdjudicationContext.investment_case.evidence` — resolved, never trusted as content (FR-005) |

This is the exact schema passed to `LLMProvider.complete_structured` and the exact shape the
LLM's raw response is validated against (FR-004) before any further processing. Every
constitution-listed Chair responsibility (central thesis, disagreements, valuation,
downside risks, invalidation conditions) has its own required field — omitting one is a
schema-validation failure, not a silent gap (research.md).

## Computation / control flow (`generate_decision`, not a stored field)

```text
generate_decision(context: CommitteeAdjudicationContext, provider: LLMProvider) -> CommitteeDecision:
    system_prompt, user_prompt = build_prompt(context)          # deterministic, no I/O
    completion = provider.complete_structured(
        system_prompt=system_prompt, user_prompt=user_prompt, schema=CommitteeDecisionDraft,
    )                                                             # may raise a provider error (FR-013)
    log.info("committee decision adjudicated", extra={
        "prompt_tokens": completion.prompt_tokens,
        "completion_tokens": completion.completion_tokens,
        "latency_ms": completion.latency_ms,
    })                                                            # research.md "Cost/latency measurement"

    draft = CommitteeDecisionDraft.model_validate(completion.content)  # FR-004; raises explicitly if invalid

    known_evidence_ids = {e.evidence_id for e in context.investment_case.evidence}
    for evidence_id in draft.supporting_evidence_ids:
        if evidence_id not in known_evidence_ids:
            raise ValueError(f"LLM referenced unknown evidence_id: {evidence_id}")  # FR-005

    rationale = _compose_rationale(draft)  # deterministic Python string composition —
                                            # central_thesis + key_disagreements +
                                            # valuation_summary + downside_risks +
                                            # invalidation_conditions + confidence
                                            # (the conviction score), in that order

    return CommitteeDecision(
        decision_id=uuid4(),
        recommendation=draft.recommendation,
        rationale=rationale,
        referenced_evidence=draft.supporting_evidence_ids,         # already-validated UUIDs
        referenced_thesis=context.investment_case.thesis,
        valuation_reference=None,                                  # research.md "valuation_reference is left unset"
        dissent=draft.dissent,
    )
```

`_compose_rationale(draft: CommitteeDecisionDraft) -> str` is a separate, pure function —
string templating only, no I/O, no randomness, no LLM call (mirrors 004/005's
`render_*_document` pattern).

## Relationship to existing entities

```text
InvestmentCase (002) ──┐
                         ├─▶ CommitteeAdjudicationContext ──▶ generate_decision ──▶ CommitteeDecision (002, unchanged)
DCFResult (003) ────────┤         │                                                        │
bull AnalysisAssessment ┤         ▼                                                        │
  (002) ────────────────┤   build_prompt (deterministic)                                    │
bear AnalysisAssessment ┘         │                                                        │
  (002)                           ▼                                                        ▼
                             LLMProvider.complete_structured                    consumed unchanged by
                             (OpenAIProvider from 004 in production,            005-investment-committee-report
                              FakeLLMProvider in tests)
```
