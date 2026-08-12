# Phase 1 Data Model: Investment Committee Report

One new Pydantic model (`CommitteeReport`) and one pure rendering function
(`render_report_document`). Every composed entity is reused completely unchanged from
002-domain-model and 003-dcf-valuation-engine.

## CommitteeReport

| Field | Type | Required | Notes |
|---|---|---|---|
| `company` | `Company` (aic.domain) | Yes | |
| `financial_snapshots` | `list[FinancialSnapshot]` (aic.domain) | Yes, `min_length=1` | Mirrors `InvestmentCase`'s own `min_length=1` constraint (002-domain-model); presented as-supplied, not reconciled across periods/currencies (spec Edge Cases) |
| `thesis` | `InvestmentThesis` (aic.domain) | Yes | Includes its own `supporting_evidence`, `key_assumptions`, `key_risks`, `invalidation_conditions` — presented unchanged (FR-002) |
| `dcf_result` | `DCFResult` (aic.dcf) | Yes | Read-only; the sole source of every valuation figure in the report (FR-003, FR-010; research.md) |
| `assessment` | `AnalysisAssessment` (aic.domain) | Yes | Conclusion, confidence, arguments, assumptions, risks — presented unchanged (FR-004) |
| `decision` | `CommitteeDecision` (aic.domain) | Yes | Recommendation, rationale, and dissent — presented unchanged (FR-005, FR-006) |

No validators beyond the fields being required (plus `financial_snapshots`'
`min_length=1`) — this feature does not cross-validate that `dcf_result`, `thesis`,
`assessment`, and `decision` all pertain to the same underlying analysis (spec Edge Cases;
spec Assumptions), consistent with 004-investment-research-thesis's own precedent for
`ResearchContext`. Constructing `CommitteeReport` with a missing required field raises a
`pydantic.ValidationError` — this *is* the "fail explicitly on missing input" behavior
required by FR-007/FR-014; no wrapper function is needed (research.md).

## render_report_document (pure function, `aic.report.document`)

```text
render_report_document(report: CommitteeReport) -> str
```

- Pure: no I/O, no randomness, no dependency on wall-clock time (FR-008, FR-009).
- Renders, in order: company header, financial snapshots, investment thesis (summary,
  supporting evidence, key assumptions, key risks, invalidation conditions), DCF valuation
  (enterprise value, equity value, implied value per share, per-year FCFF), committee
  assessment (conclusion, confidence, arguments, assumptions, risks), and committee decision
  (recommendation, rationale, dissent).
- Dissent rendering: each entry in `report.decision.dissent` is listed; if the list is
  empty, the document prints an explicit "No dissent recorded." line rather than omitting
  the section (FR-006, SC-004; research.md).
- Contains exactly `report`'s own structured content — no additional invented narrative
  (FR-008).

## Relationship to existing entities

```text
Company (002) ──────────────┐
FinancialSnapshot (002) ────┤
InvestmentThesis (002) ─────┼─▶ CommitteeReport ──▶ render_report_document ──▶ document (str)
DCFResult (003) ────────────┤        (direct
AnalysisAssessment (002) ───┤       construction
CommitteeDecision (002) ────┘       is assembly)
```

`InvestmentThesis` may itself have been produced by 004-investment-research-thesis's
`generate_thesis`, but this feature does not import or depend on `aic.research` — it
composes whatever `InvestmentThesis` it is given, regardless of its origin.
