# Quickstart: Validate the Deterministic DCF Valuation Engine

Validates the three user stories from `spec.md` end-to-end. Run from the repository
root in Windows PowerShell, using the `uv`-managed environment.

## Prerequisites

```powershell
uv sync
```

## User Story 1 — Compute Enterprise Value, Equity Value, Implied Value Per Share

Uses the spec's Reference Case (all values USD):

```powershell
uv run python -c "
from decimal import Decimal
from aic.dcf import ForecastYear, DCFAssumptions, compute_dcf
from aic.domain import Money

def money(amount):
    return Money(amount=Decimal(amount), currency='USD')

forecast = [
    ForecastYear(revenue=money('1000.00'), depreciation_and_amortization=money('50.00'), capital_expenditure=money('60.00'), change_in_net_working_capital=money('10.00')),
    ForecastYear(revenue=money('1100.00'), depreciation_and_amortization=money('50.00'), capital_expenditure=money('60.00'), change_in_net_working_capital=money('10.00')),
    ForecastYear(revenue=money('1210.00'), depreciation_and_amortization=money('50.00'), capital_expenditure=money('60.00'), change_in_net_working_capital=money('10.00')),
]
assumptions = DCFAssumptions(
    forecast=forecast,
    operating_margin=Decimal('0.20'),
    tax_rate=Decimal('0.25'),
    wacc=Decimal('0.10'),
    terminal_growth_rate=Decimal('0.02'),
    cash=money('200.00'),
    debt=money('150.00'),
    shares_outstanding=Decimal('100'),
)
result = compute_dcf(assumptions)
print(result.enterprise_value.amount, result.equity_value.amount, result.implied_value_per_share.amount)
print(compute_dcf(assumptions) == result)
"
```

**Expected outcome**: prints `1906.40 1956.40 19.56` (matching spec.md's Reference Case
exactly) and `True` (determinism) — satisfies SC-001, SC-005.

## User Story 2 — Reject Invalid or Incoherent Assumptions

```powershell
uv run python -c "
from decimal import Decimal
from aic.dcf import ForecastYear, DCFAssumptions
from aic.domain import Money

money = Money(amount=Decimal('100'), currency='USD')
try:
    DCFAssumptions(
        forecast=[ForecastYear(revenue=money, depreciation_and_amortization=money, capital_expenditure=money, change_in_net_working_capital=money)],
        operating_margin=Decimal('0.20'), tax_rate=Decimal('0.25'),
        wacc=Decimal('0.05'), terminal_growth_rate=Decimal('0.05'),  # WACC == terminal growth
        cash=money, debt=money, shares_outstanding=Decimal('100'),
    )
    print('FAIL: should have raised')
except Exception as e:
    print('rejected:', type(e).__name__)
"
```

**Expected outcome**: prints `rejected: ValidationError` — satisfies SC-002.

## User Story 3 — Verify Against the Canonical Reference Case

Covered by User Story 1's script above (same inputs, same expected outputs). In the
test suite, this is `tests/unit/dcf/test_engine.py::test_reference_case`, which asserts
every field of `DCFResult` (not just the three headline values) against spec.md's
documented Reference Case table.

## Full validation in one pass

```powershell
uv run pytest tests/unit/dcf -v
uv run ruff check .
uv run mypy src
```

All three commands exiting with code `0` on a clean checkout is the complete acceptance
signal for this feature (SC-001–SC-005 verified by the test suite; SC-006/SC-007 are
verified by inspection — no NaN/Infinity ever produced, and no network/file I/O anywhere
in `aic.dcf` — rather than by a single command).
