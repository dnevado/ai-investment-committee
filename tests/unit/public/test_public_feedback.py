import pytest
from pydantic import ValidationError

from aic.public.feedback import FeedbackSubmission


def test_feedback_rejects_all_blank_submission() -> None:
    with pytest.raises(ValidationError):
        FeedbackSubmission()


def test_feedback_accepts_a_single_non_blank_answer() -> None:
    submission = FeedbackSubmission(intended_use="Screening ideas before deeper research")

    assert submission.intended_use == "Screening ideas before deeper research"
    assert submission.most_valuable_part is None
    assert submission.email is None


def test_feedback_succeeds_without_an_associated_email() -> None:
    submission = FeedbackSubmission(willing_to_pay="Maybe, depends on accuracy")

    assert submission.email is None
