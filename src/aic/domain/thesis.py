from pydantic import BaseModel

from aic.domain.evidence import Evidence


class InvestmentThesis(BaseModel):
    summary: str
    supporting_evidence: list[Evidence] = []
    key_assumptions: list[str] = []
    key_risks: list[str] = []
    invalidation_conditions: list[str] = []
