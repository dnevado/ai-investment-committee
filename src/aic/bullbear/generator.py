import logging
from collections.abc import Callable
from uuid import uuid4

from aic.bullbear.context import BullBearContext
from aic.bullbear.draft import AssessmentDraft
from aic.bullbear.prompt import build_bear_prompt, build_bull_prompt
from aic.domain import AnalysisAssessment
from aic.research.provider import LLMProvider

logger = logging.getLogger(__name__)


def _generate(
    context: BullBearContext,
    provider: LLMProvider,
    *,
    role: str,
    build_prompt: Callable[[BullBearContext], tuple[str, str]],
) -> AnalysisAssessment:
    system_prompt, user_prompt = build_prompt(context)
    completion = provider.complete_structured(
        system_prompt=system_prompt, user_prompt=user_prompt, schema=AssessmentDraft
    )
    logger.info(
        f"{role} assessment generated",
        extra={
            "prompt_tokens": completion.prompt_tokens,
            "completion_tokens": completion.completion_tokens,
            "latency_ms": completion.latency_ms,
        },
    )

    draft = AssessmentDraft.model_validate(completion.content)

    known_evidence_ids = {
        evidence.evidence_id for evidence in context.investment_case.evidence
    }
    for evidence_id in draft.supporting_evidence_ids:
        if evidence_id not in known_evidence_ids:
            raise ValueError(f"LLM referenced unknown evidence_id: {evidence_id}")

    return AnalysisAssessment(
        assessment_id=uuid4(),
        conclusion=draft.conclusion,
        confidence=draft.confidence,
        arguments=draft.arguments,
        supporting_evidence=draft.supporting_evidence_ids,
        assumptions=draft.assumptions,
        risks=draft.risks,
    )


def generate_bull_assessment(
    context: BullBearContext, provider: LLMProvider
) -> AnalysisAssessment:
    return _generate(context, provider, role="bull", build_prompt=build_bull_prompt)


def generate_bear_assessment(
    context: BullBearContext, provider: LLMProvider
) -> AnalysisAssessment:
    return _generate(context, provider, role="bear", build_prompt=build_bear_prompt)
