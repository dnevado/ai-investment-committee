from datetime import date
from uuid import UUID

from pydantic import BaseModel

from aic.domain.enums import EvidenceType


class Evidence(BaseModel):
    evidence_id: UUID
    source: str
    title: str
    excerpt: str
    retrieved_date: date
    evidence_type: EvidenceType
    reference: str | None = None
    publication_date: date | None = None
