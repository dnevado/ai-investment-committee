from uuid import UUID

from pydantic import BaseModel, Field


class AnalysisAssessment(BaseModel):
    assessment_id: UUID
    conclusion: str
    confidence: float = Field(ge=0.0, le=1.0)
    arguments: list[str] = []
    supporting_evidence: list[UUID] = []
    assumptions: list[str] = []
    risks: list[str] = []
