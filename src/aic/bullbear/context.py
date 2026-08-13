from pydantic import BaseModel

from aic.domain import InvestmentCase, ValuationResult


class BullBearContext(BaseModel):
    investment_case: InvestmentCase
    valuation_result: ValuationResult
