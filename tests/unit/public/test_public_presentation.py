from public_fakes import make_evidence, make_workflow_result

from aic.domain.enums import EvidenceType
from aic.public.presentation import build_presentation


def test_build_presentation_maps_workflow_result_fields() -> None:
    evidence = [make_evidence()]
    result = make_workflow_result(evidence)

    presentation = build_presentation(result, evidence)

    assert presentation.company_name == result.report.company.name
    assert presentation.ticker == result.report.company.ticker
    assert presentation.implied_value_per_share == "$75.07"
    assert presentation.recommendation == result.decision.recommendation.value
    assert presentation.conviction == 0.82
    assert presentation.thesis_summary == result.thesis.summary
    assert presentation.bull_summary == result.bull_assessment.conclusion
    assert presentation.bear_summary == result.bear_assessment.conclusion
    assert presentation.key_assumptions == result.thesis.key_assumptions
    assert presentation.key_risks == result.thesis.key_risks


def test_build_presentation_includes_evidence_referenced_by_every_stage() -> None:
    thesis_evidence = make_evidence(title="Thesis-cited item")
    bull_only_evidence = make_evidence(title="Bull-only item")
    evidence = [thesis_evidence, bull_only_evidence]
    result = make_workflow_result(evidence)

    # Simulate an evidence item only referenced by bull/bear/decision, not by the
    # thesis itself, to prove build_presentation resolves those UUID-only
    # references against the full evidence list rather than only the thesis's
    # own (full-object) supporting_evidence.
    result = result.model_copy(
        update={
            "thesis": result.thesis.model_copy(update={"supporting_evidence": [thesis_evidence]})
        }
    )

    presentation = build_presentation(result, evidence)

    titles = {item.title for item in presentation.evidence}
    assert thesis_evidence.title in titles


def test_build_presentation_classifies_evidence_types() -> None:
    fact = make_evidence(EvidenceType.FACT, title="Fact item")
    calculation = make_evidence(EvidenceType.CALCULATION, title="Calculation item")
    assumption = make_evidence(EvidenceType.ASSUMPTION, title="Assumption item")
    interpretation = make_evidence(EvidenceType.INTERPRETATION, title="Interpretation item")
    opinion = make_evidence(EvidenceType.OPINION, title="Opinion item")
    evidence = [fact, calculation, assumption, interpretation, opinion]
    result = make_workflow_result(evidence)
    result = result.model_copy(
        update={"thesis": result.thesis.model_copy(update={"supporting_evidence": evidence})}
    )

    presentation = build_presentation(result, evidence)

    classification_by_title = {item.title: item.classification for item in presentation.evidence}
    assert classification_by_title[fact.title] == "Reported fact"
    assert classification_by_title[calculation.title] == "Calculation"
    assert classification_by_title[assumption.title] == "Forecast assumption"
    assert classification_by_title[interpretation.title] == "AI analysis"
    assert classification_by_title[opinion.title] == "AI analysis"
