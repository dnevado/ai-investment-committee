import os
import sqlite3
import threading
from datetime import UTC, datetime
from typing import Any, Protocol
from uuid import UUID

import boto3
from boto3.dynamodb.conditions import Attr, ConditionBase
from botocore.exceptions import ClientError

from aic.public.events import EventType, ValidationEvent
from aic.public.feedback import FeedbackSubmission
from aic.public.registration import EarlyAccessRegistration

_SCHEMA = """
CREATE TABLE IF NOT EXISTS registrations (
    registration_id TEXT PRIMARY KEY,
    email TEXT NOT NULL,
    email_normalized TEXT NOT NULL UNIQUE,
    name TEXT,
    role TEXT,
    experience TEXT,
    interests TEXT,
    feedback TEXT,
    qualified INTEGER NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS feedback_submissions (
    feedback_id TEXT PRIMARY KEY,
    intended_use TEXT,
    most_valuable_part TEXT,
    trust_blockers TEXT,
    regular_use TEXT,
    willing_to_pay TEXT,
    pre_conditions TEXT,
    email TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS validation_events (
    event_id TEXT PRIMARY KEY,
    event_type TEXT NOT NULL,
    device TEXT,
    source TEXT,
    created_at TEXT NOT NULL
);
"""


class Storage(Protocol):
    def create_registration(
        self, registration: EarlyAccessRegistration
    ) -> EarlyAccessRegistration: ...

    def create_feedback(self, feedback: FeedbackSubmission) -> FeedbackSubmission: ...

    def record_event(
        self,
        event_type: EventType,
        *,
        device: str | None = None,
        source: str | None = None,
    ) -> ValidationEvent: ...

    def count_events(
        self, event_type: str, since: datetime | None, until: datetime | None
    ) -> int: ...

    def count_events_grouped(
        self,
        event_type: str,
        group_by: str,
        since: datetime | None,
        until: datetime | None,
    ) -> dict[str, int]: ...

    def count_registrations(
        self,
        since: datetime | None,
        until: datetime | None,
        qualified_only: bool = False,
    ) -> int: ...

    def count_feedback(self, since: datetime | None, until: datetime | None) -> int: ...


def _row_to_registration(row: tuple) -> EarlyAccessRegistration:
    return EarlyAccessRegistration(
        registration_id=UUID(row[0]),
        email=row[1],
        name=row[3],
        role=row[4],
        experience=row[5],
        interests=row[6],
        feedback=row[7],
        qualified=bool(row[8]),
        created_at=datetime.fromisoformat(row[9]),
    )


class SqliteStorage:
    """A `Storage` implementation backed by a single, lock-serialized sqlite3
    connection. A single connection (rather than one per call) is required for
    `path=":memory:"` to preserve state across calls within a test; a lock keeps
    access safe when FastAPI dispatches sync endpoints to a thread pool."""

    def __init__(self, path: str = ":memory:") -> None:
        self._lock = threading.Lock()
        self._connection = sqlite3.connect(path, check_same_thread=False)
        with self._lock:
            self._connection.executescript(_SCHEMA)
            self._migrate_validation_events()
            self._connection.commit()

    def _migrate_validation_events(self) -> None:
        # `CREATE TABLE IF NOT EXISTS` leaves a pre-existing on-disk table
        # untouched, so a database created before `device`/`source` were
        # added to the schema needs those columns backfilled explicitly.
        existing = {
            row[1]
            for row in self._connection.execute("PRAGMA table_info(validation_events)")
        }
        for column in ("device", "source"):
            if column not in existing:
                self._connection.execute(
                    f"ALTER TABLE validation_events ADD COLUMN {column} TEXT"
                )

    def create_registration(
        self, registration: EarlyAccessRegistration
    ) -> EarlyAccessRegistration:
        normalized = registration.email.strip().lower()
        with self._lock:
            existing = self._connection.execute(
                "SELECT registration_id, email, email_normalized, name, role, "
                "experience, interests, feedback, qualified, created_at "
                "FROM registrations WHERE email_normalized = ?",
                (normalized,),
            ).fetchone()
            if existing is not None:
                return _row_to_registration(existing)

            self._connection.execute(
                "INSERT INTO registrations (registration_id, email, email_normalized, "
                "name, role, experience, interests, feedback, qualified, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    str(registration.registration_id),
                    registration.email,
                    normalized,
                    registration.name,
                    registration.role,
                    registration.experience,
                    registration.interests,
                    registration.feedback,
                    int(registration.qualified),
                    registration.created_at.isoformat(),
                ),
            )
            self._connection.commit()
        return registration

    def create_feedback(self, feedback: FeedbackSubmission) -> FeedbackSubmission:
        with self._lock:
            self._connection.execute(
                "INSERT INTO feedback_submissions (feedback_id, intended_use, "
                "most_valuable_part, trust_blockers, regular_use, willing_to_pay, "
                "pre_conditions, email, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    str(feedback.feedback_id),
                    feedback.intended_use,
                    feedback.most_valuable_part,
                    feedback.trust_blockers,
                    feedback.regular_use,
                    feedback.willing_to_pay,
                    feedback.pre_conditions,
                    feedback.email,
                    feedback.created_at.isoformat(),
                ),
            )
            self._connection.commit()
        return feedback

    def record_event(
        self,
        event_type: EventType,
        *,
        device: str | None = None,
        source: str | None = None,
    ) -> ValidationEvent:
        event = ValidationEvent(event_type=event_type, device=device, source=source)
        with self._lock:
            self._connection.execute(
                "INSERT INTO validation_events (event_id, event_type, device, source, "
                "created_at) VALUES (?, ?, ?, ?, ?)",
                (
                    str(event.event_id),
                    event.event_type,
                    event.device,
                    event.source,
                    event.created_at.isoformat(),
                ),
            )
            self._connection.commit()
        return event

    def count_events(
        self, event_type: str, since: datetime | None, until: datetime | None
    ) -> int:
        query = "SELECT COUNT(*) FROM validation_events WHERE event_type = ?"
        params: list[object] = [event_type]
        query, params = _apply_window(query, params, since, until)
        with self._lock:
            row = self._connection.execute(query, params).fetchone()
        return int(row[0])

    def count_events_grouped(
        self,
        event_type: str,
        group_by: str,
        since: datetime | None,
        until: datetime | None,
    ) -> dict[str, int]:
        if group_by not in {"device", "source"}:
            raise ValueError(f"Unsupported group_by column: {group_by}")
        query = (
            f"SELECT {group_by}, COUNT(*) FROM validation_events "
            "WHERE event_type = ?"
        )
        params: list[object] = [event_type]
        query, params = _apply_window(query, params, since, until)
        query += f" GROUP BY {group_by}"
        with self._lock:
            rows = self._connection.execute(query, params).fetchall()
        return {(row[0] or "unknown"): int(row[1]) for row in rows}

    def count_registrations(
        self,
        since: datetime | None,
        until: datetime | None,
        qualified_only: bool = False,
    ) -> int:
        query = "SELECT COUNT(*) FROM registrations WHERE 1 = 1"
        params: list[object] = []
        if qualified_only:
            query += " AND qualified = 1"
        query, params = _apply_window(query, params, since, until)
        with self._lock:
            row = self._connection.execute(query, params).fetchone()
        return int(row[0])

    def count_feedback(self, since: datetime | None, until: datetime | None) -> int:
        query = "SELECT COUNT(*) FROM feedback_submissions WHERE 1 = 1"
        params: list[object] = []
        query, params = _apply_window(query, params, since, until)
        with self._lock:
            row = self._connection.execute(query, params).fetchone()
        return int(row[0])


def _apply_window(
    query: str,
    params: list[object],
    since: datetime | None,
    until: datetime | None,
) -> tuple[str, list[object]]:
    if since is not None:
        query += " AND created_at >= ?"
        params.append(_to_utc_isoformat(since))
    if until is not None:
        query += " AND created_at <= ?"
        params.append(_to_utc_isoformat(until))
    return query, params


def _to_utc_isoformat(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.isoformat()


def _item_to_registration(item: dict[str, Any]) -> EarlyAccessRegistration:
    return EarlyAccessRegistration(
        registration_id=UUID(item["registration_id"]),
        email=item["email"],
        name=item.get("name"),
        role=item.get("role"),
        experience=item.get("experience"),
        interests=item.get("interests"),
        feedback=item.get("feedback"),
        qualified=bool(item.get("qualified", False)),
        created_at=datetime.fromisoformat(item["created_at"]),
    )


def _window_conditions(
    since: datetime | None, until: datetime | None
) -> list[ConditionBase]:
    conditions: list[ConditionBase] = []
    if since is not None:
        conditions.append(Attr("created_at").gte(_to_utc_isoformat(since)))
    if until is not None:
        conditions.append(Attr("created_at").lte(_to_utc_isoformat(until)))
    return conditions


def _combine_conditions(conditions: list[ConditionBase]) -> ConditionBase | None:
    if not conditions:
        return None
    combined = conditions[0]
    for condition in conditions[1:]:
        combined = combined & condition
    return combined


def _scan_all(table: Any, **scan_kwargs: Any) -> list[dict[str, Any]]:
    """Paginates through `table.scan(...)` until every matching item has been
    collected. Acceptable at this feature's traffic volume (spec.md frames
    this explicitly as a low-volume validation experiment, not a system
    requiring `Query`-level scale — research.md Decision 7)."""
    items: list[dict[str, Any]] = []
    kwargs = dict(scan_kwargs)
    while True:
        response = table.scan(**kwargs)
        items.extend(response.get("Items", []))
        last_key = response.get("LastEvaluatedKey")
        if not last_key:
            break
        kwargs["ExclusiveStartKey"] = last_key
    return items


def _scan_filtered(table: Any, conditions: list[ConditionBase]) -> list[dict[str, Any]]:
    filter_expression = _combine_conditions(conditions)
    if filter_expression is None:
        return _scan_all(table)
    return _scan_all(table, FilterExpression=filter_expression)


class DynamoDbStorage:
    """A `Storage` implementation backed by DynamoDB — production only (used
    exclusively by `lambda_handler.py`). Local development and every test use
    `SqliteStorage` instead; this class exists solely because spec.md forbids
    SQLite as the production persistence layer (FR-021). See data-model.md
    "Deployment revision, second" for the table designs and
    research.md Decision 7 for why three plain tables were chosen over a
    single-table design.

    `registrations` is keyed directly by `email_normalized` (not a generated
    ID) so the idempotent-registration requirement (FR-017) is a single
    atomic conditional `put_item` — no separate uniqueness index needed.
    """

    def __init__(
        self,
        *,
        registrations_table: str | None = None,
        feedback_table: str | None = None,
        events_table: str | None = None,
        region_name: str | None = None,
        resource: Any | None = None,
    ) -> None:
        dynamodb = resource or boto3.resource("dynamodb", region_name=region_name)
        self._registrations = dynamodb.Table(
            registrations_table
            or os.environ.get("QUORUM_REGISTRATIONS_TABLE", "quorum-registrations")
        )
        self._feedback = dynamodb.Table(
            feedback_table
            or os.environ.get(
                "QUORUM_FEEDBACK_TABLE", "quorum-feedback-submissions"
            )
        )
        self._events = dynamodb.Table(
            events_table
            or os.environ.get("QUORUM_EVENTS_TABLE", "quorum-validation-events")
        )

    def create_registration(
        self, registration: EarlyAccessRegistration
    ) -> EarlyAccessRegistration:
        normalized = registration.email.strip().lower()
        item: dict[str, Any] = {
            "email_normalized": normalized,
            "registration_id": str(registration.registration_id),
            "email": registration.email,
            "qualified": registration.qualified,
            "created_at": registration.created_at.isoformat(),
        }
        for field in ("name", "role", "experience", "interests", "feedback"):
            value = getattr(registration, field)
            if value is not None:
                item[field] = value

        try:
            self._registrations.put_item(
                Item=item,
                ConditionExpression="attribute_not_exists(email_normalized)",
            )
        except ClientError as exc:
            if exc.response["Error"]["Code"] != "ConditionalCheckFailedException":
                raise
            existing = self._registrations.get_item(
                Key={"email_normalized": normalized}
            )["Item"]
            return _item_to_registration(existing)
        return registration

    def create_feedback(self, feedback: FeedbackSubmission) -> FeedbackSubmission:
        item: dict[str, Any] = {
            "feedback_id": str(feedback.feedback_id),
            "created_at": feedback.created_at.isoformat(),
        }
        for field in (
            "intended_use",
            "most_valuable_part",
            "trust_blockers",
            "regular_use",
            "willing_to_pay",
            "pre_conditions",
            "email",
        ):
            value = getattr(feedback, field)
            if value is not None:
                item[field] = value
        self._feedback.put_item(Item=item)
        return feedback

    def record_event(
        self,
        event_type: EventType,
        *,
        device: str | None = None,
        source: str | None = None,
    ) -> ValidationEvent:
        event = ValidationEvent(event_type=event_type, device=device, source=source)
        item: dict[str, Any] = {
            "event_id": str(event.event_id),
            "event_type": event.event_type,
            "created_at": event.created_at.isoformat(),
        }
        if device is not None:
            item["device"] = device
        if source is not None:
            item["source"] = source
        self._events.put_item(Item=item)
        return event

    def count_events(
        self, event_type: str, since: datetime | None, until: datetime | None
    ) -> int:
        conditions = [Attr("event_type").eq(event_type), *_window_conditions(since, until)]
        return len(_scan_filtered(self._events, conditions))

    def count_events_grouped(
        self,
        event_type: str,
        group_by: str,
        since: datetime | None,
        until: datetime | None,
    ) -> dict[str, int]:
        if group_by not in {"device", "source"}:
            raise ValueError(f"Unsupported group_by column: {group_by}")
        conditions = [Attr("event_type").eq(event_type), *_window_conditions(since, until)]
        items = _scan_filtered(self._events, conditions)
        counts: dict[str, int] = {}
        for item in items:
            key = item.get(group_by) or "unknown"
            counts[key] = counts.get(key, 0) + 1
        return counts

    def count_registrations(
        self,
        since: datetime | None,
        until: datetime | None,
        qualified_only: bool = False,
    ) -> int:
        conditions = _window_conditions(since, until)
        if qualified_only:
            conditions.append(Attr("qualified").eq(True))
        return len(_scan_filtered(self._registrations, conditions))

    def count_feedback(self, since: datetime | None, until: datetime | None) -> int:
        return len(_scan_filtered(self._feedback, _window_conditions(since, until)))
