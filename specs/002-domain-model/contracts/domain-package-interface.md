# Contract: `aic.domain` Package Public Interface

This feature's only "interface" is the Python import surface `aic.domain` exposes to
every future consumer (research, Bull/Bear agents, valuation engine, committee logic,
tests). There is no network API, CLI, or UI in scope.

## Import contract

```python
from aic.domain import (
    Company,
    Evidence,
    EvidenceType,
    FinancialSnapshot,
    InvestmentThesis,
    InvestmentCase,
    AnalysisAssessment,
    ValuationResult,
    CommitteeDecision,
    Recommendation,
    Money,
)
```

- Every name above MUST be importable directly from `aic.domain` (FR-019) — callers
  never need to know which internal module (`company.py`, `evidence.py`, ...) defines a
  given model.
- Importing `aic.domain` MUST succeed with no network access, no file I/O, and no
  environment-variable reads (FR-018, SC-006).

## Construction contract

- Every model above is a Pydantic `BaseModel`. Constructing one with valid data MUST
  succeed and return a fully typed instance — never a plain `dict` (SC-001).
- Constructing one with invalid or missing required data MUST raise
  `pydantic.ValidationError` — never silently coerce, drop, or default the value
  (FR-012, FR-013, FR-014).
- `company_id`, `evidence_id`, `case_id`, `assessment_id`, `valuation_id`, and
  `decision_id` are `uuid.UUID`-typed fields that MUST be supplied explicitly by the
  caller — the domain models perform no auto-generation. Construction without one of
  these fields MUST fail with an explicit validation error, the same as any other
  missing required field (FR-010).

## Currency contract

- `Money.currency` MUST reject any value that is not a real ISO 4217 alphabetic
  currency code, validated against the complete active code set — not a curated subset
  (spec Clarification, SC-002).
- A monetary value MUST NOT be constructible as a bare amount without its `Money.currency`
  also being present and valid — every monetary field (`FinancialSnapshot`'s metrics,
  `ValuationResult.estimated_value`) is typed as `Money`, not a bare `Decimal` with a
  separately-declared currency field.
- On `FinancialSnapshot`, if more than one monetary metric is populated, all populated
  `Money` values MUST share the same currency; a mismatch MUST fail with an explicit
  validation error.
- `Money` itself exposes no arithmetic or conversion methods — it is a typed container
  only.

## Serialization contract

- Every model MUST support a lossless round trip through Pydantic v2's dict-conversion
  methods: `Model.model_validate(original.model_dump()) == original` for every core
  model, including nested `Money` values (spec Clarification, FR-016, SC-004). This is
  the *canonical* form — a JSON string, if ever produced, is that same dict encoded, not
  a separate contract this feature guarantees independently.

## Non-goals of this contract

- No CLI entry point is defined by this feature.
- No network-facing API is defined by this feature.
- No repository, service, agent, or persistence symbol is exported by `aic.domain`.
- No calculation function (DCF, ratios, scoring, currency conversion) is exported by
  `aic.domain`.
