from datetime import date

import pytest
from fastapi.testclient import TestClient

from aic.public.app import create_app
from aic.public.presentation import AmazonPresentation, EvidenceItemView
from aic.public.storage import SqliteStorage


def _presentation() -> AmazonPresentation:
    return AmazonPresentation(
        company_name="Amazon.com, Inc.",
        ticker="AMZN",
        implied_value_per_share="$75.07",
        enterprise_value="$843.19B",
        equity_value="$813.23B",
        recommendation="WATCH",
        conviction=0.82,
        thesis_summary="Durable moat in cloud and advertising.",
        bull_summary="Structural growth supports upside.",
        bear_summary="Valuation already prices in growth.",
        key_assumptions=["Cloud demand persists"],
        key_risks=["Margin compression"],
        evidence=[
            EvidenceItemView(
                title="FY2025 revenue",
                excerpt="Revenue increased 12%.",
                classification="Reported fact",
                source="10-K",
                reference=None,
            ),
            EvidenceItemView(
                title="Forecast margin",
                excerpt="Model assumes 12% operating margin.",
                classification="Forecast assumption",
                source="Analyst commentary",
                reference=None,
            ),
        ],
        captured_at=date(2026, 8, 15),
    )


@pytest.fixture
def client() -> TestClient:
    app = create_app(storage=SqliteStorage(":memory:"), presentation=_presentation())
    return TestClient(app)


# --- User Story 1: value proposition ----------------------------------------


def test_get_landing_page_returns_value_proposition(client: TestClient) -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert "Quorum" in response.text
    assert "evidence-backed" in response.text.lower()


def test_get_landing_page_records_one_landing_visit_event(client: TestClient) -> None:
    storage: SqliteStorage = client.app.state.storage  # type: ignore[attr-defined]

    client.get("/")

    assert storage.count_events("landing_visit", None, None) == 1

    client.get("/")

    assert storage.count_events("landing_visit", None, None) == 2


# --- User Story 2: trustworthy Amazon example -------------------------------


def test_get_landing_page_shows_amazon_example_in_human_readable_form(
    client: TestClient,
) -> None:
    response = client.get("/")

    assert "$75.07" in response.text
    assert "WATCH" in response.text
    assert "AMAZON.COM, INC." in response.text  # case-header, styled uppercase
    assert "Reported fact" in response.text
    assert "Forecast assumption" in response.text
    assert "AmazonPresentation(" not in response.text
    assert "object at 0x" not in response.text


# --- User Story 3: registration ---------------------------------------------


def test_post_register_with_only_email_redirects_to_confirmation(
    client: TestClient,
) -> None:
    response = client.post("/register", data={"email": "visitor@example.com"})

    assert response.status_code == 200
    assert "validation group" in response.text.lower()


def test_post_register_with_malformed_email_returns_422(client: TestClient) -> None:
    response = client.post(
        "/register", data={"email": "not-an-email"}, follow_redirects=False
    )

    assert response.status_code == 422
    assert "valid email" in response.text.lower()


def test_post_register_duplicate_email_is_not_double_counted(client: TestClient) -> None:
    client.post("/register", data={"email": "visitor@example.com"})
    client.post("/register", data={"email": "Visitor@Example.com"})

    storage: SqliteStorage = client.app.state.storage  # type: ignore[attr-defined]
    assert storage.count_registrations(None, None) == 1


def test_post_register_creates_no_auth_cookie_or_session(client: TestClient) -> None:
    response = client.post(
        "/register", data={"email": "visitor@example.com"}, follow_redirects=False
    )

    assert "set-cookie" not in {k.lower() for k in response.headers}


# --- User Story 4: feedback --------------------------------------------------


def test_post_feedback_succeeds_without_prior_registration(client: TestClient) -> None:
    response = client.post("/feedback", data={"intended_use": "Research screening"})

    assert response.status_code == 200
    storage: SqliteStorage = client.app.state.storage  # type: ignore[attr-defined]
    assert storage.count_feedback(None, None) == 1
    assert storage.count_registrations(None, None) == 0


def test_post_feedback_all_blank_returns_422(client: TestClient) -> None:
    response = client.post("/feedback", data={}, follow_redirects=False)

    assert response.status_code == 422


# --- User Story 5: funnel measurement ---------------------------------------


def test_post_events_always_returns_202_or_200_even_for_unknown_type(
    client: TestClient,
) -> None:
    response = client.post("/events", json={"event_type": "not_a_real_event"})

    assert response.status_code < 300
    storage: SqliteStorage = client.app.state.storage  # type: ignore[attr-defined]
    assert storage.count_events("not_a_real_event", None, None) == 0


def test_get_metrics_reflects_recorded_activity(client: TestClient) -> None:
    client.get("/")
    client.post("/events", json={"event_type": "hero_cta_click"})
    client.post("/register", data={"email": "visitor@example.com"})

    response = client.get("/metrics")

    assert response.status_code == 200
    body = response.json()
    assert body["landing_visits"] == 1
    assert body["cta_clicks"] == 1
    assert body["completed_registrations"] == 1
    assert body["registration_conversion_rate"] == 1.0


def test_landing_page_has_primary_and_secondary_cta_tracking_points(
    client: TestClient,
) -> None:
    """"Get early access" is the single primary-action label used
    consistently everywhere it appears (persistent nav, hero, closing
    section) — no competing CTA language. Secondary actions ("Explore the
    Amazon case", "View the complete evidence trail") are deliberately
    distinct, lower-weight text links rather than alternate primary-CTA
    phrasing. `example_cta_click`/`workflow_cta_click` remain valid event
    types (storage/analytics schema unchanged) but are deliberately unused
    on this page."""
    response = client.get("/")

    assert 'data-track="hero_cta_click"' in response.text
    assert 'data-track="final_cta_click"' in response.text
    assert 'data-track="demo_view"' in response.text
    assert response.text.count("Get early access") == 3  # nav + hero + closing
    assert "Explore the Amazon case" in response.text
    assert "View the complete evidence trail" in response.text


def test_landing_visit_classifies_mobile_device(client: TestClient) -> None:
    client.get(
        "/",
        headers={
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)"
        },
    )

    storage: SqliteStorage = client.app.state.storage  # type: ignore[attr-defined]
    grouped = storage.count_events_grouped("landing_visit", "device", None, None)
    assert grouped == {"mobile": 1}


def test_landing_visit_classifies_desktop_device_by_default(client: TestClient) -> None:
    client.get("/", headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})

    storage: SqliteStorage = client.app.state.storage  # type: ignore[attr-defined]
    grouped = storage.count_events_grouped("landing_visit", "device", None, None)
    assert grouped == {"desktop": 1}


def test_landing_visit_records_acquisition_source_from_query_param(
    client: TestClient,
) -> None:
    client.get("/?src=newsletter")

    storage: SqliteStorage = client.app.state.storage  # type: ignore[attr-defined]
    grouped = storage.count_events_grouped("landing_visit", "source", None, None)
    assert grouped == {"newsletter": 1}


def test_post_events_records_positional_cta_clicks(client: TestClient) -> None:
    for event_type in ("workflow_cta_click", "example_cta_click", "final_cta_click"):
        response = client.post("/events", json={"event_type": event_type})
        assert response.status_code < 300

    storage: SqliteStorage = client.app.state.storage  # type: ignore[attr-defined]
    assert storage.count_events("workflow_cta_click", None, None) == 1
    assert storage.count_events("example_cta_click", None, None) == 1
    assert storage.count_events("final_cta_click", None, None) == 1


# --- User Story 6: trust and disclaimer messaging ---------------------------


def test_landing_page_shows_disclaimer_near_example(client: TestClient) -> None:
    response = client.get("/")

    assert "not financial advice" in response.text.lower()


def test_register_page_shows_disclaimer_near_cta(client: TestClient) -> None:
    response = client.get("/register")

    assert "not financial advice" in response.text.lower()


@pytest.mark.parametrize("path", ["/", "/register", "/feedback"])
def test_no_guaranteed_return_language_anywhere(client: TestClient, path: str) -> None:
    """Bans promotional phrases that promise returns — distinct from the
    disclaimer's legitimate, negating use of "guaranteed" ("no results are
    guaranteed"), which is exactly the required FR-012 messaging, not a
    violation of it."""
    response = client.get(path)
    lowered = response.text.lower()

    banned_phrases = (
        "guaranteed return",
        "guaranteed profit",
        "guaranteed income",
        "guaranteed gains",
        "get rich",
        "revolutionizing",
    )
    for banned_phrase in banned_phrases:
        assert banned_phrase not in lowered
