from datetime import date
from decimal import Decimal

from pydantic import BaseModel, model_validator

from aic.domain.money import Money

_MONEY_FIELDS = (
    "revenue",
    "operating_income",
    "net_income",
    "free_cash_flow",
    "cash",
    "debt",
)


class FinancialSnapshot(BaseModel):
    as_of: date
    revenue: Money | None = None
    operating_income: Money | None = None
    net_income: Money | None = None
    free_cash_flow: Money | None = None
    cash: Money | None = None
    debt: Money | None = None
    shares_outstanding: Decimal | None = None

    @model_validator(mode="after")
    def _check_consistent_currency(self) -> "FinancialSnapshot":
        currencies = {
            getattr(self, field).currency
            for field in _MONEY_FIELDS
            if getattr(self, field) is not None
        }
        if len(currencies) > 1:
            raise ValueError(
                f"FinancialSnapshot monetary metrics must share one currency, "
                f"got: {sorted(currencies)}"
            )
        return self
