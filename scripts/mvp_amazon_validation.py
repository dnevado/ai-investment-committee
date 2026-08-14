"""Amazon FY2025 thesis-generation demo (one LLM call: generate_thesis).

For the full Bull/Bear/Committee/Report pipeline run against the same dataset,
see mvp_amazon_acceptance.py.
"""

from uuid import uuid4

from mvp_amazon_dataset import (
    build_company,
    build_dcf_assumptions,
    build_evidence,
    build_snapshot,
)

from aic.dcf import compute_dcf
from aic.domain import InvestmentCase, InvestmentThesis
from aic.research import (
    OpenAIProvider,
    ResearchContext,
    generate_thesis,
    render_thesis_document,
)
from aic.settings import get_settings

company = build_company()
evidence = build_evidence()
snapshot = build_snapshot()
assumptions = build_dcf_assumptions()

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

dcf_result = compute_dcf(assumptions)

settings = get_settings()

if not settings.openai_api_key:
    raise RuntimeError(
        "AIC_OPENAI_API_KEY is not configured. "
        "Set it before running the Amazon validation."
    )

provider = OpenAIProvider(api_key=settings.openai_api_key)


context = ResearchContext(
    investment_case=case,
    dcf_result=dcf_result,
)


print("=" * 70)
print("AMAZON MVP VALIDATION")
print("=" * 70)
print(f"Company:             {company.name} ({company.ticker})")
print(f"Currency:            {dcf_result.enterprise_value.currency}")
print(f"Enterprise Value:    {dcf_result.enterprise_value.amount}")
print(f"Equity Value:        {dcf_result.equity_value.amount}")
print(f"Value / Share:       {dcf_result.implied_value_per_share.amount}")
print()

print("ResearchContext:     OK")
print(f"Evidence supplied:   {len(evidence)}")
print("DCF result:          OK")
print()

generated_thesis = generate_thesis(context, provider)

print("Investment Thesis:   OK")
print(f"Summary:             {generated_thesis.summary}")
print(f"Evidence linked:     {len(generated_thesis.supporting_evidence)}")
print()

document = render_thesis_document(generated_thesis)

print("=" * 70)
print("FINAL AMAZON THESIS")
print("=" * 70)
print(document)
print("=" * 70)
