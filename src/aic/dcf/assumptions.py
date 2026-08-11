from decimal import Decimal

from pydantic import BaseModel, Field, model_validator

from aic.domain import Money


class ForecastYear(BaseModel):
    revenue: Money
    depreciation_and_amortization: Money
    capital_expenditure: Money
    change_in_net_working_capital: Money


class DCFAssumptions(BaseModel):
    forecast: list[ForecastYear] = Field(min_length=1)
    operating_margin: Decimal
    tax_rate: Decimal = Field(ge=0, le=1)
    wacc: Decimal = Field(gt=0)
    terminal_growth_rate: Decimal
    cash: Money
    debt: Money
    shares_outstanding: Decimal = Field(gt=0)

    @model_validator(mode="after")
    def _check_wacc_exceeds_terminal_growth(self) -> "DCFAssumptions":
        if self.wacc <= self.terminal_growth_rate:
            raise ValueError(
                "wacc must be strictly greater than terminal_growth_rate, got "
                f"wacc={self.wacc}, terminal_growth_rate={self.terminal_growth_rate}"
            )
        return self

    @model_validator(mode="after")
    def _check_consistent_currency(self) -> "DCFAssumptions":
        currencies = {item.revenue.currency for item in self.forecast}
        currencies |= {item.depreciation_and_amortization.currency for item in self.forecast}
        currencies |= {item.capital_expenditure.currency for item in self.forecast}
        currencies |= {item.change_in_net_working_capital.currency for item in self.forecast}
        currencies.add(self.cash.currency)
        currencies.add(self.debt.currency)
        if len(currencies) > 1:
            raise ValueError(
                f"DCFAssumptions monetary values must share one currency, got: {sorted(currencies)}"
            )
        return self
