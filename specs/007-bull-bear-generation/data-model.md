# Phase 1 Data Model: Bull/Bear Analysis Generation

One new Pydantic model (`BullBearContext`) and one LLM-facing intermediate schema
(`AssessmentDraft`), shared by both roles. The `LLMProvider`/`LLMCompletion` protocol and
`OpenAIProvider` adapter are reused unchanged from `aic.research` (004). The feature's final
output reuses `AnalysisAssessment` (002-domain-model) completely unchanged, produced twice
(once per role).

## BullBearContext

| Field | Type | Required | Notes |
|---|---|---|---|
| `investment_case` | `InvestmentCase` (aic.domain) | Yes | Supplies `Company`, `InvestmentThesis`, and `Evidence` |
| `valuation_result` | `ValuationResult` (aic.domain) | Yes | Read-only valuation context — never recomputed (FR-009); per spec Assumptions, this is the domain-level summary type, not `DCFResult` |

No validators beyond both fields being required — this feature does not cross-validate that
`valuation_result` "belongs to" `investment_case` (spec Edge Cases; spec Assumptions),
consistent with 004/005/006's own precedent.

## AssessmentDraft (LLM-facing intermediate schema — not a domain entity; shared by both roles)

| Field | Type | Required | Notes |
|---|---|---|---|
| `conclusion` | `str` | Yes | The role's overall conclusion — framed as the strongest upside case (Bull) or the strongest challenge to the thesis (Bear), per the prompt used |
| `confidence` | `float`, `0 <= x <= 1` | Yes | LLM-proposed, Python-validated against the same bounded range already used for `AnalysisAssessment.confidence` (FR-008) |
| `arguments` | `list[str]` | Yes (may be empty) | Supporting arguments; for Bull this includes catalysts and outperformance conditions, for Bear this includes the core challenge to the thesis — folded in via role-specific prompting, not a separate field (research.md) |
| `assumptions` | `list[str]` | Yes (may be empty) | The assumptions underpinning the role's case |
| `risks` | `list[str]` | Yes (may be empty) | For Bull, risks/caveats to the upside case; for Bear, this is the core content — downside risks, adverse scenarios, and invalidation conditions, folded in via role-specific prompting (research.md) |
| `supporting_evidence_ids` | `list[UUID]` | Yes (may be empty) | References into `BullBearContext.investment_case.evidence` — resolved, never trusted as content (FR-007) |

This is the exact schema passed to `LLMProvider.complete_structured` for **both** the Bull
and the Bear call, and the exact shape each LLM's raw response is validated against
(FR-006) before any further processing. Contains no field beyond the bounded `confidence`
that could carry a financial calculation (FR-009).

## Computation / control flow (`generate_bull_assessment` / `generate_bear_assessment`, not stored fields)

```text
_generate(context: BullBearContext, provider: LLMProvider, role: str, build_prompt) -> AnalysisAssessment:
    system_prompt, user_prompt = build_prompt(context)            # deterministic, no I/O
    completion = provider.complete_structured(
        system_prompt=system_prompt, user_prompt=user_prompt, schema=AssessmentDraft,
    )                                                               # may raise a provider error (FR-016)
    log.info(f"{role} assessment generated", extra={
        "prompt_tokens": completion.prompt_tokens,
        "completion_tokens": completion.completion_tokens,
        "latency_ms": completion.latency_ms,
    })                                                              # research.md "Cost/latency measurement"

    draft = AssessmentDraft.model_validate(completion.content)      # FR-006; raises explicitly if invalid

    known_evidence_ids = {e.evidence_id for e in context.investment_case.evidence}
    for evidence_id in draft.supporting_evidence_ids:
        if evidence_id not in known_evidence_ids:
            raise ValueError(f"LLM referenced unknown evidence_id: {evidence_id}")  # FR-007

    return AnalysisAssessment(
        assessment_id=uuid4(),
        conclusion=draft.conclusion,
        confidence=draft.confidence,
        arguments=draft.arguments,
        supporting_evidence=draft.supporting_evidence_ids,          # already-validated UUIDs
        assumptions=draft.assumptions,
        risks=draft.risks,
    )

generate_bull_assessment(context, provider) -> AnalysisAssessment:
    return _generate(context, provider, role="bull", build_prompt=build_bull_prompt)

generate_bear_assessment(context, provider) -> AnalysisAssessment:
    return _generate(context, provider, role="bear", build_prompt=build_bear_prompt)
```

`build_bull_prompt`/`build_bear_prompt` are separate, pure functions — string construction
only, no I/O, no randomness, no LLM call (mirror 004/006's `build_prompt` pattern). Neither
`generate_bull_assessment` nor `generate_bear_assessment` ever calls the other or has
access to the other's `AnalysisAssessment`/`AssessmentDraft`/`LLMCompletion` — the only
thing they share is the private `_generate` helper's *mechanics*, not any *content*
(FR-004; research.md).

## Relationship to existing entities

```text
InvestmentCase (002) ──┐
                         ├─▶ BullBearContext ──▶ generate_bull_assessment ──▶ AnalysisAssessment (Bull)
ValuationResult (002) ──┘         │
                                    ├────────────▶ generate_bear_assessment ──▶ AnalysisAssessment (Bear)
                                    ▼
                              build_bull_prompt / build_bear_prompt (deterministic, role-specific)
                                    │
                                    ▼
                              LLMProvider.complete_structured
                              (OpenAIProvider from 004 in production,
                               FakeLLMProvider in tests)
```

Both resulting `AnalysisAssessment` instances are indistinguishable by type — a caller
(e.g., a future wiring into 006-committee-decision-engine's `CommitteeAdjudicationContext`)
must track which is which by which function produced it, not by inspecting the object
itself (spec Key Entities).
