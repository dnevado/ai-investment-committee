from aic.public.events import compute_funnel_metrics
from aic.public.registration import EarlyAccessRegistration, classify_qualified
from aic.public.storage import SqliteStorage


def test_each_event_type_records_correctly() -> None:
    storage = SqliteStorage(":memory:")

    storage.record_event("landing_visit")
    storage.record_event("hero_cta_click")
    storage.record_event("demo_view")

    assert storage.count_events("landing_visit", None, None) == 1
    assert storage.count_events("hero_cta_click", None, None) == 1
    assert storage.count_events("demo_view", None, None) == 1
    assert storage.count_events("demo_interaction", None, None) == 0


def test_compute_funnel_metrics_computes_all_three_rates() -> None:
    storage = SqliteStorage(":memory:")

    for _ in range(10):
        storage.record_event("landing_visit")
    for _ in range(4):
        storage.record_event("hero_cta_click")

    for email, role in [
        ("a@example.com", "individual investor"),
        ("b@example.com", "curious hobbyist"),
        ("c@example.com", None),
    ]:
        storage.create_registration(
            EarlyAccessRegistration(email=email, role=role, qualified=classify_qualified(role))
        )

    metrics = compute_funnel_metrics(storage)

    assert metrics.landing_visits == 10
    assert metrics.cta_clicks == 4
    assert metrics.completed_registrations == 3
    assert metrics.qualified_registrations == 1
    assert metrics.cta_conversion_rate == 0.4
    assert metrics.registration_conversion_rate == 0.3
    assert metrics.qualified_interest_rate == 1 / 3


def test_compute_funnel_metrics_handles_zero_denominators() -> None:
    storage = SqliteStorage(":memory:")

    metrics = compute_funnel_metrics(storage)

    assert metrics.landing_visits == 0
    assert metrics.completed_registrations == 0
    assert metrics.cta_conversion_rate == 0.0
    assert metrics.registration_conversion_rate == 0.0
    assert metrics.qualified_interest_rate == 0.0
    assert metrics.cta_clicks_by_position == {
        "hero_cta_click": 0,
        "workflow_cta_click": 0,
        "example_cta_click": 0,
        "final_cta_click": 0,
    }
    assert metrics.landing_visits_by_device == {}
    assert metrics.landing_visits_by_source == {}


def test_compute_funnel_metrics_breaks_down_cta_clicks_by_position() -> None:
    storage = SqliteStorage(":memory:")
    storage.record_event("hero_cta_click")
    storage.record_event("hero_cta_click")
    storage.record_event("workflow_cta_click")
    storage.record_event("example_cta_click")
    storage.record_event("final_cta_click")

    metrics = compute_funnel_metrics(storage)

    assert metrics.cta_clicks == 5
    assert metrics.cta_clicks_by_position == {
        "hero_cta_click": 2,
        "workflow_cta_click": 1,
        "example_cta_click": 1,
        "final_cta_click": 1,
    }


def test_compute_funnel_metrics_breaks_down_visits_by_device_and_source() -> None:
    storage = SqliteStorage(":memory:")
    storage.record_event("landing_visit", device="mobile", source="twitter")
    storage.record_event("landing_visit", device="desktop", source="twitter")
    storage.record_event("landing_visit", device="desktop")

    metrics = compute_funnel_metrics(storage)

    assert metrics.landing_visits_by_device == {"mobile": 1, "desktop": 2}
    assert metrics.landing_visits_by_source == {"twitter": 2, "unknown": 1}
