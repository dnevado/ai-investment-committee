from datetime import UTC, date, datetime

from pydantic import BaseModel

from aic.domain import Evidence
from aic.domain.enums import EvidenceType
from aic.workflow import WorkflowResult

_CLASSIFICATION_LABELS: dict[EvidenceType, str] = {
    EvidenceType.FACT: "Reported fact",
    EvidenceType.CALCULATION: "Calculation",
    EvidenceType.ASSUMPTION: "Forecast assumption",
    EvidenceType.INTERPRETATION: "AI analysis",
    EvidenceType.OPINION: "AI analysis",
}

# A small, curated sample for the landing page's compact evidence table (one
# FACT, one CALCULATION, two ASSUMPTIONs) — chosen for legibility, not an
# exhaustive dump. Falls back to whatever evidence is available if these
# specific titles aren't present (e.g. in tests, or a future re-capture),
# so the table is never empty as long as some evidence exists.
_LANDING_SAMPLE_TITLES = (
    "FY2025 net sales (revenue)",
    "FY2025 free cash flow",
    "WACC assumption",
    "Terminal growth rate assumption",
)


class EvidenceItemView(BaseModel):
    title: str
    excerpt: str
    classification: str
    source: str
    reference: str | None = None


class AmazonPresentation(BaseModel):
    company_name: str
    ticker: str
    implied_value_per_share: str
    enterprise_value: str
    equity_value: str
    recommendation: str
    conviction: float
    thesis_summary: str
    bull_summary: str
    bear_summary: str
    key_assumptions: list[str]
    key_risks: list[str]
    evidence: list[EvidenceItemView]
    captured_at: date

    @property
    def landing_sample_evidence(self) -> list[EvidenceItemView]:
        by_title = {item.title: item for item in self.evidence}
        sample = [by_title[t] for t in _LANDING_SAMPLE_TITLES if t in by_title]
        remaining = [item for item in self.evidence if item.title not in _LANDING_SAMPLE_TITLES]
        return (sample + remaining)[:4]


def _format_money(amount: float, currency: str) -> str:
    symbol = "$" if currency == "USD" else f"{currency} "
    return f"{symbol}{amount:,.2f}"


def _format_billions(amount: float, currency: str) -> str:
    symbol = "$" if currency == "USD" else f"{currency} "
    return f"{symbol}{amount / 1_000_000_000:,.2f}B"


def _conviction(rationale: str) -> float:
    """CommitteeDecision has no standalone confidence field; the Committee's
    conviction score is folded into rationale's trailing "Conviction: {value}" line
    (feature 006's _compose_rationale)."""
    for line in reversed(rationale.splitlines()):
        stripped = line.strip()
        if stripped.lower().startswith("conviction:"):
            try:
                return float(stripped.split(":", 1)[1].strip())
            except ValueError:
                return 0.0
    return 0.0


def build_presentation(
    result: WorkflowResult, evidence: list[Evidence]
) -> AmazonPresentation:
    """`evidence` is the full, original evidence list supplied to the workflow
    (WorkflowInput.evidence) — needed because AnalysisAssessment.supporting_evidence
    and CommitteeDecision.referenced_evidence only store evidence_id UUIDs, not full
    Evidence objects, so resolving every evidence item referenced anywhere in the run
    requires looking them up against the original list."""
    evidence_by_id = {item.evidence_id: item for item in evidence}

    referenced_ids = {item.evidence_id for item in result.thesis.supporting_evidence}
    referenced_ids.update(result.bull_assessment.supporting_evidence)
    referenced_ids.update(result.bear_assessment.supporting_evidence)
    referenced_ids.update(result.decision.referenced_evidence)

    evidence_views = [
        EvidenceItemView(
            title=item.title,
            excerpt=item.excerpt,
            classification=_CLASSIFICATION_LABELS[item.evidence_type],
            source=item.source,
            reference=item.reference,
        )
        for evidence_id in referenced_ids
        if (item := evidence_by_id.get(evidence_id)) is not None
    ]

    dcf = result.dcf_result
    return AmazonPresentation(
        company_name=result.report.company.name,
        ticker=result.report.company.ticker,
        implied_value_per_share=_format_money(
            float(dcf.implied_value_per_share.amount), dcf.implied_value_per_share.currency
        ),
        enterprise_value=_format_billions(
            float(dcf.enterprise_value.amount), dcf.enterprise_value.currency
        ),
        equity_value=_format_billions(
            float(dcf.equity_value.amount), dcf.equity_value.currency
        ),
        recommendation=result.decision.recommendation.value,
        conviction=_conviction(result.decision.rationale),
        thesis_summary=result.thesis.summary,
        bull_summary=result.bull_assessment.conclusion,
        bear_summary=result.bear_assessment.conclusion,
        key_assumptions=list(result.thesis.key_assumptions),
        key_risks=list(result.thesis.key_risks),
        evidence=evidence_views,
        captured_at=datetime.now(UTC).date(),
    )
