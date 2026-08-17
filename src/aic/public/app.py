import os
from datetime import datetime
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError

from aic.public.events import compute_funnel_metrics
from aic.public.feedback import FeedbackSubmission
from aic.public.presentation import AmazonPresentation
from aic.public.registration import EarlyAccessRegistration, classify_qualified
from aic.public.storage import SqliteStorage, Storage

_PACKAGE_DIR = Path(__file__).resolve().parent
_DEFAULT_SNAPSHOT_PATH = _PACKAGE_DIR.parent.parent.parent / "data" / "amazon_snapshot.json"
# In Lambda, this module's own `app = create_app()` below runs as an
# unavoidable import-time side effect (importing anything under aic.public
# initializes this module) even though lambda_handler.py always passes its
# own DynamoDbStorage explicitly — Lambda's filesystem is read-only except
# /tmp, so the plain repo-relative default path would crash module import
# with "unable to open database file" before lambda_handler.py's override
# ever gets a chance to matter. AWS_LAMBDA_FUNCTION_NAME is a standard,
# always-set Lambda environment variable, used here only to pick a writable
# throwaway path; local/test behavior (that variable is unset) is unchanged.
_DEFAULT_DB_PATH = (
    Path("/tmp/public.db")
    if os.environ.get("AWS_LAMBDA_FUNCTION_NAME")
    else _PACKAGE_DIR.parent.parent.parent / "data" / "public.db"
)


def _load_default_presentation() -> AmazonPresentation:
    return AmazonPresentation.model_validate_json(
        _DEFAULT_SNAPSHOT_PATH.read_text(encoding="utf-8")
    )


def _classify_device(user_agent: str | None) -> str:
    if not user_agent:
        return "unknown"
    lowered = user_agent.lower()
    if any(token in lowered for token in ("mobi", "android", "iphone")):
        return "mobile"
    if "ipad" in lowered or "tablet" in lowered:
        return "tablet"
    return "desktop"


def create_app(
    *,
    storage: Storage | None = None,
    presentation: AmazonPresentation | None = None,
) -> FastAPI:
    app = FastAPI(title="AI Investment Committee")

    resolved_storage: Storage = storage or SqliteStorage(str(_DEFAULT_DB_PATH))
    resolved_presentation = presentation or _load_default_presentation()

    templates = Jinja2Templates(directory=str(_PACKAGE_DIR / "templates"))
    app.mount("/static", StaticFiles(directory=str(_PACKAGE_DIR / "static")), name="static")

    app.state.storage = resolved_storage
    app.state.presentation = resolved_presentation

    @app.get("/", response_class=HTMLResponse)
    def landing(request: Request, src: str | None = None) -> HTMLResponse:
        device = _classify_device(request.headers.get("user-agent"))
        resolved_storage.record_event("landing_visit", device=device, source=src)
        return templates.TemplateResponse(
            request, "landing.html", {"presentation": resolved_presentation}
        )

    @app.post("/events")
    def track_event(payload: dict[str, str]) -> dict[str, str]:
        event_type = payload.get("event_type")
        allowed: set[str] = {
            "hero_cta_click",
            "workflow_cta_click",
            "example_cta_click",
            "final_cta_click",
            "demo_view",
            "demo_interaction",
            "signup_started",
        }
        if event_type in allowed:
            resolved_storage.record_event(event_type)  # type: ignore[arg-type]
        return {"status": "accepted"}

    @app.get("/register", response_class=HTMLResponse)
    def register_form(request: Request) -> HTMLResponse:
        return templates.TemplateResponse(request, "register.html", {"error": None})

    @app.post("/register", response_model=None)
    def register_submit(
        request: Request,
        email: Annotated[str, Form()],
        name: Annotated[str | None, Form()] = None,
        role: Annotated[str | None, Form()] = None,
        experience: Annotated[str | None, Form()] = None,
        interests: Annotated[str | None, Form()] = None,
        feedback: Annotated[str | None, Form()] = None,
    ) -> HTMLResponse | RedirectResponse:
        try:
            registration = EarlyAccessRegistration(
                email=email,  # type: ignore[arg-type]
                name=name,
                role=role,
                experience=experience,
                interests=interests,
                feedback=feedback,
                qualified=classify_qualified(role),
            )
        except ValidationError:
            return templates.TemplateResponse(
                request,
                "register.html",
                {"error": "Please enter a valid email address."},
                status_code=422,
            )

        resolved_storage.create_registration(registration)
        resolved_storage.record_event("signup_completed")
        resolved_storage.record_event("early_access_requested")
        return RedirectResponse(url="/register/confirmation", status_code=303)

    @app.get("/register/confirmation", response_class=HTMLResponse)
    def register_confirmation(request: Request) -> HTMLResponse:
        return templates.TemplateResponse(request, "register_confirmation.html", {})

    @app.get("/feedback", response_class=HTMLResponse)
    def feedback_form(request: Request) -> HTMLResponse:
        return templates.TemplateResponse(request, "feedback.html", {"error": None})

    @app.post("/feedback", response_model=None)
    def feedback_submit(
        request: Request,
        intended_use: Annotated[str | None, Form()] = None,
        most_valuable_part: Annotated[str | None, Form()] = None,
        trust_blockers: Annotated[str | None, Form()] = None,
        regular_use: Annotated[str | None, Form()] = None,
        willing_to_pay: Annotated[str | None, Form()] = None,
        pre_conditions: Annotated[str | None, Form()] = None,
        email: Annotated[str | None, Form()] = None,
    ) -> HTMLResponse | RedirectResponse:
        try:
            submission = FeedbackSubmission(
                intended_use=intended_use,
                most_valuable_part=most_valuable_part,
                trust_blockers=trust_blockers,
                regular_use=regular_use,
                willing_to_pay=willing_to_pay,
                pre_conditions=pre_conditions,
                email=email,  # type: ignore[arg-type]
            )
        except ValidationError:
            return templates.TemplateResponse(
                request,
                "feedback.html",
                {"error": "Please answer at least one question."},
                status_code=422,
            )

        resolved_storage.create_feedback(submission)
        return RedirectResponse(url="/feedback/confirmation", status_code=303)

    @app.get("/feedback/confirmation", response_class=HTMLResponse)
    def feedback_confirmation(request: Request) -> HTMLResponse:
        return templates.TemplateResponse(request, "feedback_confirmation.html", {})

    @app.get("/metrics")
    def metrics(since: datetime | None = None, until: datetime | None = None) -> dict:
        return compute_funnel_metrics(resolved_storage, since, until).model_dump(mode="json")

    return app


app = create_app()
