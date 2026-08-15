from datetime import UTC, datetime
from typing import TYPE_CHECKING, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from aic.public.storage import Storage

EventType = Literal[
    "landing_visit",
    "hero_cta_click",
    "workflow_cta_click",
    "example_cta_click",
    "final_cta_click",
    "demo_view",
    "demo_interaction",
    "signup_started",
    "signup_completed",
    "early_access_requested",
]

CTA_EVENT_TYPES: tuple[EventType, ...] = (
    "hero_cta_click",
    "workflow_cta_click",
    "example_cta_click",
    "final_cta_click",
)


class ValidationEvent(BaseModel):
    event_id: UUID = Field(default_factory=uuid4)
    event_type: EventType
    device: str | None = None
    source: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class FunnelMetrics(BaseModel):
    window_start: datetime | None
    window_end: datetime | None
    landing_visits: int
    cta_clicks: int
    cta_clicks_by_position: dict[str, int]
    completed_registrations: int
    qualified_registrations: int
    feedback_submissions: int
    cta_conversion_rate: float
    registration_conversion_rate: float
    qualified_interest_rate: float
    landing_visits_by_device: dict[str, int]
    landing_visits_by_source: dict[str, int]


def compute_funnel_metrics(
    storage: "Storage",
    since: datetime | None = None,
    until: datetime | None = None,
) -> FunnelMetrics:
    landing_visits = storage.count_events("landing_visit", since, until)

    cta_clicks_by_position: dict[str, int] = {
        str(event_type): storage.count_events(event_type, since, until)
        for event_type in CTA_EVENT_TYPES
    }
    cta_clicks = sum(cta_clicks_by_position.values())

    completed_registrations = storage.count_registrations(since, until)
    qualified_registrations = storage.count_registrations(since, until, qualified_only=True)
    feedback_submissions = storage.count_feedback(since, until)

    cta_conversion_rate = (cta_clicks / landing_visits) if landing_visits else 0.0
    registration_conversion_rate = (
        (completed_registrations / landing_visits) if landing_visits else 0.0
    )
    qualified_interest_rate = (
        (qualified_registrations / completed_registrations)
        if completed_registrations
        else 0.0
    )

    return FunnelMetrics(
        window_start=since,
        window_end=until,
        landing_visits=landing_visits,
        cta_clicks=cta_clicks,
        cta_clicks_by_position=cta_clicks_by_position,
        completed_registrations=completed_registrations,
        qualified_registrations=qualified_registrations,
        feedback_submissions=feedback_submissions,
        cta_conversion_rate=cta_conversion_rate,
        registration_conversion_rate=registration_conversion_rate,
        qualified_interest_rate=qualified_interest_rate,
        landing_visits_by_device=storage.count_events_grouped(
            "landing_visit", "device", since, until
        ),
        landing_visits_by_source=storage.count_events_grouped(
            "landing_visit", "source", since, until
        ),
    )
