from pydantic import BaseModel, Field

from aic.dcf import DCFAssumptions
from aic.domain import Company, Evidence, FinancialSnapshot


class WorkflowInput(BaseModel):
    company: Company
    financial_snapshots: list[FinancialSnapshot] = Field(min_length=1)
    evidence: list[Evidence] = []
    dcf_assumptions: DCFAssumptions
