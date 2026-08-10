from uuid import uuid4

import pytest
from pydantic import ValidationError

from aic.domain import Company


def test_valid_construction() -> None:
    company = Company(
        company_id=uuid4(),
        ticker="ASML",
        name="ASML Holding",
        exchange="AEX",
        country="NL",
        sector="Technology",
        industry="Semiconductor Equipment",
    )
    assert company.ticker == "ASML"
    assert company.name == "ASML Holding"


@pytest.mark.parametrize(
    "missing_field",
    ["company_id", "ticker", "name", "exchange", "country", "sector", "industry"],
)
def test_required_field_validation(missing_field: str) -> None:
    valid_kwargs = {
        "company_id": uuid4(),
        "ticker": "ASML",
        "name": "ASML Holding",
        "exchange": "AEX",
        "country": "NL",
        "sector": "Technology",
        "industry": "Semiconductor Equipment",
    }
    del valid_kwargs[missing_field]
    with pytest.raises(ValidationError):
        Company(**valid_kwargs)


def test_round_trip_serialization() -> None:
    company = Company(
        company_id=uuid4(),
        ticker="ASML",
        name="ASML Holding",
        exchange="AEX",
        country="NL",
        sector="Technology",
        industry="Semiconductor Equipment",
    )
    restored = Company.model_validate(company.model_dump())
    assert restored == company
