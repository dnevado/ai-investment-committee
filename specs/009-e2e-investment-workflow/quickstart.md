# Quickstart: Validate the End-to-End Investment Committee Workflow

Validates the three user stories from `spec.md` end-to-end. Run from the repository root in
Windows PowerShell, using the `uv`-managed environment. All scenarios use a fake
`LLMProvider` (the same protocol 004/006/007 defined) — none of this requires a real OpenAI
API key or network access, matching FR-015/SC-003.

## Prerequisites

```powershell
uv sync
```

## User Story 1 — Run the complete workflow end-to-end (fake provider)

```powershell
uv run python -c "
from datetime import date
from decimal import Decimal
from uuid import uuid4
from aic.domain import Company, Evidence, EvidenceType, FinancialSnapshot, Money
from aic.dcf import DCFAssumptions, ForecastYear
from aic.research import LLMCompletion, ThesisDraft
from aic.bullbear import AssessmentDraft
from aic.workflow import WorkflowInput, run_investment_workflow

evidence = Evidence(evidence_id=uuid4(), source='10-K', title='FY2025 Annual Report', excerpt='Revenue grew 12%% YoY', retrieved_date=date(2026,1,5), evidence_type=EvidenceType.FACT)
company = Company(company_id=uuid4(), ticker='ASML', name='ASML Holding', exchange='AEX', country='NL', sector='Technology', industry='Semiconductor Equipment')
snapshot = FinancialSnapshot(as_of=date(2026,3,31), revenue=Money(amount=Decimal('6500000000'), currency='EUR'))

forecast = [ForecastYear(revenue=Money(amount=Decimal('1000'), currency='EUR'), depreciation_and_amortization=Money(amount=Decimal('0'), currency='EUR'), capital_expenditure=Money(amount=Decimal('0'), currency='EUR'), change_in_net_working_capital=Money(amount=Decimal('0'), currency='EUR'))]
assumptions = DCFAssumptions(forecast=forecast, operating_margin=Decimal('0.5'), tax_rate=Decimal('0'), wacc=Decimal('0.10'), terminal_growth_rate=Decimal('0'), cash=Money(amount=Decimal('0'), currency='EUR'), debt=Money(amount=Decimal('0'), currency='EUR'), shares_outstanding=Decimal('10'))

workflow_input = WorkflowInput(company=company, financial_snapshots=[snapshot], evidence=[evidence], dcf_assumptions=assumptions)

class QuickstartFakeProvider:
    def complete_structured(self, *, system_prompt, user_prompt, schema):
        if schema is ThesisDraft:
            content = {'summary': 'Durable moat in EUV lithography.', 'supporting_evidence_ids': [str(evidence.evidence_id)], 'key_assumptions': ['EUV demand persists'], 'key_risks': ['Export restrictions'], 'invalidation_conditions': ['Major customer cancels multi-year order']}
        elif schema is AssessmentDraft and 'Bull' in system_prompt:
            content = {'conclusion': 'Outperform on structural EUV demand.', 'confidence': 0.75, 'arguments': ['Monopoly in EUV lithography'], 'assumptions': ['EUV demand persists'], 'risks': ['Execution risk'], 'supporting_evidence_ids': [str(evidence.evidence_id)]}
        elif schema is AssessmentDraft:
            content = {'conclusion': 'Export restrictions could impair growth.', 'confidence': 0.4, 'arguments': ['Export controls tightening'], 'assumptions': ['China demand normalizes'], 'risks': ['Order cancellation'], 'supporting_evidence_ids': [str(evidence.evidence_id)]}
        else:
            content = {'central_thesis': 'Durable moat, priced for perfection.', 'key_disagreements': ['Bull weighs demand higher than Bear weighs export risk.'], 'valuation_summary': 'DCF implies fair value near current levels.', 'downside_risks': ['Export restrictions'], 'invalidation_conditions': ['Major customer cancels multi-year order'], 'recommendation': 'WATCH', 'confidence': 0.6, 'dissent': [], 'supporting_evidence_ids': [str(evidence.evidence_id)]}
        return LLMCompletion(content=content, prompt_tokens=100, completion_tokens=60, latency_ms=30.0)

result = run_investment_workflow(workflow_input, QuickstartFakeProvider())
print(result.decision.recommendation, result.decision.valuation_reference == result.valuation_result.valuation_id)
print(result.report.bull_assessment is not None, result.report.bear_assessment is not None)
print(str(result.dcf_result.implied_value_per_share.amount) in result.document)
"
```

**Expected outcome**: prints `WATCH True`, then `True True`, then `True` — confirms the
complete pipeline (DCF → research → Bull/Bear → committee → report) runs end-to-end with
zero manual wiring, the committee decision's valuation reference matches the derived
valuation, both assessments are represented in the report, and the rendered document
contains the single DCF computation's own figures (User Story 1; SC-001, SC-005).

## User Story 2 — A mid-pipeline failure halts the whole workflow

```powershell
uv run pytest tests/unit/workflow/test_workflow_orchestrator.py -v -k failure
```

**Expected outcome**: every per-stage-failure test passes, confirming that a provider error
or invalid response at any stage (research, Bull, Bear, or committee) halts the workflow
immediately with no report ever produced (SC-002).

## User Story 3 — Zero real network calls, and no regression to any existing test

```powershell
uv run pytest tests/unit/workflow -v
uv run pytest -q
```

**Expected outcome**: the entire `workflow` test suite passes with zero network access
(SC-003), and the full pre-existing test suite (every test from 002 through 008) still
passes unmodified (SC-004).

## Full validation in one pass

```powershell
uv run pytest -q
uv run ruff check .
uv run mypy src
```

All three commands exiting with code `0` on a clean checkout, with no LLM provider
credentials configured, is the complete acceptance signal for this feature (SC-001–SC-005
verified by the test suite; SC-006 verified by inspection — no new financial calculation,
valuation methodology, or provider abstraction — rather than by a single command).
