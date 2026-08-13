from pydantic import BaseModel, Field

from aic.dcf import DCFResult
from aic.domain import (
    AnalysisAssessment,
    CommitteeDecision,
    Company,
    FinancialSnapshot,
    InvestmentThesis,
)


class CommitteeReport(BaseModel):
    company: Company
    financial_snapshots: list[FinancialSnapshot] = Field(min_length=1)
    thesis: InvestmentThesis
    dcf_result: DCFResult
    assessment: AnalysisAssessment
    decision: CommitteeDecision
    bull_assessment: AnalysisAssessment | None = None
    bear_assessment: AnalysisAssessment | None = None
