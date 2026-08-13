from pydantic import BaseModel

from aic.dcf import DCFResult
from aic.domain import AnalysisAssessment, InvestmentCase


class CommitteeAdjudicationContext(BaseModel):
    investment_case: InvestmentCase
    dcf_result: DCFResult
    bull_assessment: AnalysisAssessment
    bear_assessment: AnalysisAssessment
