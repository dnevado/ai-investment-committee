from datetime import date
from uuid import uuid4

from aic.domain import Evidence, EvidenceType, InvestmentThesis
from aic.research import render_thesis_document


def _thesis() -> InvestmentThesis:
    evidence = Evidence(
        evidence_id=uuid4(),
        source="10-K",
        title="FY2025 Annual Report",
        excerpt="Revenue grew 12% YoY",
        retrieved_date=date(2026, 1, 5),
        evidence_type=EvidenceType.FACT,
    )
    return InvestmentThesis(
        summary="Durable moat in EUV lithography.",
        supporting_evidence=[evidence],
        key_assumptions=["EUV demand persists"],
        key_risks=["Export restrictions"],
        invalidation_conditions=["Major customer cancels multi-year order"],
    )


def test_render_thesis_document_contains_exactly_the_thesis_content() -> None:
    thesis = _thesis()

    document = render_thesis_document(thesis)

    assert thesis.summary in document
    assert thesis.supporting_evidence[0].title in document
    assert thesis.supporting_evidence[0].excerpt in document
    assert thesis.key_assumptions[0] in document
    assert thesis.key_risks[0] in document
    assert thesis.invalidation_conditions[0] in document


def test_render_thesis_document_is_deterministic() -> None:
    thesis = _thesis()

    first = render_thesis_document(thesis)
    second = render_thesis_document(thesis)

    assert first == second


def test_render_thesis_document_handles_empty_lists() -> None:
    thesis = InvestmentThesis(summary="No supporting detail yet.")

    document = render_thesis_document(thesis)

    assert "No supporting detail yet." in document
    assert "(none)" in document
