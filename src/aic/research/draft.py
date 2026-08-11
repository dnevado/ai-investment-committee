from uuid import UUID

from pydantic import BaseModel


class ThesisDraft(BaseModel):
    summary: str
    supporting_evidence_ids: list[UUID] = []
    key_assumptions: list[str] = []
    key_risks: list[str] = []
    invalidation_conditions: list[str] = []
