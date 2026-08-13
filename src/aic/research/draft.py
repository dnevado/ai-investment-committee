from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ThesisDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: str
    supporting_evidence_ids: list[UUID]
    key_assumptions: list[str]
    key_risks: list[str]
    invalidation_conditions: list[str]