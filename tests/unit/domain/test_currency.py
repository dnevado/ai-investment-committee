import pytest
from pydantic import TypeAdapter, ValidationError

from aic.domain import CurrencyCode

_currency_adapter: TypeAdapter[str] = TypeAdapter(CurrencyCode)


@pytest.mark.parametrize("code", ["USD", "EUR", "JPY", "GBP"])
def test_accepts_real_iso_4217_codes(code: str) -> None:
    assert _currency_adapter.validate_python(code) == code


@pytest.mark.parametrize("code", ["NOTREAL", "USDD", "Dollars", "usd"])
def test_rejects_invalid_codes(code: str) -> None:
    with pytest.raises(ValidationError):
        _currency_adapter.validate_python(code)
