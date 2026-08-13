from pydantic import BaseModel

from aic.dcf import DCFResult
from aic.domain import (
    AnalysisAssessment,
    CommitteeDecision,
    InvestmentThesis,
    ValuationResult,
)
from aic.report import CommitteeReport


class WorkflowResult(BaseModel):
    dcf_result: DCFResult
    valuation_result: ValuationResult
    thesis: InvestmentThesis
    bull_assessment: AnalysisAssessment
    bear_assessment: AnalysisAssessment
    decision: CommitteeDecision
    report: CommitteeReport
    document: str
