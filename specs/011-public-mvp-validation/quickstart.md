# Quickstart: Public MVP Validation

## Prerequisites

- Repo dependencies installed, including this feature's new ones (`fastapi`, `uvicorn`,
  `jinja2`, `python-multipart`).
- For the snapshot-capture step only: `AIC_OPENAI_API_KEY` configured (`.env`). Running the
  public app itself requires **no** OpenAI credentials — see research.md Decision 2.

## 1. Capture the Amazon snapshot (manual, one real OpenAI call sequence, optional if `data/amazon_snapshot.json` already exists)

```sh
uv run python scripts/capture_amazon_snapshot.py
```

Expected: prints a summary and writes `data/amazon_snapshot.json` containing the
`AmazonPresentation` fields (implied value/share, recommendation, conviction, thesis/bull/
bear summaries, key assumptions/risks, evidence list with FACT/CALCULATION/ASSUMPTION/AI
labels) — matching feature 010's validated Amazon output ($75.07/share, WATCH, etc., unless
the underlying dataset/assumptions have since changed).

## 2. Automated validation (no network)

```sh
pytest tests/unit/public/ -v
```

Expected outcomes:

- `test_public_presentation.py`: `AmazonPresentation` builds correctly from a fixture
  `WorkflowResult` (or loads correctly from a fixture JSON snapshot); evidence
  classification labels map FACT/CALCULATION/ASSUMPTION/INTERPRETATION/OPINION correctly.
- `test_public_registration.py`: valid email + all-optional-blank succeeds; invalid email
  rejected; duplicate email does not create a second row; `qualified` classification
  matches research.md Decision 4's rule.
- `test_public_feedback.py`: all-blank submission rejected; any single non-blank answer
  accepted; succeeds with no associated registration.
- `test_public_events.py`: each event type records correctly; `FunnelMetrics`'s three rates
  compute correctly against a small constructed set of events/registrations, including the
  zero-denominator edge cases (0 visits, 0 registrations).
- `test_public_storage.py`: `SqliteStorage` (in-memory) round-trips all three entity types.
- `test_public_app.py` (FastAPI `TestClient`): `GET /` returns 200 and includes the Amazon
  example's key figures in human-readable HTML (not raw object repr); `POST /register` with
  only an email succeeds and redirects; a malformed email is rejected with 422; `POST
  /feedback` succeeds independent of registration; `GET /metrics` returns the expected
  JSON shape.

Then confirm the rest of the suite — including every pre-existing package — is unaffected:

```sh
pytest
ruff check .
mypy src
```

Expected: same pass count as before this feature (221, per feature 010) plus this
feature's new tests, no ruff/mypy errors, and zero changes to any test outcome in
`tests/unit/dcf/`, `tests/unit/research/`, `tests/unit/bullbear/`, `tests/unit/committee/`,
`tests/unit/report/`, or `tests/unit/workflow/` (FR-016/SC-007).

## 3. Manual end-to-end walkthrough (local server, no real OpenAI call needed)

```sh
uv run uvicorn aic.public.app:app --reload
```

Then, in a browser at `http://127.0.0.1:8000/`:

1. Confirm the hero states what Quorum is and who it's for without scrolling (US1/SC-001).
2. Confirm the "Real-World Validation" section shows company identity, implied
   value/share, recommendation, and conviction, and that expanding "See the case" shows
   the condensed thesis and bull/bear cases; confirm the Evidence section's sample table
   shows items labeled fact/calculation/assumption (US2/SC-002).
3. Confirm disclaimer text is visible near the case detail and near the registration CTA
   (US6/SC-006).
4. Click the primary CTA, submit the registration form with only an email, and confirm a
   confirmation page appears stating this is early access, not a live product (US3/SC-003).
5. Submit the same email again and confirm no error is shown and no second registration is
   created (check via `GET /metrics` before/after — `completed_registrations` unchanged).
6. Open the feedback form directly (without registering first) and submit at least one
   answer; confirm it succeeds (US4).
7. `GET /metrics` and confirm `landing_visits`, `cta_clicks` (if the CTA-click beacon
   fired), `completed_registrations`, `qualified_registrations`, `feedback_submissions`,
   and the three computed rates are all present and consistent with the actions taken
   above (US5/SC-004).

## Non-goal reminder

This quickstart does not cover live public deployment (domain, TLS, real hosting) — that is
explicitly out of this plan's scope (research.md Decision 6).
