from pydantic import BaseModel

from aic.dcf import DCFResult
from aic.domain import InvestmentCase


class ResearchContext(BaseModel):
    investment_case: InvestmentCase
    dcf_result: DCFResult
