# Quickstart: Validate Investment Committee Report

Validates the three user stories from `spec.md` end-to-end. Run from the repository root in
Windows PowerShell, using the `uv`-managed environment. This feature makes no network call
and needs no credentials — it is pure composition and deterministic rendering.

## Prerequisites

```powershell
uv sync
```

## User Story 1 — Assemble a complete, structured report

```powershell
uv run python -c "
from datetime import date, UTC, datetime
from decimal import Decimal
from uuid import uuid4
from aic.domain import (
    Company, Evidence, EvidenceType, FinancialSnapshot, InvestmentThesis,
    AnalysisAssessment, CommitteeDecision, Recommendation, Money,
)
from aic.dcf import DCFAssumptions, ForecastYear, compute_dcf
from aic.report import CommitteeReport, render_report_document

evidence = Evidence(evidence_id=uuid4(), source='10-K', title='FY2025 Annual Report', excerpt='Revenue grew 12%% YoY', retrieved_date=date(2026,1,5), evidence_type=EvidenceType.FACT)
company = Company(company_id=uuid4(), ticker='ASML', name='ASML Holding', exchange='AEX', country='NL', sector='Technology', industry='Semiconductor Equipment')
snapshot = FinancialSnapshot(as_of=date(2026,3,31), revenue=Money(amount=Decimal('6500000000'), currency='EUR'))
thesis = InvestmentThesis(summary='Durable moat in EUV lithography.', supporting_evidence=[evidence], key_assumptions=['EUV demand persists'], key_risks=['Export restrictions'], invalidation_conditions=['Major customer cancels multi-year order'])

forecast = [ForecastYear(revenue=Money(amount=Decimal('1000'), currency='EUR'), depreciation_and_amortization=Money(amount=Decimal('0'), currency='EUR'), capital_expenditure=Money(amount=Decimal('0'), currency='EUR'), change_in_net_working_capital=Money(amount=Decimal('0'), currency='EUR'))]
assumptions = DCFAssumptions(forecast=forecast, operating_margin=Decimal('0.5'), tax_rate=Decimal('0'), wacc=Decimal('0.10'), terminal_growth_rate=Decimal('0'), cash=Money(amount=Decimal('0'), currency='EUR'), debt=Money(amount=Decimal('0'), currency='EUR'), shares_outstanding=Decimal('10'))
dcf_result = compute_dcf(assumptions)

assessment = AnalysisAssessment(assessment_id=uuid4(), conclusion='Thesis is well-supported.', confidence=0.8, arguments=['Structural demand for EUV'], supporting_evidence=[evidence.evidence_id], assumptions=['EUV demand persists'], risks=['Export restrictions'])
decision = CommitteeDecision(decision_id=uuid4(), recommendation=Recommendation.WATCH, rationale='Attractive but priced for perfection.', referenced_evidence=[evidence.evidence_id], referenced_thesis=thesis)

report = CommitteeReport(company=company, financial_snapshots=[snapshot], thesis=thesis, dcf_result=dcf_result, assessment=assessment, decision=decision)
print(report.company.ticker, report.decision.recommendation, len(report.thesis.supporting_evidence))
"
```

**Expected outcome**: prints `ASML WATCH 1` — confirms a complete report
assembles from already-validated inputs with zero recalculation, satisfying User Story 1 and
SC-001/SC-002.

## User Story 1 — Missing required input fails explicitly

```powershell
uv run python -c "
from aic.report import CommitteeReport
try:
    CommitteeReport()
except Exception as exc:
    print(type(exc).__name__)
"
```

**Expected outcome**: prints `ValidationError` — confirms FR-007/FR-014/SC-005: a report
missing required inputs fails explicitly rather than partially assembling.

## User Story 2 — Deterministic document rendering

```powershell
uv run pytest tests/unit/report/test_report_document.py -v
```

**Expected outcome**: all tests pass, including a test asserting two renders of the same
`CommitteeReport` are byte-identical (SC-003), and a test asserting an empty
`decision.dissent` renders an explicit "No dissent recorded." line rather than omitting the
section (SC-004).

## User Story 3 — No new valuation logic

```powershell
uv run pytest tests/unit/report -v
```

**Expected outcome**: the entire `report` test suite passes, including tests confirming
every valuation figure the rendered document displays matches `dcf_result`'s own values
exactly, and that `CommitteeReport`/`render_report_document` never alter the supplied
`CommitteeDecision.recommendation` (SC-006).

## Full validation in one pass

```powershell
uv run pytest tests/unit/report -v
uv run ruff check .
uv run mypy src
```

All three commands exiting with code `0` on a clean checkout is the complete acceptance
signal for this feature (SC-001–SC-005 verified by the test suite; SC-006–SC-007 verified by
inspection — no new financial calculation and no persistence/API/UI/scheduling — rather than
by a single command).
