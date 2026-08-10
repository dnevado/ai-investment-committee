from datetime import date
from uuid import UUID

from pydantic import BaseModel, Field

from aic.domain.money import Money


class ValuationResult(BaseModel):
    valuation_id: UUID
    method: str
    valuation_date: date
    estimated_value: Money
    confidence: float = Field(ge=0.0, le=1.0)
    assumption_evidence_refs: list[UUID] = []
