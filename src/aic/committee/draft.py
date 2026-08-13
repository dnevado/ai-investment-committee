from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from aic.domain import Recommendation


class CommitteeDecisionDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")

    central_thesis: str
    key_disagreements: list[str]
    valuation_summary: str
    downside_risks: list[str]
    invalidation_conditions: list[str]
    recommendation: Recommendation
    confidence: float = Field(ge=0.0, le=1.0)
    dissent: list[str]
    supporting_evidence_ids: list[UUID]
