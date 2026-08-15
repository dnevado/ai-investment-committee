# Research: Public MVP Validation

## Decision 1: Web framework — FastAPI + Jinja2, not a separate frontend stack

**Decision**: Use FastAPI (ASGI) with Jinja2 server-rendered HTML templates and minimal
vanilla CSS/JS for the registration/feedback forms. No SPA framework, no JS build
toolchain, no separate frontend project.

**Rationale**: FastAPI is built directly on Pydantic, which is already this project's core
dependency and validation mechanism (constitution Principle III: "Structured Outputs
Only") — request/response schemas for registration and feedback reuse the exact same
`BaseModel` discipline used throughout `aic.domain`/`aic.research`/etc., so no new
validation paradigm is introduced. `httpx` (needed for FastAPI's `TestClient`) is already
present transitively via the `openai` package, keeping the net-new dependency surface to
`fastapi`, `uvicorn`, `jinja2`, `python-multipart`. Server-rendered HTML avoids a build
step entirely, matching spec Non-Goals' "do not attempt to build a complete design system"
and the `aic-brand-landing` skill's "smallest architecture" guidance.

**Alternatives considered**:
- *Flask*: comparable minimalism, but lacks FastAPI's native Pydantic integration —
  request validation would need to be reimplemented or bolted on, adding code rather than
  reusing an existing pattern.
- *Static site + third-party form service (e.g., a hosted forms API)*: rejected — would
  require sending user data and funnel events to an external third party, and would make
  computing the exact conversion-rate formulas in FR-011 dependent on that third party's
  export capabilities rather than this project's own SQLite queries.
- *Pure static HTML with no backend at all*: rejected — cannot satisfy FR-007/FR-009/FR-010
  (registration, feedback, and event capture all require persisting something server-side).

## Decision 2: Static, pre-captured Amazon snapshot (already an Assumption in spec.md)

**Decision**: `scripts/capture_amazon_snapshot.py` runs `run_investment_workflow` once
against the existing Amazon dataset (`scripts/mvp_amazon_dataset.py`, feature 010) with a
real `OpenAIProvider`, converts the resulting `WorkflowResult` into an `AmazonPresentation`
read model (human-readable strings, not raw Pydantic dumps of internal types), and writes
it to `data/amazon_snapshot.json`. The FastAPI app loads this file once at startup and
serves it to every visitor identically — no per-request recomputation, no LLM call in the
request path.

**Rationale**: Already justified in spec.md's Assumptions (cost, latency, and
non-determinism of live per-visitor LLM calls). This also means `aic.public`'s
request-serving code has zero runtime dependency on `AIC_OPENAI_API_KEY` being configured
— only the manual, occasionally-run capture script needs it, matching the existing
`mvp_amazon_validation.py`/`mvp_amazon_acceptance.py` pattern of "manual scripts make real
calls; the tested application code never does."

**Alternatives considered**:
- *Live recomputation per visitor*: rejected per spec.md Assumptions (already resolved
  there, restated here for plan traceability).
- *Recompute once per server process startup*: rejected — still requires a configured
  OpenAI key in whatever environment runs the public server, and reintroduces
  non-determinism across deploys/restarts for "the same" published example; a checked-in,
  deliberately-published snapshot is simpler and matches "a new validated snapshot
  published" language in spec.md's Edge Cases.

## Decision 3: Storage — raw `sqlite3`, three tables, no ORM

**Decision**: Use Python's stdlib `sqlite3` directly (no SQLAlchemy or other ORM). Three
tables: `registrations` (email UNIQUE, optional fields, qualified flag, timestamp),
`feedback_submissions` (six answers or a JSON blob of them, optional email, timestamp),
`validation_events` (event_type, timestamp). A small `Storage` protocol in
`aic/public/storage.py` is implemented by a `SqliteStorage` class; tests use an in-memory
SQLite database (`sqlite3.connect(":memory:")`) via the same protocol, preserving this
project's existing "provider abstraction, fake for tests" pattern (constitution Principle
X, already used for `LLMProvider`/`FakeLLMProvider`).

**Rationale**: Constitution explicitly names "SQLite locally" as baseline tech. Three
small, fixed-shape tables do not justify an ORM's complexity (constitution VIII). A
protocol + swappable implementation mirrors the exact pattern this project already uses for
`LLMProvider`, so no new architectural idiom is introduced.

**Alternatives considered**:
- *SQLAlchemy*: rejected — unnecessary abstraction for three tables with no relationships
  beyond an optional email linkage (constitution VIII, "avoid unnecessary dependencies").
- *In-memory Python list/dict with no persistence*: rejected — funnel metrics (FR-011) and
  feedback export (FR-009) require data to survive a server restart to be useful for a
  real, multi-day validation experiment.

## Decision 4: "Qualified" registration classification

**Decision**: Implemented as a small pure function in `aic/public/registration.py`,
`classify_qualified(role: str | None) -> bool`, checking the submitted role/investor-profile
value against a fixed set of target-audience values (individual investor performing
fundamental research, serious retail investor, finance/investment professional). Computed
once at registration time and stored as a column, not recomputed at query time.

**Rationale**: Matches spec.md's Assumptions ("simple, adjustable heuristic, not a hard
business rule"). Storing it (rather than deriving it at read time) keeps the
qualified-interest-rate query (FR-011) a simple `COUNT` with no per-query classification
logic, and makes the heuristic trivially adjustable/auditable later without a data
migration (the raw `role` value is still stored alongside the derived flag).

**Alternatives considered**:
- *No classification, ask the operator to manually review*: rejected — FR-011 requires the
  qualified-interest rate to be computable directly from recorded data.

## Decision 5: Analytics — first-party SQLite events, no third-party analytics SDK

**Decision**: `validation_events` table records event_type + timestamp only (no
third-party analytics/tracking script, no cookies beyond what's strictly needed for the
session-less form flow). Event types follow the `aic-brand-landing` skill's exact naming:
`landing_visit`, `hero_cta_click`, `demo_view`, `demo_interaction`, `signup_started`,
`signup_completed`, `early_access_requested`.

**Rationale**: Spec Non-Goals explicitly rules out "a custom analytics platform" — this is
the minimum needed to compute the three named conversion rates (FR-011), not a general
analytics system. Avoiding a third-party script also avoids a whole category of consent/
privacy/ad-blocker considerations that would otherwise need separate handling (and directly
serves spec's Edge Case: "analytics failure must not block the core funnel actions" — a
first-party, same-origin, no-JS-dependency event write via the same request that serves the
page is simpler to keep non-blocking than a third-party async script).

**Alternatives considered**:
- *Google Analytics / a third-party product analytics tool*: rejected by spec Non-Goals
  ("do not build a custom analytics platform" is about not over-building, but a third-party
  tool would also violate "the objective is measurement, not analytics infrastructure" by
  adding an entire external integration for a handful of counters).

## Decision 6: Deployment/hosting is out of this plan's scope

**Decision**: This plan produces a fully working, tested, locally-runnable FastAPI
application (`uv run uvicorn aic.public.app:app`). It does not provision a domain, TLS
certificate, S3 bucket, or any live public URL.

**Rationale**: This execution environment has no AWS credentials or DNS/domain-control
access, so any such provisioning could not actually be carried out here regardless of
scope decisions. The constitution defers AWS until local validation works, and the
`aic-brand-landing` skill's S3 mention is phrased as "may be used where appropriate," not
mandated. Treating live deployment as a separate, subsequent operational step (outside
this feature's tasks) keeps this plan honest about what it can actually deliver.

**Alternatives considered**:
- *Write Terraform/CDK for S3 + CloudFront + a domain now*: rejected — constitution VIII
  ("no premature infrastructure," "AWS deferred until local vertical slice has been
  validated") and this plan cannot verify such infrastructure actually works without real
  credentials to test it against.
