# Phase 1 Data Model: End-to-End Investment Committee Workflow & MVP Completion

Two new Pydantic models (`WorkflowInput`, `WorkflowResult`) and two additive, optional
fields on the existing `CommitteeReport` (005). No other existing model changes. Every
other type referenced here (`InvestmentCase`, `AnalysisAssessment`, `CommitteeDecision`,
`DCFAssumptions`, `DCFResult`, `ValuationResult`, `ResearchContext`, `BullBearContext`,
`CommitteeAdjudicationContext`) is reused completely unchanged from 002/003/004/006/007.

## WorkflowInput

| Field | Type | Required | Notes |
|---|---|---|---|
| `company` | `Company` (aic.domain) | Yes | |
| `financial_snapshots` | `list[FinancialSnapshot]` (aic.domain) | Yes, `min_length=1` | Mirrors `InvestmentCase`'s own constraint (002) |
| `evidence` | `list[Evidence]` (aic.domain) | Yes (may be empty) | Passed through to the initial `InvestmentCase`; every downstream evidence reference is checked against exactly this list |
| `dcf_assumptions` | `DCFAssumptions` (aic.dcf) | Yes | Already self-validating (003) — invalid assumptions (e.g., WACC not exceeding terminal growth) are rejected by `DCFAssumptions`'s own constructor, before a `WorkflowInput` can even be built |

No validators beyond the fields being required — `WorkflowInput` is a pure input bundle, not
a cross-validated aggregate (spec Edge Cases; spec Assumptions; consistent with every prior
feature's own context-object precedent).

## WorkflowResult

| Field | Type | Notes |
|---|---|---|
| `dcf_result` | `DCFResult` (aic.dcf) | The single DCF computation, reused as read-only context by every later stage (FR-002, FR-009) |
| `valuation_result` | `ValuationResult` (aic.domain) | Derived once from `dcf_result` via the existing `to_valuation_result` conversion (research.md); its `valuation_id` is what `CommitteeDecision.valuation_reference` is set to (FR-010) |
| `thesis` | `InvestmentThesis` (aic.domain) | The generated thesis — the placeholder used internally before research ran is never exposed here (research.md) |
| `bull_assessment` | `AnalysisAssessment` (aic.domain) | |
| `bear_assessment` | `AnalysisAssessment` (aic.domain) | |
| `decision` | `CommitteeDecision` (aic.domain) | With `valuation_reference` set to `valuation_result.valuation_id` (FR-010) |
| `report` | `CommitteeReport` (aic.report) | With both `bull_assessment` and `bear_assessment` populated (data-model.md "CommitteeReport additions" below) |
| `document` | `str` | The rendered document from `render_report_document(report)` |

Every field is populated only on a fully successful run — `run_investment_workflow` either
returns a complete `WorkflowResult` or raises (FR-011); it never returns a partially-filled
result.

## CommitteeReport additions (005, additive and backward-compatible)

| Field | Type | Required | Notes |
|---|---|---|---|
| `bull_assessment` | `AnalysisAssessment \| None` | No, default `None` | New. When present alongside `bear_assessment`, `render_report_document` shows both as distinct sections |
| `bear_assessment` | `AnalysisAssessment \| None` | No, default `None` | New. Same as above |

`CommitteeReport.assessment` (existing, required, unchanged) continues to work exactly as
005 shipped it for every caller that does not set the two new fields — this workflow is the
first caller that sets all three (`assessment` populated with the Bull assessment, plus
both new fields populated with the full pair; research.md).

## Computation / control flow (`run_investment_workflow`, not a stored field)

```text
run_investment_workflow(input: WorkflowInput, provider: LLMProvider) -> WorkflowResult:
    dcf_result = compute_dcf(input.dcf_assumptions)                    # FR-002; may raise

    placeholder_thesis = InvestmentThesis(summary="Pending research")   # research.md
    initial_case = InvestmentCase(
        case_id=uuid4(), company=input.company,
        financial_snapshots=input.financial_snapshots,
        thesis=placeholder_thesis, evidence=input.evidence,
    )

    research_context = ResearchContext(investment_case=initial_case, dcf_result=dcf_result)
    thesis = generate_thesis(research_context, provider)                # FR-003; may raise

    case = initial_case.model_copy(update={"thesis": thesis})           # research.md

    latest_snapshot_date = max(s.as_of for s in input.financial_snapshots)
    valuation_result = to_valuation_result(
        dcf_result, valuation_id=uuid4(), valuation_date=latest_snapshot_date,
        confidence=1.0,
    )                                                                     # FR-004

    bullbear_context = BullBearContext(investment_case=case, valuation_result=valuation_result)
    bull_assessment = generate_bull_assessment(bullbear_context, provider)  # FR-005; may raise
    bear_assessment = generate_bear_assessment(bullbear_context, provider)  # FR-005; may raise

    adjudication_context = CommitteeAdjudicationContext(
        investment_case=case, dcf_result=dcf_result,
        bull_assessment=bull_assessment, bear_assessment=bear_assessment,
    )
    decision = generate_decision(adjudication_context, provider)          # FR-006; may raise
    decision = decision.model_copy(
        update={"valuation_reference": valuation_result.valuation_id}
    )                                                                      # FR-010

    report = CommitteeReport(
        company=input.company, financial_snapshots=input.financial_snapshots,
        thesis=thesis, dcf_result=dcf_result,
        assessment=bull_assessment,                                        # research.md
        bull_assessment=bull_assessment, bear_assessment=bear_assessment,
        decision=decision,
    )                                                                        # FR-007
    document = render_report_document(report)

    return WorkflowResult(
        dcf_result=dcf_result, valuation_result=valuation_result, thesis=thesis,
        bull_assessment=bull_assessment, bear_assessment=bear_assessment,
        decision=decision, report=report, document=document,
    )
```

No step catches an exception from an earlier step — every stage's own error propagates
unchanged (research.md "Each stage's own exception propagates unchanged").

## Relationship to existing entities

```text
WorkflowInput ──▶ compute_dcf (003) ──▶ DCFResult ──┬──▶ ResearchContext (004) ──▶ generate_thesis ──▶ InvestmentThesis
                                                      │                                                      │
                                                      ├──▶ to_valuation_result (003) ──▶ ValuationResult      │
                                                      │                                        │              │
                                                      │                                        ▼              ▼
                                                      │                              BullBearContext (007, updated case)
                                                      │                                        │
                                                      │                          generate_bull/bear_assessment
                                                      │                                        │
                                                      ▼                                        ▼
                                        CommitteeAdjudicationContext (006) ◀───────────────────┘
                                                      │
                                            generate_decision ──▶ CommitteeDecision (valuation_reference set)
                                                      │
                                        CommitteeReport (005, bull_assessment + bear_assessment set)
                                                      │
                                        render_report_document ──▶ document (str)
```
