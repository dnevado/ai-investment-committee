# Quickstart: Validate Investment Research & Thesis Generation

Validates the three user stories from `spec.md` end-to-end. Run from the repository
root in Windows PowerShell, using the `uv`-managed environment. All scenarios use a fake
`LLMProvider` — none of this requires a real OpenAI API key or network access, matching
FR-003/SC-003.

## Prerequisites

```powershell
uv sync
```

## User Story 1 — Generate an evidence-traceable thesis (fake provider)

```powershell
uv run python -c "
from datetime import date
from decimal import Decimal
from uuid import uuid4
from aic.domain import Company, Evidence, EvidenceType, FinancialSnapshot, InvestmentCase, InvestmentThesis
from aic.dcf import DCFAssumptions, ForecastYear, compute_dcf
from aic.domain import Money
from aic.research import ResearchContext, LLMCompletion, generate_thesis

evidence = Evidence(evidence_id=uuid4(), source='10-K', title='FY2025 Annual Report', excerpt='Revenue grew 12%% YoY', retrieved_date=date(2026,1,5), evidence_type=EvidenceType.FACT)
company = Company(company_id=uuid4(), ticker='ASML', name='ASML Holding', exchange='AEX', country='NL', sector='Technology', industry='Semiconductor Equipment')
snapshot = FinancialSnapshot(as_of=date(2026,3,31), revenue=Money(amount=Decimal('6500000000'), currency='EUR'))
case = InvestmentCase(case_id=uuid4(), company=company, financial_snapshots=[snapshot], thesis=InvestmentThesis(summary='placeholder'), evidence=[evidence])

forecast = [ForecastYear(revenue=Money(amount=Decimal('1000'), currency='EUR'), depreciation_and_amortization=Money(amount=Decimal('0'), currency='EUR'), capital_expenditure=Money(amount=Decimal('0'), currency='EUR'), change_in_net_working_capital=Money(amount=Decimal('0'), currency='EUR'))]
assumptions = DCFAssumptions(forecast=forecast, operating_margin=Decimal('0.5'), tax_rate=Decimal('0'), wacc=Decimal('0.10'), terminal_growth_rate=Decimal('0'), cash=Money(amount=Decimal('0'), currency='EUR'), debt=Money(amount=Decimal('0'), currency='EUR'), shares_outstanding=Decimal('10'))
dcf_result = compute_dcf(assumptions)

context = ResearchContext(investment_case=case, dcf_result=dcf_result)

class QuickstartFakeProvider:
    def complete_structured(self, *, system_prompt, user_prompt, schema):
        return LLMCompletion(
            content={
                'summary': 'Durable moat in EUV lithography.',
                'supporting_evidence_ids': [str(evidence.evidence_id)],
                'key_assumptions': ['EUV demand persists'],
                'key_risks': ['Export restrictions'],
                'invalidation_conditions': ['Major customer cancels multi-year order'],
            },
            prompt_tokens=120, completion_tokens=80, latency_ms=42.0,
        )

thesis = generate_thesis(context, QuickstartFakeProvider())
print(thesis.summary, len(thesis.supporting_evidence))
"
```

**Expected outcome**: prints `Durable moat in EUV lithography. 1` — confirms the full
flow (context assembly, fake-provider call, `ThesisDraft` validation, evidence-ID
resolution against the real `Evidence` object) works end-to-end with zero network access,
satisfying User Story 1 and SC-001.

## User Story 2 — Deterministic document rendering

```powershell
uv run pytest tests/unit/research/test_document.py -v
```

**Expected outcome**: all tests pass, including a test asserting two renders of the same
`InvestmentThesis` are byte-identical (SC-004).

## User Story 3 — Zero real OpenAI calls

```powershell
uv run pytest tests/unit/research -v
```

**Expected outcome**: the entire `research` test suite (generator, document, prompt,
context, and the mocked `OpenAIProvider` adapter tests) passes with zero network access —
confirmed by running with no `OPENAI_API_KEY`/`AIC_OPENAI_API_KEY` set in the environment
and no network available; nothing in this test run requires either (SC-003).

## Full validation in one pass

```powershell
uv run pytest tests/unit/research -v
uv run ruff check .
uv run mypy src
```

All three commands exiting with code `0` on a clean checkout, with no OpenAI credentials
configured, is the complete acceptance signal for this feature (SC-001–SC-004 verified by
the test suite; SC-005–SC-007 verified by inspection — no financial computation, no
recommendation/Bull-Bear content, and explicit provider-error propagation — rather than
by a single command).
