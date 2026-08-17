# Contract: `aic.public` HTTP Interface

This feature's interface is a small FastAPI application (`aic.public.app:app`). Every route
below is defined once, in `app.py`, and is unchanged by *how* it's invoked: directly by
`uvicorn` locally, or via `Mangum` inside AWS Lambda in production (plan.md "Deployment
Technical Context", research.md Decision 7) — the request/response contract described here
is identical either way.

## Routes

### `GET /`

Renders the landing page: brand/value proposition (FR-001), plain-language workflow
explanation (FR-002), the Amazon example (FR-003/FR-004/FR-005), primary and secondary
CTAs (FR-006), and disclaimer text adjacent to the example and the CTA (FR-012).

- MUST synchronously record one `landing_visit` `ValidationEvent` per request, server-side
  — not dependent on client-side JS, so it is not affected by ad blockers (spec Edge Case).
- MUST NOT make any LLM/network call — content is rendered entirely from the loaded
  `AmazonPresentation` snapshot.
- Response: `text/html`.

**Deployment note (2026-08-16)**: In production this route is not invoked live at all — it
is the *source* for `scripts/build_static_site.py`'s one-time render, which is what S3/
CloudFront actually serve (research.md Decision 7). The server-side `landing_visit`
recording this route performs therefore never fires per real visitor in production;
research.md Decision 9 resolves this by adding a `landing_visit` client-side beacon (same
mechanism `track.js` already uses for other events) for production specifically. Locally
(`uvicorn`), this route still records the event exactly as written, so `test_get_landing_
page_records_one_landing_visit_event` remains accurate for local/test behavior.

### `POST /events`

Client-side beacon for events that only make sense as a user interaction (CTA click, demo
view/interaction, signup started). Body: `{"event_type": "hero_cta_click" | "demo_view" |
"demo_interaction" | "signup_started"}` (the literal set minus the two events recorded
server-side by their own routes: `landing_visit`, `signup_completed`).

- MUST record one `ValidationEvent` of the given type.
- MUST respond `202 Accepted` with an empty body even on validation failure of the event
  type itself (best-effort; a malformed/blocked beacon MUST NOT surface an error to the
  visitor or block any other action — spec Edge Case: "analytics failure must not block the
  core funnel actions").

### `GET /register`

Renders the registration form (email required; name, role, experience, interests, feedback
all optional — FR-007/FR-008). MAY fire a `signup_started` event via the same `/events`
beacon from the page's own script, or the caller MAY POST it directly before navigating
here; either is acceptable, this route itself does not record an event server-side.

### `POST /register`

Body (form-encoded, matching a plain HTML `<form>` — no JS required for the core action):
`email` (required), `name`, `role`, `experience`, `interests`, `feedback` (all optional).

- MUST reject a syntactically invalid email with `422` and re-render the form with a clear
  error message — no row is written (spec US3/AC3).
- MUST classify `qualified` from `role` per research.md Decision 4 and persist it.
- MUST treat a resubmission with an email already on file (case-insensitive) as
  idempotent: it MUST NOT create a second row and MUST NOT be double-counted in
  `completed_registrations` (FR-017) — implemented via the `email_normalized UNIQUE`
  constraint locally (`SqliteStorage`) and via a conditional `put_item` keyed on
  `email_normalized` in production (`DynamoDbStorage`); same guarantee, storage-specific
  mechanism (data-model.md).
- On success: MUST record one `signup_completed` and one `early_access_requested`
  `ValidationEvent`, MUST NOT create any authentication session or account (FR-008), and
  MUST redirect (`303 See Other`) to a confirmation page making clear the visitor has
  joined an early-access/validation program, not a live product (spec US3/AC2).

### `GET /feedback`

Renders the six-question feedback form (US4/AC1), independent of registration status.

### `POST /feedback`

Body (form-encoded): the six answer fields (all individually optional) and an optional
`email`.

- MUST reject a submission where all six answer fields are blank (data-model.md validation
  rule) with `422` and a clear message; MUST NOT require a prior registration to succeed
  (spec Edge Case, FR-018).
- On success: MUST persist one `FeedbackSubmission` row and redirect to a thank-you
  confirmation.

### `GET /metrics`

Operator-facing (not linked from the public page). Query params: optional `since`/`until`
(ISO 8601); defaults to all-time. Returns `FunnelMetrics` as JSON (data-model.md), computed
live from storage — three SQLite tables locally, three DynamoDB tables in production
(`Scan` with filters — data-model.md) — nothing pre-aggregated or cached, so it always
reflects current data. No authentication is added for this route in this feature (spec
Non-Goals rule out complex auth).

**Deployment note (2026-08-16, updated)**: This route is reachable through CloudFront (path
prefix `/metrics*` → Lambda, research.md Decision 7) with no credential check — anyone with
the URL can read funnel counts (no PII beyond what registrations/feedback already store
server-side; the route returns aggregate counts and rates only, not individual rows). This
is an accepted, explicit tradeoff for "simple," matching this feature's Non-Goal of no
complex auth — not a silent gap. If this becomes a concern, the smallest fix is a
shared-secret header/query param checked inside the existing route handler (`app.py`), or a
CloudFront Function on the `/metrics*` behavior — either needs no new AWS service; this was
not added by default since spec.md did not request it.

## Non-goals of this contract

- No JSON REST API beyond `/events` (best-effort beacon) and `/metrics` (operator read) —
  the visitor-facing routes are plain server-rendered HTML forms, functional with
  JavaScript disabled except for the non-blocking analytics beacon.
- No authentication, session, or account creation anywhere in this contract (FR-008).
- No route recomputes or calls into `aic.workflow`/`aic.research`/etc. — every route only
  reads the static snapshot and/or reads/writes the three storage tables (SQLite locally,
  DynamoDB in production — data-model.md).
- No route exposes raw internal Pydantic `model_dump()` output of `WorkflowResult` or any
  `aic.domain`/`aic.dcf` type — only the `AmazonPresentation` read model (FR-004: "no raw
  Python/Pydantic object representations").
