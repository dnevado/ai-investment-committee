# Quickstart: Validate Investment Committee Decision Engine

Validates the three user stories from `spec.md` end-to-end. Run from the repository root in
Windows PowerShell, using the `uv`-managed environment. All scenarios use a fake
`LLMProvider` (the same protocol 004 defined) — none of this requires a real OpenAI API key
or network access, matching FR-003/SC-003.

## Prerequisites

```powershell
uv sync
```

## User Story 1 — Adjudicate bull/bear cases into a decision (fake provider)

```powershell
uv run python -c "
from datetime import date
from decimal import Decimal
from uuid import uuid4
from aic.domain import Company, Evidence, EvidenceType, FinancialSnapshot, InvestmentCase, InvestmentThesis, AnalysisAssessment, Recommendation, Money
from aic.dcf import DCFAssumptions, ForecastYear, compute_dcf
from aic.research import LLMCompletion
from aic.committee import CommitteeAdjudicationContext, generate_decision

evidence = Evidence(evidence_id=uuid4(), source='10-K', title='FY2025 Annual Report', excerpt='Revenue grew 12%% YoY', retrieved_date=date(2026,1,5), evidence_type=EvidenceType.FACT)
company = Company(company_id=uuid4(), ticker='ASML', name='ASML Holding', exchange='AEX', country='NL', sector='Technology', industry='Semiconductor Equipment')
snapshot = FinancialSnapshot(as_of=date(2026,3,31), revenue=Money(amount=Decimal('6500000000'), currency='EUR'))
thesis = InvestmentThesis(summary='Durable moat in EUV lithography.', supporting_evidence=[evidence])
case = InvestmentCase(case_id=uuid4(), company=company, financial_snapshots=[snapshot], thesis=thesis, evidence=[evidence])

forecast = [ForecastYear(revenue=Money(amount=Decimal('1000'), currency='EUR'), depreciation_and_amortization=Money(amount=Decimal('0'), currency='EUR'), capital_expenditure=Money(amount=Decimal('0'), currency='EUR'), change_in_net_working_capital=Money(amount=Decimal('0'), currency='EUR'))]
assumptions = DCFAssumptions(forecast=forecast, operating_margin=Decimal('0.5'), tax_rate=Decimal('0'), wacc=Decimal('0.10'), terminal_growth_rate=Decimal('0'), cash=Money(amount=Decimal('0'), currency='EUR'), debt=Money(amount=Decimal('0'), currency='EUR'), shares_outstanding=Decimal('10'))
dcf_result = compute_dcf(assumptions)

bull = AnalysisAssessment(assessment_id=uuid4(), conclusion='Structural EUV demand supports a premium multiple.', confidence=0.75, supporting_evidence=[evidence.evidence_id])
bear = AnalysisAssessment(assessment_id=uuid4(), conclusion='Export restrictions could impair growth.', confidence=0.4, supporting_evidence=[evidence.evidence_id])

context = CommitteeAdjudicationContext(investment_case=case, dcf_result=dcf_result, bull_assessment=bull, bear_assessment=bear)

class QuickstartFakeProvider:
    def complete_structured(self, *, system_prompt, user_prompt, schema):
        return LLMCompletion(
            content={
                'central_thesis': 'ASML holds a durable moat in EUV lithography.',
                'key_disagreements': ['Bull weighs demand durability higher than Bear weighs export risk.'],
                'valuation_summary': 'DCF implies upside versus current levels.',
                'downside_risks': ['Export restrictions'],
                'invalidation_conditions': ['Major customer cancels multi-year order'],
                'recommendation': 'WATCH',
                'confidence': 0.6,
                'dissent': ['Bear case underweights structural demand.'],
                'supporting_evidence_ids': [str(evidence.evidence_id)],
            },
            prompt_tokens=140, completion_tokens=95, latency_ms=55.0,
        )

decision = generate_decision(context, QuickstartFakeProvider())
print(decision.recommendation, len(decision.referenced_evidence), len(decision.dissent))
"
```

**Expected outcome**: prints `WATCH 1 1` — confirms the full flow (context assembly,
fake-provider call, `CommitteeDecisionDraft` validation, evidence-ID resolution, and
deterministic rationale composition) works end-to-end with zero network access, satisfying
User Story 1 and SC-001.

## User Story 2 — Dissent present vs. absent

```powershell
uv run pytest tests/unit/committee/test_committee_generator.py -v
```

**Expected outcome**: all tests pass, including a test asserting a decision built from
disagreeing bull/bear assessments carries non-empty `dissent`, and a test asserting a
decision built from materially aligned assessments carries empty `dissent` (SC-004).

## User Story 3 — Zero real OpenAI calls

```powershell
uv run pytest tests/unit/committee -v
```

**Expected outcome**: the entire `committee` test suite (context, prompt, and generator
tests) passes with zero network access — confirmed by running with no
`OPENAI_API_KEY`/`AIC_OPENAI_API_KEY` set in the environment and no network available;
nothing in this test run requires either (SC-003). `OpenAIProvider` itself is not
re-tested here — it is already covered by 004's `tests/unit/research/test_openai_provider.py`.

## Full validation in one pass

```powershell
uv run pytest tests/unit/committee -v
uv run ruff check .
uv run mypy src
```

All three commands exiting with code `0` on a clean checkout, with no OpenAI credentials
configured, is the complete acceptance signal for this feature (SC-001–SC-004 verified by
the test suite; SC-005–SC-007 verified by inspection — no financial computation, recommendation
restricted to the existing enum, and explicit provider-error propagation — rather than by a
single command).
