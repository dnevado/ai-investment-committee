"""Tests for `DynamoDbStorage` against `moto`'s DynamoDB mock — no real AWS
calls (research.md Decision 8). Mirrors `test_public_storage.py`'s
`SqliteStorage` coverage so both `Storage` implementations are held to the
same contract."""

import boto3
import pytest
from moto import mock_aws

from aic.public.feedback import FeedbackSubmission
from aic.public.registration import EarlyAccessRegistration
from aic.public.storage import DynamoDbStorage

_REGISTRATIONS_TABLE = "test-registrations"
_FEEDBACK_TABLE = "test-feedback-submissions"
_EVENTS_TABLE = "test-validation-events"


@pytest.fixture
def storage(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")

    with mock_aws():
        resource = boto3.resource("dynamodb", region_name="us-east-1")
        resource.create_table(
            TableName=_REGISTRATIONS_TABLE,
            KeySchema=[{"AttributeName": "email_normalized", "KeyType": "HASH"}],
            AttributeDefinitions=[
                {"AttributeName": "email_normalized", "AttributeType": "S"}
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        resource.create_table(
            TableName=_FEEDBACK_TABLE,
            KeySchema=[{"AttributeName": "feedback_id", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "feedback_id", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
        resource.create_table(
            TableName=_EVENTS_TABLE,
            KeySchema=[{"AttributeName": "event_id", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "event_id", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )

        yield DynamoDbStorage(
            registrations_table=_REGISTRATIONS_TABLE,
            feedback_table=_FEEDBACK_TABLE,
            events_table=_EVENTS_TABLE,
            resource=resource,
        )


def test_registration_round_trips(storage: DynamoDbStorage) -> None:
    registration = EarlyAccessRegistration(email="visitor@example.com", name="Alex", qualified=True)

    stored = storage.create_registration(registration)

    assert stored.registration_id == registration.registration_id
    assert storage.count_registrations(None, None) == 1
    assert storage.count_registrations(None, None, qualified_only=True) == 1


def test_feedback_round_trips(storage: DynamoDbStorage) -> None:
    submission = FeedbackSubmission(intended_use="Research")

    storage.create_feedback(submission)

    assert storage.count_feedback(None, None) == 1


def test_event_round_trips(storage: DynamoDbStorage) -> None:
    storage.record_event("landing_visit")

    assert storage.count_events("landing_visit", None, None) == 1


def test_duplicate_email_registration_does_not_create_second_row(
    storage: DynamoDbStorage,
) -> None:
    first = storage.create_registration(EarlyAccessRegistration(email="Visitor@Example.com"))
    second = storage.create_registration(EarlyAccessRegistration(email="visitor@example.com"))

    assert first.registration_id == second.registration_id
    assert storage.count_registrations(None, None) == 1


def test_duplicate_registration_preserves_original_fields(
    storage: DynamoDbStorage,
) -> None:
    first = storage.create_registration(
        EarlyAccessRegistration(email="visitor@example.com", role="individual investor")
    )

    second = storage.create_registration(
        EarlyAccessRegistration(email="visitor@example.com", role="finance professional")
    )

    assert second.registration_id == first.registration_id
    assert second.role == "individual investor"  # the original, not the resubmission's


def test_event_records_optional_device_and_source(storage: DynamoDbStorage) -> None:
    event = storage.record_event("landing_visit", device="mobile", source="twitter")

    assert event.device == "mobile"
    assert event.source == "twitter"


def test_count_events_grouped_by_device(storage: DynamoDbStorage) -> None:
    storage.record_event("landing_visit", device="mobile")
    storage.record_event("landing_visit", device="mobile")
    storage.record_event("landing_visit", device="desktop")
    storage.record_event("landing_visit")  # no device recorded

    grouped = storage.count_events_grouped("landing_visit", "device", None, None)

    assert grouped == {"mobile": 2, "desktop": 1, "unknown": 1}


def test_count_events_grouped_by_source(storage: DynamoDbStorage) -> None:
    storage.record_event("landing_visit", source="twitter")
    storage.record_event("landing_visit", source="newsletter")

    grouped = storage.count_events_grouped("landing_visit", "source", None, None)

    assert grouped == {"twitter": 1, "newsletter": 1}


def test_count_events_grouped_rejects_unsupported_column(storage: DynamoDbStorage) -> None:
    with pytest.raises(ValueError, match="Unsupported group_by column"):
        storage.count_events_grouped("landing_visit", "event_type", None, None)


def test_funnel_metrics_match_sqlite_semantics(storage: DynamoDbStorage) -> None:
    """Cross-checks `compute_funnel_metrics` (the real caller of every
    `Storage` method) against `DynamoDbStorage`, not just individual methods
    in isolation."""
    from aic.public.events import compute_funnel_metrics

    storage.record_event("landing_visit")
    storage.record_event("landing_visit")
    storage.record_event("hero_cta_click")
    storage.create_registration(
        EarlyAccessRegistration(email="a@example.com", role="individual investor", qualified=True)
    )
    storage.create_registration(EarlyAccessRegistration(email="b@example.com"))
    storage.create_feedback(FeedbackSubmission(intended_use="Research"))

    metrics = compute_funnel_metrics(storage)

    assert metrics.landing_visits == 2
    assert metrics.cta_clicks == 1
    assert metrics.completed_registrations == 2
    assert metrics.qualified_registrations == 1
    assert metrics.feedback_submissions == 1
    assert metrics.cta_conversion_rate == pytest.approx(0.5)
    assert metrics.registration_conversion_rate == pytest.approx(1.0)
    assert metrics.qualified_interest_rate == pytest.approx(0.5)


def test_funnel_metrics_zero_denominator_cases(storage: DynamoDbStorage) -> None:
    from aic.public.events import compute_funnel_metrics

    metrics = compute_funnel_metrics(storage)

    assert metrics.cta_conversion_rate == 0.0
    assert metrics.registration_conversion_rate == 0.0
    assert metrics.qualified_interest_rate == 0.0
