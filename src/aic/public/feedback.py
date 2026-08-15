from datetime import UTC, datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, EmailStr, Field, model_validator


class FeedbackSubmission(BaseModel):
    feedback_id: UUID = Field(default_factory=uuid4)
    intended_use: str | None = None
    most_valuable_part: str | None = None
    trust_blockers: str | None = None
    regular_use: str | None = None
    willing_to_pay: str | None = None
    pre_conditions: str | None = None
    email: EmailStr | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @model_validator(mode="after")
    def _check_at_least_one_answer(self) -> "FeedbackSubmission":
        answers = (
            self.intended_use,
            self.most_valuable_part,
            self.trust_blockers,
            self.regular_use,
            self.willing_to_pay,
            self.pre_conditions,
        )
        if not any(answer and answer.strip() for answer in answers):
            raise ValueError(
                "At least one feedback answer must be non-empty; a submission "
                "with all six questions blank carries no signal."
            )
        return self
