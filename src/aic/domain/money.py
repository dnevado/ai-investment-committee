from decimal import Decimal

from pydantic import BaseModel

from aic.domain.currency import CurrencyCode


class Money(BaseModel):
    amount: Decimal
    currency: CurrencyCode
