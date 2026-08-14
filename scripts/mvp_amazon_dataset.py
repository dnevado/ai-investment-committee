"""Shared Amazon FY2025 reference dataset used by both mvp_amazon_validation.py
(thesis-only demo) and mvp_amazon_acceptance.py (full-pipeline acceptance gate).

Kept as a single source of truth so the two scripts cannot silently drift apart —
the acceptance gate is only meaningful if it is validating the same inputs the
validation script demonstrates.

All dollar figures are in whole USD (not millions). Historical (FACT) figures are
Amazon's own reported FY2025 (year ended December 31, 2025) results, sourced from
Amazon's Form 10-K / Q4 2025 earnings release on SEC EDGAR and cross-checked
against independent financial-data aggregators. Forecast figures (ASSUMPTION) are
this validation model's own assumptions, not claims about Amazon, and are grounded
in the cited analyst ranges rather than invented outright.
"""

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

from aic.dcf import DCFAssumptions, ForecastYear
from aic.domain import Company, Evidence, EvidenceType, FinancialSnapshot, Money
from aic.workflow import WorkflowInput

USD = "USD"
TODAY = datetime.now(UTC).date()


def build_company() -> Company:
    return Company(
        company_id=uuid4(),
        ticker="AMZN",
        name="Amazon.com, Inc.",
        exchange="NASDAQ",
        country="US",
        sector="Technology",
        industry="Internet Retail / Cloud",
    )


def build_evidence() -> list[Evidence]:
    return [
        Evidence(
            evidence_id=uuid4(),
            source="Amazon.com, Inc. Form 10-K, fiscal year ended December 31, 2025",
            title="FY2025 net sales (revenue)",
            excerpt=(
                "Revenue increased 12% to $716.9 billion in 2025, compared with "
                "$638.0 billion in 2024."
            ),
            retrieved_date=TODAY,
            evidence_type=EvidenceType.FACT,
            reference="https://www.sec.gov/Archives/edgar/data/1018724/000101872426000004/amzn-20251231.htm",
        ),
        Evidence(
            evidence_id=uuid4(),
            source="Amazon.com, Inc. Form 10-K, fiscal year ended December 31, 2025",
            title="FY2025 operating income",
            excerpt="Operating income was $79,975 million in FY2025, compared with $68,593 million in FY2024.",
            retrieved_date=TODAY,
            evidence_type=EvidenceType.FACT,
            reference="https://www.sec.gov/Archives/edgar/data/1018724/000101872426000004/amzn-20251231.htm",
        ),
        Evidence(
            evidence_id=uuid4(),
            source="Amazon.com, Inc. Form 10-K / Q4 2025 earnings release",
            title="FY2025 net income",
            excerpt=(
                "Net income was $77,670 million, up from $59,248 million in the prior "
                "year. Diluted earnings per share rose to $7.17 from $5.53."
            ),
            retrieved_date=TODAY,
            evidence_type=EvidenceType.FACT,
            reference="https://www.sec.gov/Archives/edgar/data/1018724/000101872426000002/amzn-20251231xex991.htm",
        ),
        Evidence(
            evidence_id=uuid4(),
            source="Amazon FY2025 cash flow statement (aggregated from Form 10-K)",
            title="FY2025 free cash flow",
            excerpt=(
                "Free cash flow is calculated as cash provided by operating "
                "activities ($139,514 million) less purchases of property and "
                "equipment ($131,819 million), or approximately $7,695 million for "
                "FY2025 (down from $32,878 million in FY2024, reflecting a sharp "
                "increase in capital expenditures)."
            ),
            retrieved_date=TODAY,
            evidence_type=EvidenceType.CALCULATION,
            reference="https://www.stockanalysis.com/stocks/amzn/financials/cash-flow-statement/",
        ),
        Evidence(
            evidence_id=uuid4(),
            source="Amazon.com, Inc. Form 10-K, fiscal year ended December 31, 2025",
            title="FY2025 cash, cash equivalents, and marketable securities",
            excerpt=(
                "Cash, cash equivalents, and marketable securities totaled $123.0 "
                "billion as of December 31, 2025 ($86,810 million in cash and cash "
                "equivalents plus $36,219 million in short-term investments), "
                "compared with $101.2 billion as of December 31, 2024."
            ),
            retrieved_date=TODAY,
            evidence_type=EvidenceType.FACT,
            reference="https://www.stockanalysis.com/stocks/amzn/financials/balance-sheet/",
        ),
        Evidence(
            evidence_id=uuid4(),
            source="Amazon FY2025 balance sheet (aggregated from Form 10-K)",
            title="FY2025 total debt",
            excerpt=(
                "Total debt (long-term debt plus long-term lease liabilities and "
                "other borrowings) was $152,987 million as of December 31, 2025, "
                "compared with $130,900 million as of December 31, 2024."
            ),
            retrieved_date=TODAY,
            evidence_type=EvidenceType.FACT,
            reference="https://www.stockanalysis.com/stocks/amzn/financials/balance-sheet/",
        ),
        Evidence(
            evidence_id=uuid4(),
            source="Amazon.com, Inc. Form 10-K / Q4 2025 earnings release",
            title="FY2025 diluted weighted-average shares outstanding",
            excerpt=(
                "Diluted weighted-average shares outstanding were approximately "
                "10,833 million, derived from FY2025 net income of $77,670 million "
                "divided by diluted EPS of $7.17. Separately, total shares "
                "outstanding plus outstanding stock awards were reported at "
                "approximately 11.0 billion as of December 31, 2025."
            ),
            retrieved_date=TODAY,
            evidence_type=EvidenceType.CALCULATION,
            reference="https://www.sec.gov/Archives/edgar/data/1018724/000101872426000002/amzn-20251231xex991.htm",
        ),
        Evidence(
            evidence_id=uuid4(),
            source="Amazon.com, Inc. Form 10-K, fiscal year ended December 31, 2025",
            title="FY2025 effective tax rate",
            excerpt=(
                "Amazon's effective tax rate increased to 19.7% in 2025, with a "
                "$19.1 billion income tax provision recorded for the year."
            ),
            retrieved_date=TODAY,
            evidence_type=EvidenceType.FACT,
            reference="https://www.sec.gov/Archives/edgar/data/1018724/000101872426000004/amzn-20251231.htm",
        ),
        Evidence(
            evidence_id=uuid4(),
            source="Amazon FY2025 cash flow statement (aggregated from Form 10-K)",
            title="FY2025 depreciation and amortization",
            excerpt="Depreciation and amortization expense was $65,756 million in FY2025, compared with $52,795 million in FY2024.",
            retrieved_date=TODAY,
            evidence_type=EvidenceType.FACT,
            reference="https://www.stockanalysis.com/stocks/amzn/financials/cash-flow-statement/",
        ),
        Evidence(
            evidence_id=uuid4(),
            source="Amazon FY2025 cash flow statement (aggregated from Form 10-K)",
            title="FY2025 capital expenditures",
            excerpt=(
                "Purchases of property and equipment were $131,819 million in "
                "FY2025 (approximately 18.4% of revenue), compared with $82,999 "
                "million in FY2024. Amazon has since guided 2026 capital "
                "expenditures higher, to roughly $220 billion, citing higher "
                "infrastructure and memory costs. This ratio reflects a specific, "
                "disclosed, temporarily elevated AI-infrastructure buildout cycle, "
                "not a steady-state capital intensity; Amazon's pre-surge "
                "capex/revenue ratio ran closer to 10-13% in prior years. This "
                "model's forecast therefore fades the capex/revenue ratio down "
                "from 15% (Y1) to 12% (Y2) to 10% (Y3) rather than holding the "
                "elevated FY2025 ratio flat, consistent with standard DCF practice "
                "for a company in an identified, disclosed investment cycle."
            ),
            retrieved_date=TODAY,
            evidence_type=EvidenceType.FACT,
            reference="https://www.cnbc.com/2026/07/30/amazon-amzn-q2-earnings-report-2026.html",
        ),
        Evidence(
            evidence_id=uuid4(),
            source="Amazon FY2025 cash flow statement (aggregated from Form 10-K)",
            title="FY2025 change in net working capital",
            excerpt=(
                "The net change in operating assets and liabilities (receivables, "
                "inventories, accounts payable, accrued expenses, and unearned "
                "revenue) was a net use of cash of approximately $19,969 million in "
                "FY2025, compared with $15,541 million in FY2024."
            ),
            retrieved_date=TODAY,
            evidence_type=EvidenceType.CALCULATION,
            reference="https://www.stockanalysis.com/stocks/amzn/financials/cash-flow-statement/",
        ),
        Evidence(
            evidence_id=uuid4(),
            source="Sell-side analyst commentary (aggregated), retrieved 2026",
            title="Forecast revenue growth assumption",
            excerpt=(
                "Analyst estimates for Amazon's forward revenue growth cluster "
                "around 10.5%-14% annually through 2027-2028, driven particularly "
                "by AWS and advertising growth. This model assumes a moderate, "
                "fading growth path of 11% / 10% / 9% for Y1/Y2/Y3, within but "
                "below the more bullish end of the cited analyst range."
            ),
            retrieved_date=TODAY,
            evidence_type=EvidenceType.ASSUMPTION,
            reference="https://www.tikr.com/blog/amazon-stock-prediction-where-analysts-see-the-stock-going-by-2027",
        ),
        Evidence(
            evidence_id=uuid4(),
            source="Sell-side analyst commentary (aggregated), retrieved 2026",
            title="Forecast operating margin assumption",
            excerpt=(
                "FY2025 actual operating margin was approximately 11.2% "
                "($79,975M / $716,924M). Some analyst scenarios cite roughly 15% "
                "operating margins as an achievable longer-term case on continued "
                "AWS/advertising mix shift. This model assumes a moderate 12.0% "
                "operating margin across the forecast horizon, applied uniformly to "
                "every forecast year per this project's DCF engine convention."
            ),
            retrieved_date=TODAY,
            evidence_type=EvidenceType.ASSUMPTION,
            reference="https://www.tikr.com/blog/amazon-stock-prediction-where-analysts-see-the-stock-going-by-2027",
        ),
        Evidence(
            evidence_id=uuid4(),
            source="Third-party WACC estimates (aggregated), retrieved 2026",
            title="WACC assumption",
            excerpt=(
                "Published WACC estimates for Amazon vary by source and "
                "methodology: approximately 7.62% (AlphaSpread), 8.2% "
                "(ValueInvesting.io), and 13.13% (GuruFocus). This model assumes a "
                "9.0% WACC, a value within the lower-to-middle portion of the cited "
                "range."
            ),
            retrieved_date=TODAY,
            evidence_type=EvidenceType.ASSUMPTION,
            reference="https://www.alphaspread.com/security/nasdaq/amzn/discount-rate",
        ),
        Evidence(
            evidence_id=uuid4(),
            source="Standard DCF modeling convention",
            title="Terminal growth rate assumption",
            excerpt=(
                "A 3.0% terminal growth rate is assumed, consistent with the "
                "standard convention of anchoring perpetuity growth close to "
                "long-run nominal GDP growth rather than a company-specific "
                "estimate."
            ),
            retrieved_date=TODAY,
            evidence_type=EvidenceType.ASSUMPTION,
        ),
    ]


def build_snapshot() -> FinancialSnapshot:
    return FinancialSnapshot(
        as_of=TODAY,
        revenue=Money(amount=Decimal(716924000000), currency=USD),
        operating_income=Money(amount=Decimal(79975000000), currency=USD),
        net_income=Money(amount=Decimal(77670000000), currency=USD),
        free_cash_flow=Money(amount=Decimal(7695000000), currency=USD),
        cash=Money(amount=Decimal(123029000000), currency=USD),
        debt=Money(amount=Decimal(152987000000), currency=USD),
        shares_outstanding=Decimal(10833000000),
    )


def build_dcf_assumptions() -> DCFAssumptions:
    """Capital expenditure is faded down from 15% to 12% to 10% of revenue
    (rather than holding FY2025's elevated ~18.4% ratio flat), since that
    ratio reflects a disclosed, temporary AI-infrastructure buildout cycle,
    not Amazon's steady-state capital intensity (see the capex Evidence
    entry). Operating margin, tax rate, WACC, and terminal growth are
    single values applied across the whole forecast, per this project's
    own DCF engine convention.
    """
    return DCFAssumptions(
        forecast=[
            ForecastYear(
                revenue=Money(amount=Decimal(795786000000), currency=USD),
                depreciation_and_amortization=Money(amount=Decimal(72978000000), currency=USD),
                capital_expenditure=Money(amount=Decimal(119368000000), currency=USD),
                change_in_net_working_capital=Money(amount=Decimal(22164000000), currency=USD),
            ),
            ForecastYear(
                revenue=Money(amount=Decimal(875365000000), currency=USD),
                depreciation_and_amortization=Money(amount=Decimal(80285000000), currency=USD),
                capital_expenditure=Money(amount=Decimal(105044000000), currency=USD),
                change_in_net_working_capital=Money(amount=Decimal(24384000000), currency=USD),
            ),
            ForecastYear(
                revenue=Money(amount=Decimal(954148000000), currency=USD),
                depreciation_and_amortization=Money(amount=Decimal(87514000000), currency=USD),
                capital_expenditure=Money(amount=Decimal(95415000000), currency=USD),
                change_in_net_working_capital=Money(amount=Decimal(26577000000), currency=USD),
            ),
        ],
        operating_margin=Decimal("0.12"),
        tax_rate=Decimal("0.197"),
        wacc=Decimal("0.09"),
        terminal_growth_rate=Decimal("0.03"),
        cash=Money(amount=Decimal(123029000000), currency=USD),
        debt=Money(amount=Decimal(152987000000), currency=USD),
        shares_outstanding=Decimal(10833000000),
    )


def build_workflow_input() -> WorkflowInput:
    return WorkflowInput(
        company=build_company(),
        financial_snapshots=[build_snapshot()],
        evidence=build_evidence(),
        dcf_assumptions=build_dcf_assumptions(),
    )
