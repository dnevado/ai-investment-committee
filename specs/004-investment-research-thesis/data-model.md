# Phase 1 Data Model: Investment Research & Thesis Generation

Two new Pydantic models (`ResearchContext`, `ThesisDraft`), one protocol (`LLMProvider`),
one small result type (`LLMCompletion`), and one settings addition. The feature's final
output reuses `InvestmentThesis` (002-domain-model) completely unchanged.

## ResearchContext

| Field | Type | Required | Notes |
|---|---|---|---|
| `investment_case` | `InvestmentCase` (aic.domain) | Yes | Supplies `Company`, `FinancialSnapshot`(s), and `Evidence` |
| `dcf_result` | `DCFResult` (aic.dcf) | Yes | Read-only valuation figures — never recomputed (FR-006) |

No validators beyond both fields being required — this feature does not cross-validate
that `dcf_result` "belongs to" `investment_case` (spec Edge Cases; spec Assumptions).

## ThesisDraft (LLM-facing intermediate schema — not a domain entity)

| Field | Type | Required | Notes |
|---|---|---|---|
| `summary` | `str` | Yes | |
| `supporting_evidence_ids` | `list[UUID]` | Yes (may be empty) | References into `ResearchContext.investment_case.evidence` — resolved, never trusted as content |
| `key_assumptions` | `list[str]` | Yes (may be empty) | |
| `key_risks` | `list[str]` | Yes (may be empty) | |
| `invalidation_conditions` | `list[str]` | Yes (may be empty) | |

This is the exact schema passed to `LLMProvider.complete_structured` and the exact shape
the LLM's raw response is validated against (FR-004) before any further processing.
Contains no monetary/numeric field — structurally enforces FR-006 (no financial
calculation possible through this schema).

## LLMCompletion (provider result wrapper)

| Field | Type | Notes |
|---|---|---|
| `content` | `dict[str, Any]` | Raw, not-yet-validated structured payload |
| `prompt_tokens` | `int` | For cost/latency measurement (research.md) |
| `completion_tokens` | `int` | For cost/latency measurement |
| `latency_ms` | `float` | Wall-clock time of the provider call |

## LLMProvider (protocol, `aic.research.provider`)

```text
complete_structured(*, system_prompt: str, user_prompt: str, schema: type[BaseModel]) -> LLMCompletion
```

Implemented by `OpenAIProvider` (production) and `FakeLLMProvider` (test double, lives in
`tests/unit/research/fakes.py`, not shipped source).

## Settings addition (`aic.settings.AppSettings`)

| Field | Type | Required | Notes |
|---|---|---|---|
| `openai_api_key` | `str \| None` | No (default `None`) | Sourced from `AIC_OPENAI_API_KEY`; never hardcoded, never logged (FR-009) |

## Computation / control flow (`generate_thesis`, not a stored field)

```text
generate_thesis(context: ResearchContext, provider: LLMProvider) -> InvestmentThesis:
    system_prompt, user_prompt = build_prompt(context)          # deterministic, no I/O
    completion = provider.complete_structured(
        system_prompt=system_prompt, user_prompt=user_prompt, schema=ThesisDraft,
    )                                                             # may raise a provider error (FR-013)
    log.info("thesis generation completed", extra={
        "prompt_tokens": completion.prompt_tokens,
        "completion_tokens": completion.completion_tokens,
        "latency_ms": completion.latency_ms,
    })                                                            # research.md "Cost/latency measurement"

    draft = ThesisDraft.model_validate(completion.content)        # FR-004; raises explicitly if invalid

    known_evidence = {e.evidence_id: e for e in context.investment_case.evidence}
    resolved_evidence = []
    for evidence_id in draft.supporting_evidence_ids:
        if evidence_id not in known_evidence:
            raise ValueError(f"LLM referenced unknown evidence_id: {evidence_id}")  # FR-005
        resolved_evidence.append(known_evidence[evidence_id])

    return InvestmentThesis(
        summary=draft.summary,
        supporting_evidence=resolved_evidence,                    # original Evidence objects only
        key_assumptions=draft.key_assumptions,
        key_risks=draft.key_risks,
        invalidation_conditions=draft.invalidation_conditions,
    )
```

`render_thesis_document(thesis: InvestmentThesis) -> str` is a separate, pure function —
string templating only, no I/O, no randomness (FR-011, FR-012).

## Relationship to existing entities

```text
InvestmentCase (002) ──┐
                         ├─▶ ResearchContext ──▶ generate_thesis ──▶ InvestmentThesis (002, unchanged)
DCFResult (003) ────────┘         │                                        │
                                    ▼                                       ▼
                              build_prompt (deterministic)          render_thesis_document
                                    │                                        │
                                    ▼                                       ▼
                              LLMProvider.complete_structured        ThesisDocument (str)
                              (OpenAIProvider in production,
                               FakeLLMProvider in tests)
```
