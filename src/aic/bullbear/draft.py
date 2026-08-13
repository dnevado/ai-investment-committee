from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AssessmentDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")

    conclusion: str
    confidence: float = Field(ge=0.0, le=1.0)
    arguments: list[str]
    assumptions: list[str]
    risks: list[str]
    supporting_evidence_ids: list[UUID]
