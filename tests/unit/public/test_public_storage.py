import sqlite3

from aic.public.feedback import FeedbackSubmission
from aic.public.registration import EarlyAccessRegistration
from aic.public.storage import SqliteStorage


def test_registration_round_trips() -> None:
    storage = SqliteStorage(":memory:")
    registration = EarlyAccessRegistration(email="visitor@example.com", name="Alex", qualified=True)

    stored = storage.create_registration(registration)

    assert stored.registration_id == registration.registration_id
    assert storage.count_registrations(None, None) == 1
    assert storage.count_registrations(None, None, qualified_only=True) == 1


def test_feedback_round_trips() -> None:
    storage = SqliteStorage(":memory:")
    submission = FeedbackSubmission(intended_use="Research")

    storage.create_feedback(submission)

    assert storage.count_feedback(None, None) == 1


def test_event_round_trips() -> None:
    storage = SqliteStorage(":memory:")

    storage.record_event("landing_visit")

    assert storage.count_events("landing_visit", None, None) == 1


def test_duplicate_email_registration_does_not_create_second_row() -> None:
    storage = SqliteStorage(":memory:")

    first = storage.create_registration(EarlyAccessRegistration(email="Visitor@Example.com"))
    second = storage.create_registration(EarlyAccessRegistration(email="visitor@example.com"))

    assert first.registration_id == second.registration_id
    assert storage.count_registrations(None, None) == 1


def test_event_records_optional_device_and_source() -> None:
    storage = SqliteStorage(":memory:")

    event = storage.record_event("landing_visit", device="mobile", source="twitter")

    assert event.device == "mobile"
    assert event.source == "twitter"


def test_count_events_grouped_by_device() -> None:
    storage = SqliteStorage(":memory:")
    storage.record_event("landing_visit", device="mobile")
    storage.record_event("landing_visit", device="mobile")
    storage.record_event("landing_visit", device="desktop")
    storage.record_event("landing_visit")  # no device recorded

    grouped = storage.count_events_grouped("landing_visit", "device", None, None)

    assert grouped == {"mobile": 2, "desktop": 1, "unknown": 1}


def test_count_events_grouped_by_source() -> None:
    storage = SqliteStorage(":memory:")
    storage.record_event("landing_visit", source="twitter")
    storage.record_event("landing_visit", source="newsletter")

    grouped = storage.count_events_grouped("landing_visit", "source", None, None)

    assert grouped == {"twitter": 1, "newsletter": 1}


def test_migrates_pre_existing_database_missing_device_and_source_columns(
    tmp_path,
) -> None:
    db_path = tmp_path / "legacy.db"
    legacy_connection = sqlite3.connect(str(db_path))
    legacy_connection.execute(
        "CREATE TABLE validation_events ("
        "event_id TEXT PRIMARY KEY, event_type TEXT NOT NULL, created_at TEXT NOT NULL)"
    )
    legacy_connection.execute(
        "INSERT INTO validation_events VALUES ('e1', 'landing_visit', '2026-01-01T00:00:00+00:00')"
    )
    legacy_connection.commit()
    legacy_connection.close()

    storage = SqliteStorage(str(db_path))
    event = storage.record_event("landing_visit", device="mobile", source="twitter")

    assert event.device == "mobile"
    assert event.source == "twitter"
    assert storage.count_events("landing_visit", None, None) == 2
