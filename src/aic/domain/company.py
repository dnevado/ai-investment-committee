from uuid import UUID

from pydantic import BaseModel


class Company(BaseModel):
    company_id: UUID
    ticker: str
    name: str
    exchange: str
    country: str
    sector: str
    industry: str
