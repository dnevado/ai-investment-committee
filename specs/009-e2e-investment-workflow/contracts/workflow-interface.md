# Contract: `aic.workflow` Package Public Interface (and the `aic.report` Additions)

This feature's "interface" is the Python import surface `aic.workflow` exposes, plus two new
optional fields on the existing `aic.report.CommitteeReport`. There is no network API, CLI,
or UI in scope.

## Import contract

```python
from aic.workflow import (
    WorkflowInput,
    WorkflowResult,
    run_investment_workflow,
)
```

- Every name above MUST be importable directly from `aic.workflow`.
- Importing `aic.workflow` MUST succeed with no network access and no LLM provider
  credentials required — construction of a real provider may require credentials, but
  merely importing `aic.workflow` MUST NOT.

## `run_investment_workflow` contract

```python
def run_investment_workflow(input: WorkflowInput, provider: LLMProvider) -> WorkflowResult: ...
```

- `provider` MUST accept any conforming `aic.research.provider.LLMProvider` implementation
  (including `aic.research.OpenAIProvider` and a test's fake) — this feature MUST NOT define
  or require a second, incompatible provider protocol (FR-013).
- MUST call `compute_dcf` (003) before any stage that requires its result (FR-002).
- MUST call `generate_thesis` (004), `generate_bull_assessment` and
  `generate_bear_assessment` (007), and `generate_decision` (006) using the single supplied
  `provider` instance — MUST NOT construct or require a second provider instance (FR-013).
- MUST NOT catch, wrap, or suppress any exception raised by any stage it calls — a failure
  at any stage MUST propagate to the caller unmodified, and MUST NOT result in a returned
  `WorkflowResult` (FR-011; research.md).
- MUST set the returned `CommitteeDecision.valuation_reference` to the `valuation_id` of the
  `ValuationResult` derived from the same `DCFResult` used throughout the rest of the run
  (FR-010).
- MUST construct the returned `CommitteeReport` with both `bull_assessment` and
  `bear_assessment` populated with the two independently-generated assessments (FR-007; see
  `CommitteeReport` contract addition below).
- MUST NOT perform, request, or infer any financial calculation of its own — every
  valuation figure in the result traces to the single `compute_dcf` call (FR-009, FR-012).

## `CommitteeReport` contract addition (005)

```python
class CommitteeReport(BaseModel):
    # ... existing fields unchanged: company, financial_snapshots, thesis, dcf_result,
    #     assessment, decision ...
    bull_assessment: AnalysisAssessment | None = None    # new, additive
    bear_assessment: AnalysisAssessment | None = None    # new, additive
```

- Both new fields MUST default to `None` — every existing caller/test that does not set
  them MUST continue to construct and behave exactly as before (FR-016).
- `render_report_document` MUST render two distinct, labeled sections (one per assessment)
  when both new fields are non-`None`, and MUST render its pre-existing single "Committee
  Assessment" section (from `assessment`) unchanged when either or both are `None`.

## Non-goals of this contract

- No CLI entry point is defined by this feature.
- No network-facing API is defined by this feature.
- No LangGraph node, graph, or multi-agent orchestration symbol is exported (research.md).
- No new `LLMProvider`/`LLMCompletion`/`OpenAIProvider` definition — reused from
  `aic.research` unchanged.
- No new financial calculation, valuation type, or DCF logic — reused from `aic.dcf`
  unchanged.
- `CommitteeReport.assessment`'s existing required-field contract is unchanged — no
  existing caller is required to change how it constructs a `CommitteeReport`.
