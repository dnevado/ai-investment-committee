# Quickstart: Validate Bull/Bear Analysis Generation

Validates the three user stories from `spec.md` end-to-end. Run from the repository root in
Windows PowerShell, using the `uv`-managed environment. All scenarios use a fake
`LLMProvider` (the same protocol 004 defined) — none of this requires a real OpenAI API key
or network access, matching FR-005/SC-003.

## Prerequisites

```powershell
uv sync
```

## User Story 1 & 2 — Generate Bull and Bear cases independently (fake provider)

```powershell
uv run python -c "
from datetime import date
from decimal import Decimal
from uuid import uuid4
from aic.domain import Company, Evidence, EvidenceType, FinancialSnapshot, InvestmentCase, InvestmentThesis, ValuationResult, Money
from aic.research import LLMCompletion
from aic.bullbear import BullBearContext, generate_bull_assessment, generate_bear_assessment

evidence = Evidence(evidence_id=uuid4(), source='10-K', title='FY2025 Annual Report', excerpt='Revenue grew 12%% YoY', retrieved_date=date(2026,1,5), evidence_type=EvidenceType.FACT)
company = Company(company_id=uuid4(), ticker='ASML', name='ASML Holding', exchange='AEX', country='NL', sector='Technology', industry='Semiconductor Equipment')
snapshot = FinancialSnapshot(as_of=date(2026,3,31), revenue=Money(amount=Decimal('6500000000'), currency='EUR'))
thesis = InvestmentThesis(summary='Durable moat in EUV lithography.', supporting_evidence=[evidence])
case = InvestmentCase(case_id=uuid4(), company=company, financial_snapshots=[snapshot], thesis=thesis, evidence=[evidence])

valuation = ValuationResult(valuation_id=uuid4(), method='DCF (FCFF)', valuation_date=date(2026,3,31), estimated_value=Money(amount=Decimal('850.00'), currency='EUR'), confidence=0.7)

context = BullBearContext(investment_case=case, valuation_result=valuation)

call_log = []

class QuickstartFakeProvider:
    def __init__(self, role):
        self.role = role
    def complete_structured(self, *, system_prompt, user_prompt, schema):
        call_log.append((self.role, user_prompt))
        if self.role == 'bull':
            content = {
                'conclusion': 'ASML is positioned to outperform on structural EUV demand.',
                'confidence': 0.75,
                'arguments': ['Monopoly position in EUV lithography', 'Multi-year order backlog provides revenue visibility'],
                'assumptions': ['EUV demand persists'],
                'risks': ['Execution risk on capacity expansion'],
                'supporting_evidence_ids': [str(evidence.evidence_id)],
            }
        else:
            content = {
                'conclusion': 'Export restrictions could materially impair growth.',
                'confidence': 0.4,
                'arguments': ['Geopolitical export controls are tightening'],
                'assumptions': ['China demand normalizes'],
                'risks': ['Loss of a major customer', 'Multi-year order cancellation'],
                'supporting_evidence_ids': [str(evidence.evidence_id)],
            }
        return LLMCompletion(content=content, prompt_tokens=120, completion_tokens=80, latency_ms=40.0)

bull = generate_bull_assessment(context, QuickstartFakeProvider('bull'))
bear = generate_bear_assessment(context, QuickstartFakeProvider('bear'))

bull_prompt = next(p for r, p in call_log if r == 'bull')
bear_prompt = next(p for r, p in call_log if r == 'bear')

print(bull.confidence, bear.confidence, len(bull.supporting_evidence), len(bear.supporting_evidence))
print('independent:', bull.conclusion not in bear_prompt and bear.conclusion not in bull_prompt)
"
```

**Expected outcome**: prints `0.75 0.4 1 1` then `independent: True` — confirms both roles
generate validated, evidence-traceable `AnalysisAssessment`s from independent calls, and
that neither call's prompt contains the other's conclusion (User Stories 1 & 2; SC-001,
SC-004).

## User Story 3 — Zero real OpenAI calls

```powershell
uv run pytest tests/unit/bullbear -v
```

**Expected outcome**: the entire `bullbear` test suite (context, prompt, and generator
tests, for both roles) passes with zero network access — confirmed by running with no
`OPENAI_API_KEY`/`AIC_OPENAI_API_KEY` set in the environment and no network available;
nothing in this test run requires either (SC-003). `OpenAIProvider` itself is not re-tested
here — it is already covered by 004's `tests/unit/research/test_openai_provider.py`.

## Full validation in one pass

```powershell
uv run pytest tests/unit/bullbear -v
uv run ruff check .
uv run mypy src
```

All three commands exiting with code `0` on a clean checkout, with no OpenAI credentials
configured, is the complete acceptance signal for this feature (SC-001–SC-004 verified by
the test suite; SC-005–SC-007 verified by inspection — no financial computation, no new
provider abstraction, and explicit provider-error propagation for either role — rather than
by a single command).
