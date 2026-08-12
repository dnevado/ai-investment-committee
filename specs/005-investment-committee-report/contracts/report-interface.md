# Contract: `aic.report` Package Public Interface

This feature's "interface" is the Python import surface `aic.report` exposes to future
consumers (a future application/CLI layer, tests). There is no network API, CLI, or UI in
scope, and no existing contract is modified.

## Import contract

```python
from aic.report import (
    CommitteeReport,
    render_report_document,
)
```

- Both names above MUST be importable directly from `aic.report`.
- Importing `aic.report` MUST succeed with no network access and no external dependency —
  this feature has none.

## `CommitteeReport` contract

```python
class CommitteeReport(BaseModel):
    company: Company
    financial_snapshots: list[FinancialSnapshot]  # min_length=1
    thesis: InvestmentThesis
    dcf_result: DCFResult
    assessment: AnalysisAssessment
    decision: CommitteeDecision
```

- Every field is required; constructing `CommitteeReport` with any field missing MUST raise
  `pydantic.ValidationError` — no partial or fabricated report is ever produced (FR-007,
  FR-014).
- MUST NOT alter, recompute, or reinterpret any composed value — every field is stored and
  presented exactly as supplied (FR-002, FR-003, FR-004, FR-005, FR-013).
- MUST NOT perform, request, or infer any financial calculation — `dcf_result`'s figures are
  the sole source of every valuation figure in the report (FR-003, FR-010).

## `render_report_document` contract

```python
def render_report_document(report: CommitteeReport) -> str: ...
```

- MUST be a pure function: no I/O, no randomness, no dependency on wall-clock time.
- MUST produce byte-identical output when called twice with an equal `CommitteeReport`
  (FR-009).
- MUST include exactly `report`'s own structured content — the investment thesis, its
  supporting evidence, the DCF valuation, key assumptions, key risks, invalidation
  conditions, the committee assessment, the recommendation, and dissent — no additional
  invented narrative (FR-008).
- MUST explicitly indicate when `report.decision.dissent` is empty (e.g., "No dissent
  recorded.") rather than silently omitting the topic (FR-006).
- Every valuation figure it displays MUST match `report.dcf_result`'s own values exactly
  (FR-008, US3/AC1).

## Non-goals of this contract

- No CLI entry point is defined by this feature.
- No network-facing API is defined by this feature.
- No persistence, repository, or file-write is exported by `aic.report`.
- No LLM provider, prompt, or LangGraph node is exported — this feature calls no LLM.
- No new financial calculation or valuation type is exported.
