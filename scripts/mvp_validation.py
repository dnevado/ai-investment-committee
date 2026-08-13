import os
from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import uuid4

from aic.dcf import DCFAssumptions, ForecastYear, compute_dcf
from aic.domain import (
    Company,
    Evidence,
    EvidenceType,
    FinancialSnapshot,
    InvestmentCase,
    InvestmentThesis,
    Money,
)
from aic.research import ResearchContext, generate_thesis, render_thesis_document
from aic.research.openai_provider import OpenAIProvider

EUR = "EUR"

company = Company(
    company_id=uuid4(),
    ticker="MVP",
    name="MVP Example Corp",
    exchange="TEST",
    country="ES",
    sector="Technology",
    industry="Software",
)

evidence = [
    Evidence(
        evidence_id=uuid4(),
        source="MVP validation",
        title="Revenue growth",
        excerpt="The company is expected to grow revenue during the forecast period.",
        retrieved_date=date.now(UTC).date(),
        evidence_type=EvidenceType.FACT,
    ),
    Evidence(
        evidence_id=uuid4(),
        source="MVP validation",
        title="DCF assumption",
        excerpt="The DCF uses a 10% WACC and 2% terminal growth rate.",
        retrieved_date=datetime.now(UTC).date(),
        evidence_type=EvidenceType.ASSUMPTION,
    ),
]

snapshot = FinancialSnapshot(
    as_of=datetime.now(UTC).date(),
    revenue=Money(amount=Decimal(1000), currency=EUR),
    operating_income=Money(amount=Decimal(200), currency=EUR),
    net_income=Money(amount=Decimal(150), currency=EUR),
    free_cash_flow=Money(amount=Decimal(100), currency=EUR),
    cash=Money(amount=Decimal(100), currency=EUR),
    debt=Money(amount=Decimal(50), currency=EUR),
)

thesis = InvestmentThesis(
    summary="Initial thesis pending AI research analysis.",
    supporting_evidence=evidence,
    key_assumptions=[],
    key_risks=[],
    invalidation_conditions=[],
)

case = InvestmentCase(
    case_id=uuid4(),
    company=company,
    financial_snapshots=[snapshot],
    thesis=thesis,
    evidence=evidence,
)

assumptions = DCFAssumptions(
    forecast=[
        ForecastYear(
            year=1,
            revenue=Money(amount=Decimal(1100), currency=EUR),
            depreciation_and_amortization=Money(amount=Decimal(50), currency=EUR),
            capital_expenditure=Money(amount=Decimal(60), currency=EUR),
            change_in_net_working_capital=Money(amount=Decimal(20), currency=EUR),
        ),
        ForecastYear(
            year=2,
            revenue=Money(amount=Decimal(1200), currency=EUR),
            depreciation_and_amortization=Money(amount=Decimal(55), currency=EUR),
            capital_expenditure=Money(amount=Decimal(65), currency=EUR),
            change_in_net_working_capital=Money(amount=Decimal(20), currency=EUR),
        ),
        ForecastYear(
            year=3,
            revenue=Money(amount=Decimal(1300), currency=EUR),
            depreciation_and_amortization=print("DCF result:          OK")Money(amount=Decimal(60), currency=EUR),
            capital_expenditure=Money(amount=Decimal(70), currency=EUR),
            change_in_net_working_capital=Money(amount=Decimal(25), currency=EUR),
        ),
    ],
    operating_margin=Decimal("0.20"),
    tax_rate=Decimal("0.25"),
    wacc=Decimal("0.10"),
    terminal_growth_rate=Decimal("0.02"),
    cash=Money(amount=Decimal(100), currency=EUR),
    debt=Money(amount=Decimal(50), currency=EUR),
    shares_outstanding=Decimal(100),
)

dcf_result = compute_dcf(assumptions)

print("=" * 70)
print("MVP VALIDATION")
print("=" * 70)
print(f"Company:             {company.name} ({company.ticker})")
print(f"Currency:            {dcf_result.enterprise_value.currency}")
print(f"Enterprise Value:    {dcf_result.enterprise_value.amount}")
print(f"Equity Value:        {dcf_result.equity_value.amount}")
print(f"Value / Share:       {dcf_result.implied_value_per_share.amount}")
print()

context = ResearchContext(
    investment_case=case,
    dcf_result=dcf_result,
)

print("ResearchContext:     OK")
print(f"Evidence supplied:   {len(evidence)}")
print("DCF result:          OK")
print()

# This requires the configured OpenAI provider/API key.
# This requires the configured OpenAI provider/API key.
api_key = os.environ["OPENAI_API_KEY"]
provider = OpenAIProvider(api_key=api_key)

generated_thesis = generate_thesis(context, provider)

print("Investment Thesis:   OK")
print(f"Summary:             {generated_thesis.summary}")
print(f"Evidence linked:     {len(generated_thesis.supporting_evidence)}")
print()

document = render_thesis_document(generated_thesis)

print("=" * 70)
print("FINAL THESIS DOCUMENT")
print("=" * 70)
print(document)
print("=" * 70) 