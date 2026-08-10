# Quickstart: Validate the Investment Committee Domain Model

Validates the three user stories from `spec.md` end-to-end. Run from the repository
root in Windows PowerShell, using the `uv`-managed environment established in
001-repository-bootstrap.

## Prerequisites

```powershell
uv sync
```

## User Story 1 — Company and FinancialSnapshot without ambiguity

```powershell
uv run python -c "
from decimal import Decimal
from datetime import date
from uuid import uuid4
from aic.domain import Company, FinancialSnapshot, Money

c = Company(company_id=uuid4(), ticker='ASML', name='ASML Holding', exchange='AEX', country='NL', sector='Technology', industry='Semiconductor Equipment')
fs = FinancialSnapshot(as_of=date(2026, 3, 31), revenue=Money(amount=Decimal('6500000000'), currency='EUR'))
print(c.model_dump())
print(fs.model_dump())
print(Company.model_validate(c.model_dump()) == c)
print(FinancialSnapshot.model_validate(fs.model_dump()) == fs)
"
```

**Expected outcome**: both objects print their typed fields, the round-trip equality
checks print `True`, and `fs.free_cash_flow` is `None` (not `0`) — satisfies SC-001,
SC-003, SC-004.

```powershell
uv run python -c "
from aic.domain import Money
from decimal import Decimal
Money(amount=Decimal('1'), currency='NOTREAL')
"
```

**Expected outcome**: raises `pydantic.ValidationError` — the currency is not a real
ISO 4217 code — satisfies SC-002.

## User Story 2 — Evidence, InvestmentThesis, InvestmentCase

```powershell
uv run python -c "
from datetime import date
from uuid import uuid4
from decimal import Decimal
from aic.domain import Evidence, EvidenceType, InvestmentThesis, InvestmentCase, Company, FinancialSnapshot, Money

ev = Evidence(evidence_id=uuid4(), source='10-K', title='FY2025 Annual Report', retrieved_date=date(2026, 1, 5), excerpt='Revenue grew 12% YoY', evidence_type=EvidenceType.FACT)
thesis = InvestmentThesis(summary='Durable moat in EUV lithography', supporting_evidence=[ev], key_assumptions=['EUV demand persists'], key_risks=['Export restrictions'], invalidation_conditions=['Major customer cancels multi-year order'])
company = Company(company_id=uuid4(), ticker='ASML', name='ASML Holding', exchange='AEX', country='NL', sector='Technology', industry='Semiconductor Equipment')
snap = FinancialSnapshot(as_of=date(2026, 3, 31), revenue=Money(amount=Decimal('6500000000'), currency='EUR'))
case = InvestmentCase(case_id=uuid4(), company=company, financial_snapshots=[snap], thesis=thesis, evidence=[ev])
print(case.case_id, case.analysis_timestamp)
print(InvestmentCase.model_validate(case.model_dump()) == case)
"
```

**Expected outcome**: prints a UUID and timestamp, and the round-trip equality check
prints `True` — satisfies User Story 2's acceptance scenarios and SC-004.

## User Story 3 — AnalysisAssessment, ValuationResult, CommitteeDecision

```powershell
uv run python -c "
from datetime import date
from decimal import Decimal
from uuid import uuid4
from aic.domain import AnalysisAssessment, ValuationResult, CommitteeDecision, Recommendation, Money

assessment = AnalysisAssessment(assessment_id=uuid4(), conclusion='Strong upside on lithography demand', arguments=['Backlog at record highs'], supporting_evidence=[], assumptions=['No major export restriction change'], risks=['China demand softening'], confidence=0.7)
valuation = ValuationResult(valuation_id=uuid4(), method='comparable-multiples (placeholder)', valuation_date=date(2026, 8, 10), estimated_value=Money(amount=Decimal('850.00'), currency='EUR'), assumption_evidence_refs=[], confidence=0.6)
decision = CommitteeDecision(decision_id=uuid4(), recommendation=Recommendation.WATCH, rationale='Valuation stretched relative to near-term catalysts', referenced_evidence=[], dissent=[])
print('Bull' in str(type(assessment)), 'Bear' in str(type(assessment)))
print(decision.valuation_reference)
"
```

**Expected outcome**: the `'Bull'`/`'Bear'` membership check prints `False False` (the
type name carries no role label), `decision.valuation_reference` prints `None` (a
decision can exist before a valuation does) — satisfies User Story 3's acceptance
scenarios.

## Full validation in one pass

```powershell
uv run pytest tests/unit/domain -v
uv run ruff check .
uv run mypy src
```

All three commands exiting with code `0` on a clean checkout is the complete acceptance
signal for this feature (spec Success Criteria SC-001–SC-005; SC-006/SC-007 are verified
by inspection — no network/env/LLM/orchestration/cloud dependency and no calculation or
agent code present — rather than by a single command).
