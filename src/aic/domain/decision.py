from datetime import UTC, datetime
from uuid import UUID

from pydantic import BaseModel, Field

from aic.domain.enums import Recommendation
from aic.domain.thesis import InvestmentThesis


class CommitteeDecision(BaseModel):
    decision_id: UUID
    recommendation: Recommendation
    rationale: str
    decision_timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    referenced_evidence: list[UUID] = []
    referenced_thesis: InvestmentThesis | None = None
    valuation_reference: UUID | None = None
    dissent: list[str] = []
