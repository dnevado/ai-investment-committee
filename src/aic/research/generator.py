import logging

from aic.domain import InvestmentThesis
from aic.research.context import ResearchContext
from aic.research.draft import ThesisDraft
from aic.research.prompt import build_prompt
from aic.research.provider import LLMProvider

logger = logging.getLogger(__name__)


def generate_thesis(
    context: ResearchContext, provider: LLMProvider
) -> InvestmentThesis:
    system_prompt, user_prompt = build_prompt(context)
    completion = provider.complete_structured(
        system_prompt=system_prompt, user_prompt=user_prompt, schema=ThesisDraft
    )
    logger.info(
        "thesis generation completed",
        extra={
            "prompt_tokens": completion.prompt_tokens,
            "completion_tokens": completion.completion_tokens,
            "latency_ms": completion.latency_ms,
        },
    )

    draft = ThesisDraft.model_validate(completion.content)

    known_evidence = {
        evidence.evidence_id: evidence for evidence in context.investment_case.evidence
    }
    resolved_evidence = []
    for evidence_id in draft.supporting_evidence_ids:
        if evidence_id not in known_evidence:
            raise ValueError(f"LLM referenced unknown evidence_id: {evidence_id}")
        resolved_evidence.append(known_evidence[evidence_id])

    return InvestmentThesis(
        summary=draft.summary,
        supporting_evidence=resolved_evidence,
        key_assumptions=draft.key_assumptions,
        key_risks=draft.key_risks,
        invalidation_conditions=draft.invalidation_conditions,
    )
