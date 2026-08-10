from datetime import UTC, datetime
from uuid import UUID

from pydantic import BaseModel, Field

from aic.domain.company import Company
from aic.domain.evidence import Evidence
from aic.domain.financial_snapshot import FinancialSnapshot
from aic.domain.thesis import InvestmentThesis


class InvestmentCase(BaseModel):
    case_id: UUID
    company: Company
    financial_snapshots: list[FinancialSnapshot] = Field(min_length=1)
    thesis: InvestmentThesis
    analysis_timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    evidence: list[Evidence] = []
