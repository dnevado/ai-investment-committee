import logging
from uuid import uuid4

from aic.committee.context import CommitteeAdjudicationContext
from aic.committee.draft import CommitteeDecisionDraft
from aic.committee.prompt import build_prompt
from aic.domain import CommitteeDecision
from aic.research.provider import LLMProvider

logger = logging.getLogger(__name__)


def _compose_rationale(draft: CommitteeDecisionDraft) -> str:
    return (
        f"Central thesis: {draft.central_thesis}\n\n"
        f"Key disagreements: {'; '.join(draft.key_disagreements) or '(none)'}\n\n"
        f"Valuation: {draft.valuation_summary}\n\n"
        f"Downside risks: {'; '.join(draft.downside_risks) or '(none)'}\n\n"
        f"Invalidation conditions: {'; '.join(draft.invalidation_conditions) or '(none)'}\n\n"
        f"Conviction: {draft.confidence}"
    )


def generate_decision(
    context: CommitteeAdjudicationContext, provider: LLMProvider
) -> CommitteeDecision:
    system_prompt, user_prompt = build_prompt(context)
    completion = provider.complete_structured(
        system_prompt=system_prompt, user_prompt=user_prompt, schema=CommitteeDecisionDraft
    )
    logger.info(
        "committee decision adjudicated",
        extra={
            "prompt_tokens": completion.prompt_tokens,
            "completion_tokens": completion.completion_tokens,
            "latency_ms": completion.latency_ms,
        },
    )

    draft = CommitteeDecisionDraft.model_validate(completion.content)

    known_evidence_ids = {evidence.evidence_id for evidence in context.investment_case.evidence}
    for evidence_id in draft.supporting_evidence_ids:
        if evidence_id not in known_evidence_ids:
            raise ValueError(f"LLM referenced unknown evidence_id: {evidence_id}")

    return CommitteeDecision(
        decision_id=uuid4(),
        recommendation=draft.recommendation,
        rationale=_compose_rationale(draft),
        referenced_evidence=draft.supporting_evidence_ids,
        referenced_thesis=context.investment_case.thesis,
        valuation_reference=None,
        dissent=draft.dissent,
    )
