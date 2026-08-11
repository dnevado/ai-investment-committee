from pydantic import BaseModel

from aic.domain import Money


class YearResult(BaseModel):
    year: int
    fcff: Money
    pv_fcff: Money


class DCFResult(BaseModel):
    per_year: list[YearResult]
    terminal_value: Money
    pv_terminal_value: Money
    enterprise_value: Money
    equity_value: Money
    implied_value_per_share: Money
