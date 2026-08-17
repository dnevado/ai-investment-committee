---

## description: "Task list for public MVP validation and AWS deployment"

# Tasks: Public MVP Validation

**Input**: Design documents from `/specs/011-public-mvp-validation/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`,
`contracts/public-interface.md`, `quickstart.md`

**Current objective**: The public validation application itself is already implemented and
tested (Phases 1–9, T001–T034). The remaining objective is to deploy it to AWS using the
serverless architecture the current `spec.md` mandates (S3 + CloudFront + Lambda +
DynamoDB — see plan.md, research.md Decisions 7–9), expose it through a real custom domain
over HTTPS, verify the complete validation funnel end-to-end, and prove that production
registration data survives independent static-site and Lambda redeployments.

**Revision note (2026-08-16, second)**: An earlier Phase 10 (T035–T068, below, kept for
history) targeted a single AWS Lightsail instance running `systemd` + Caddy + SQLite.
`spec.md` was replaced with a complete specification that explicitly forbids that
architecture. T035–T039's *files* are superseded and scheduled for removal (T080); T040–
T068 describe manual steps against infrastructure that must not be built, so they are not
carried forward as actionable tasks — the new Phase 10 (revised), T069 onward, replaces
them.

**Tests**: Automated application tests are already complete in Phases 1–9. The new
`DynamoDbStorage` gets its own automated tests (against `moto`, no real AWS calls — T074).
Everything AWS-account-specific is verified manually against the real environment/domain.

**Organization**: Tasks are grouped by implementation phase and user story. User Stories
1–6 are already implemented. User Story 7 is the deployment/publication objective.

## Format: `[ID] [P?] [Story] Description`

* **[P]**: Can run in parallel because it touches different files and has no dependency on
  another task in the same phase.
* **[Story]**: User story associated with the task.
* Exact file paths are included in implementation tasks.

## Path Conventions

Single project, `src`-layout:

* Public application: `src/aic/public/` (gains `lambda_handler.py`; `storage.py` gains
  `DynamoDbStorage` alongside the unchanged `SqliteStorage`)
* Static-site build script: `scripts/build_static_site.py`
* Deployment artifacts: `deploy/`
* Public snapshot: `data/amazon_snapshot.json`
* Tests: `tests/unit/public/`
* Production persistence: DynamoDB (three tables — data-model.md). SQLite remains local/
  test-only (FR-021).
* No deployment task modifies `aic.dcf`/`aic.domain`/`aic.research`/`aic.bullbear`/
  `aic.committee`/`aic.report`/`aic.workflow`.

---

# Phase 1: Setup

**Purpose**: Add the public-layer dependencies and establish the package shell.

* [x] T001 Add `fastapi`, `uvicorn`, `jinja2`, `python-multipart` to `pyproject.toml` dependencies and run `uv sync` (research.md Decision 1).
* [x] T002 Create `src/aic/public/__init__.py` as the public package shell.

**Checkpoint**: Public dependencies and package structure exist.

---

# Phase 2: Foundational

**Purpose**: Establish the storage layer, public read model, registration/feedback/event
models, validated Amazon snapshot, and FastAPI application scaffold.

* [x] T003 [P] Create `src/aic/public/storage.py` with the `Storage` protocol and
  `SqliteStorage` implementation covering `registrations`, `feedback_submissions`, and
  `validation_events`, including the unique normalized-email constraint and support for
  both filesystem and `":memory:"` databases.

* [x] T004 [P] Create `src/aic/public/presentation.py` with `EvidenceItemView`,
  `AmazonPresentation`, and `build_presentation(result: WorkflowResult) ->
  AmazonPresentation`, mapping the validated workflow result into the stable public
  presentation/read model and translating evidence classifications into human-readable
  labels.

* [x] T005 [P] Create `src/aic/public/registration.py` with the
  `EarlyAccessRegistration` Pydantic model and `classify_qualified(role)` heuristic defined
  by the specification.

* [x] T006 [P] Create `src/aic/public/feedback.py` with the six optional qualitative
  feedback fields and optional email association.

* [x] T007 [P] Create `src/aic/public/events.py` with the validation-event model,
  funnel-metrics model, supported event types, and `compute_funnel_metrics(...)` including
  zero-denominator guards.

* [x] T008 Create `scripts/capture_amazon_snapshot.py` to build the existing Amazon
  workflow input, execute the validated Feature 009/010 workflow once using the real
  provider configuration, convert the result through `build_presentation`, and write
  `data/amazon_snapshot.json`.

* [x] T009 Run `uv run python scripts/capture_amazon_snapshot.py` with
  `AIC_OPENAI_API_KEY` configured and commit the resulting
  `data/amazon_snapshot.json`.

* [x] T010 Create `src/aic/public/app.py` with
  `create_app(*, storage=None, presentation=None) -> FastAPI`, loading the committed
  Amazon snapshot and opening the default SQLite database when no test overrides are
  supplied. Keep `app = create_app()` for Uvicorn.

* [x] T011 Export the public API from `src/aic/public/__init__.py`.

**Checkpoint**: Public application foundation is complete and decoupled from live workflow
execution.

---

# Phase 3: User Story 1 — Understand the Value Proposition

**Priority**: P1

* [x] T012 Create the shared public templates in
  `src/aic/public/templates/base.html` and
  `src/aic/public/templates/landing.html`, implementing the final approved
  Problem → Quorum Difference → How It Works → Real-World Validation →
  Why It's Different → Evidence → CTA narrative and the approved visual identity.

* [x] T013 Wire `GET /` in `src/aic/public/app.py` to render the landing page and record
  one `landing_visit` event synchronously before responding.

* [x] T014 Create public application test helpers in
  `tests/unit/public/public_fakes.py` and tests in
  `tests/unit/public/test_public_app.py` covering the landing-page value proposition and
  visit tracking.

**Checkpoint**: The public landing page communicates the product proposition and tracks
landing visits.

---

# Phase 4: User Story 2 — Inspect a Real Investment Example

**Priority**: P1

* [x] T015 Extend `src/aic/public/templates/landing.html` with the final Amazon/AMZN
  validation presentation using the committed `AmazonPresentation` snapshot. Render only
  approved presentation fields and the curated evidence sample; do not introduce new
  financial figures or recompute the workflow.

* [x] T016 Add presentation-model tests in
  `tests/unit/public/test_public_presentation.py` covering every
  `AmazonPresentation` mapping and all evidence classification mappings.

* [x] T017 Add the human-readable Amazon-example rendering test to
  `tests/unit/public/test_public_app.py`, ensuring the response contains the expected
  snapshot-derived valuation/recommendation content and no raw Python/Pydantic
  representation.

**Checkpoint**: The public page presents the same validated Amazon workflow output without
live recomputation.

---

# Phase 5: User Story 3 — Minimal-Friction Registration

**Priority**: P1

* [x] T018 Create `src/aic/public/templates/register.html` and
  `src/aic/public/templates/register_confirmation.html` using the final approved
  registration UX: email required and role represented by the approved radio-button
  options; keep optional backend fields compatible with the existing model.

* [x] T019 Wire `GET /register` and `POST /register` in
  `src/aic/public/app.py`, including validation, qualification classification,
  idempotent registration persistence, registration events, and `303` confirmation
  redirect.

* [x] T020 Add registration-model tests in
  `tests/unit/public/test_public_registration.py` covering valid email-only submission,
  malformed email rejection, and qualification classification.

* [x] T021 Add the duplicate-email persistence test to
  `tests/unit/public/test_public_storage.py`.

* [x] T022 Add application-level registration tests to
  `tests/unit/public/test_public_app.py`, covering successful email-only registration,
  malformed email rejection, and duplicate-registration behavior.

**Checkpoint**: The primary validation signal — completed registration — works without
accounts, passwords, or authentication.

---

# Phase 6: User Story 4 — Qualitative Feedback

**Priority**: P2

* [x] T023 Create `src/aic/public/templates/feedback.html` containing exactly the six
  questions specified by US4 and create
  `src/aic/public/templates/feedback_confirmation.html`.

* [x] T024 Wire `GET /feedback` and `POST /feedback` in
  `src/aic/public/app.py`. Reject all-blank submissions with `422`; persist any submission
  containing at least one answer; do not require a prior registration.

* [x] T025 Add feedback-model tests in
  `tests/unit/public/test_public_feedback.py` covering all-blank rejection, single-answer
  acceptance, and submission without an associated registration/email.

* [x] T026 Add application-level feedback tests to
  `tests/unit/public/test_public_app.py`.

**Checkpoint**: Feedback is independently collectible from registration.

---

# Phase 7: User Story 5 — Measure the Validation Funnel

**Priority**: P2

* [x] T027 Wire `POST /events` in `src/aic/public/app.py` as a best-effort analytics
  endpoint returning `202 Accepted` even when the supplied event type is malformed or
  unknown.

* [x] T028 Wire `GET /metrics` in `src/aic/public/app.py`, including optional time-window
  filtering and the three specified conversion rates.

* [x] T029 Add event and funnel-metric tests in
  `tests/unit/public/test_public_events.py`, including zero-denominator cases.

* [x] T030 Add application-level event and metrics tests to
  `tests/unit/public/test_public_app.py`.

**Checkpoint**: The validation experiment can measure visits, CTA activity, registrations,
qualified interest, and feedback.

---

# Phase 8: User Story 6 — Trust and Disclaimer Messaging

**Priority**: P3

* [x] T031 Create the shared disclaimer partial
  `src/aic/public/templates/_disclaimer.html` and include it adjacent to the Amazon
  example and registration/CTA areas.

* [x] T032 Add disclaimer and prohibited-language tests to
  `tests/unit/public/test_public_app.py`, covering landing, registration, and feedback
  pages.

**Checkpoint**: The public experience explicitly positions the output as research
assistance rather than financial advice and contains no guaranteed-return messaging.

---

# Phase 9: Polish and Full Regression

**Purpose**: Confirm that the complete application remains correct and green before
deployment.

* [x] T033 Run the full repository validation:
  `pytest`, `ruff check .`, and `mypy src`.
  Confirm that all pre-existing Feature 010 tests remain green and that no investment-engine
  behavior has changed.

* [x] T034 Execute the manual browser walkthrough from `quickstart.md`, including landing,
  Amazon example, CTA, registration, duplicate registration, feedback, and `/metrics`
  consistency checks against the local application.

**Checkpoint**: The application is implementation-complete locally. `aic.public`'s route
logic is stable; only its production storage/entry-point wiring changes below.

---

# Phase 10 (SUPERSEDED — kept for history, not actionable): Publish the Validation MVP on a Lightsail Instance

**Superseded 2026-08-16 (second revision)**: `spec.md` was replaced with a complete
specification that explicitly forbids this architecture (Lightsail, EC2, systemd, Caddy, an
always-running Python server, production SQLite). **Do not execute T040–T068 below.** They
describe manual steps against infrastructure that must not be built. T035–T039's files
(`deploy/quorum.service`, `deploy/Caddyfile`, `deploy/provision.sh`, `deploy/release.sh`,
`deploy/backup_to_s3.sh`) exist on disk from when these tasks were completed, and are
removed by T080 in the new Phase 10 (revised) below. See plan.md's Revision history and
research.md Decision 6 (superseded) for the full reasoning.

<details>
<summary>Original Phase 10 content (collapsed — historical record only)</summary>

**Priority**: P1

**Goal**: Make the already-complete application publicly accessible through a real custom
domain over HTTPS using a single AWS Lightsail instance. Registration, feedback,
analytics, and the Amazon snapshot must behave identically to local execution.

Production topology (superseded):

```text
Internet → Custom Domain → Caddy/Let's Encrypt → 127.0.0.1:8000 → FastAPI/Uvicorn
                                                                     ├── Amazon snapshot
                                                                     ├── templates/assets
                                                                     └── SQLite database
```

* [x] T035 [P] [US7] Create `deploy/quorum.service` (systemd unit) — **superseded, see T080**.
* [x] T036 [P] [US7] Create `deploy/Caddyfile` — **superseded, see T080**.
* [x] T037 [P] [US7] Create `deploy/provision.sh` (Lightsail instance + static IP + firewall) — **superseded, see T080**.
* [x] T038 [US7] Create `deploy/release.sh` (rsync app code, `uv sync`, restart systemd/Caddy) — **superseded, see T080**.
* [x] T039 [P] [US7] Create `deploy/backup_to_s3.sh` (SQLite → private S3 backup) — **superseded, see T080**.
* [ ] T040–T068 — **do not execute.** Manual AWS provisioning, first release, production
  end-to-end validation, persistence/redeployment verification, backup verification, and a
  final release checklist, all written against the Lightsail architecture. Superseded in
  full by Phase 10 (revised) T081–T100 below.

</details>

---

# Phase 10 (revised, current): Publish the Validation MVP on AWS — S3 + CloudFront + Lambda + DynamoDB

**Priority**: P1

**Goal**: Make the already-complete application publicly accessible through a real custom
domain over HTTPS using the serverless architecture `spec.md` mandates. The landing page
becomes a static artifact served by CloudFront/S3; every dynamic route (register, feedback,
events, metrics) continues to be served by the *unmodified* `aic.public.app` FastAPI routes,
now running inside AWS Lambda; production persistence moves to DynamoDB (plan.md, research.md
Decisions 7–9, data-model.md).

**Important constraint**: This phase MUST NOT modify `aic.dcf`, `aic.domain`,
`aic.research`, `aic.bullbear`, `aic.committee`, `aic.report`, `aic.workflow`, or the
validated Amazon snapshot. It MAY add new code to `src/aic/public/` (a new `Storage`
implementation and a thin Lambda entry point) — narrowly scoped, spec-mandated, and
consistent with the existing `Storage` protocol (constitution Principle X).

Production topology (current):

```text
Browser → Custom Domain → CloudFront
                             ├── default behavior ──────────► S3 (OAC)
                             │                                  └── static landing page,
                             │                                      CSS/JS, built once by
                             │                                      scripts/build_static_site.py
                             └── /register*, /feedback*, ────► Lambda Function URL (OAC)
                                 /events*, /metrics*               └── aic.public.app via
                                                                        Mangum, unmodified
                                                                        route logic
                                                                          │
                                                                          ▼
                                                                     DynamoDB
                                                                     (registrations,
                                                                      feedback_submissions,
                                                                      validation_events)
```

## Application code (genuinely new — the only Python changes in this feature)

* [x] T069 [P] [US7] Add `DynamoDbStorage` to `src/aic/public/storage.py`, implementing the
  existing `Storage` protocol via `boto3`: `registrations` keyed by `email_normalized`
  with a conditional `put_item` (`ConditionExpression="attribute_not_exists(
  email_normalized)"`) for idempotent registration (FR-017); `feedback_submissions` keyed
  by `feedback_id`; `validation_events` keyed by `event_id`; `compute_funnel_metrics`
  implemented via table `Scan` with `created_at`/`event_type` filters, preserving the same
  zero-denominator guards as `SqliteStorage`. `SqliteStorage` is not modified
  (data-model.md "Deployment revision, second").

* [x] T070 [P] [US7] Add `mangum` and `boto3` to `pyproject.toml`'s main `dependencies`;
  add `moto` to the `dev` dependency group; run `uv sync` (research.md Decisions 7–8).

* [x] T071 [US7] Create `src/aic/public/lambda_handler.py`: loads the committed
  `AmazonPresentation` snapshot, constructs `create_app(storage=DynamoDbStorage(...),
  presentation=...)`, and exposes `handler = Mangum(app)` as the Lambda entry point. No
  route/template/validation logic is duplicated or reimplemented (depends on T069, T070).

* [x] T072 [P] [US7] Add a `landing_visit` beacon to `src/aic/public/static/track.js`,
  fired on `DOMContentLoaded` specifically on the landing page, `POST`ing `{"event_type":
  "landing_visit"}` to `/events` — restores landing-visit measurement in production now
  that `GET /` is no longer invoked per visitor (research.md Decision 9).

* [x] T073 [US7] Create `scripts/build_static_site.py`: renders `templates/landing.html`
  (with `templates/base.html`) via the same Jinja2 environment and committed
  `AmazonPresentation` snapshot `app.py` already uses, and copies `src/aic/public/static/`
  verbatim, into a build output directory (e.g. `dist/`) ready for S3 upload. Depends only
  on existing T004/T012 code — no dependency on T069–T072.

* [x] T074 [US7] Add `DynamoDbStorage` tests (new file or addition to
  `tests/unit/public/test_public_storage.py`) using `moto`'s DynamoDB mock: round-trip all
  three entity types; a second `put_item` for an existing `email_normalized` is rejected by
  the condition expression and does not create a duplicate; `compute_funnel_metrics`
  produces the same three rates (including zero-denominator cases) as the existing
  `SqliteStorage` tests already verify (depends on T069; research.md Decision 8).

## Deployment artifacts (replace the five superseded Lightsail files)

* [x] T075 [P] [US7] Create `deploy/provision_data.sh`: idempotent AWS CLI script creating
  the three DynamoDB tables in On-Demand capacity mode per data-model.md's schema.

* [x] T076 [P] [US7] Create `deploy/provision_lambda.sh`: idempotent AWS CLI script that
  packages `src/aic/public/` + dependencies + `lambda_handler.py`, creates the Lambda
  function, its execution role (scoped to `PutItem`/`GetItem`/`Query`/`Scan` on exactly the
  three table ARNs plus CloudWatch Logs — FR-024), and its Function URL (`AuthType:
  AWS_IAM`).

* [x] T077 [P] [US7] Create `deploy/provision_cdn.sh`: idempotent AWS CLI script creating a
  private S3 bucket, requesting an ACM certificate for the real domain **in `us-east-1`**,
  and creating the CloudFront distribution with two origins (S3 via Origin Access Control,
  the Lambda Function URL via Origin Access Control for Lambda) and path-pattern behaviors
  `/register*`, `/feedback*`, `/events*`, `/metrics*` → Lambda, default → S3.

* [x] T078 [US7] Create `deploy/release_static.sh`: runs `scripts/build_static_site.py`,
  syncs the build output to the S3 bucket, and invalidates the CloudFront cache for `/` and
  `/static/*` (depends on T073, T077).

* [x] T079 [US7] Create `deploy/release_lambda.sh`: re-packages `src/aic/public/` +
  production dependencies (`--no-dev`) and updates the Lambda function code (depends on
  T071, T076). Independently runnable from `release_static.sh` (FR-028).

* [x] T080 [US7] Remove the five superseded files: `deploy/quorum.service`,
  `deploy/Caddyfile`, `deploy/provision.sh`, `deploy/release.sh`,
  `deploy/backup_to_s3.sh`, and the now-unused `deploy/.ssh/` directory if present (depends
  on T075–T079 existing as replacements).

## AWS provisioning (manual — requires the user's own AWS account/credentials; cannot be executed or verified in this sandbox)

* [x] T081 [US7] **Manual**: run `deploy/provision_data.sh` against the real AWS account.

* [x] T082 [US7] **Manual**: run `deploy/provision_lambda.sh` (depends on T081 — the
  execution role's policy references the table ARNs).

* [x] T083 [US7] **Manual**: run `deploy/provision_cdn.sh` (depends on T082 — CloudFront's
  Lambda origin needs the Function URL to exist), then point the real domain's DNS at the
  resulting CloudFront distribution domain name.

## First production release (manual)

* [x] T084 [US7] **Manual**: run `deploy/release_static.sh` (depends on T083).

* [x] T085 [US7] **Manual**: run `deploy/release_lambda.sh` (depends on T082; independent
  of T084).

* [ ] T086 [US7] **Manual**: confirm `https://YOUR_DOMAIN/` serves the static landing page
  over a valid ACM/CloudFront TLS certificate (depends on T084). **Blocked**: no custom
  domain purchased yet (plan.md constraint: never assume a domain is available). The site
  is verified reachable and valid over HTTPS at CloudFront's default certificate/domain
  (`https://d2bd8kteboaclo.cloudfront.net/`) — re-run `provision_cdn.sh` with
  `DOMAIN=yourdomain.com` once a domain exists, then complete this check.

**Checkpoint**: The application is reachable through the real HTTPS domain, static content
from S3/CloudFront and dynamic routes from Lambda/DynamoDB.

---

# Phase 11 (revised): Production End-to-End Validation

**Purpose**: Verify the actual public funnel works against the new architecture, not
merely that the domain resolves.

* [ ] T087 [US7] **Manual**: US1 — confirm the live static landing page states what
  Quorum is and who it's for, matching the local build.

* [ ] T088 [US7] **Manual**: US2 — confirm the Amazon/AMZN example on the live landing page
  matches the committed snapshot, with no raw Python/Pydantic output.

* [x] T089 [US7] **Manual**: US3 — submit a real test registration (email only) against
  `https://YOUR_DOMAIN/register`; confirm success and the confirmation page, served by
  Lambda. Verified against `https://d2bd8kteboaclo.cloudfront.net/register` (real domain
  pending T086) — `303 See Other → /register/confirmation`, and the record is visible in
  `/metrics`.

* [x] T090 [US7] **Manual**: resubmit the same test email; confirm the DynamoDB conditional
  put rejects it and `completed_registrations` in `/metrics` is not double-counted. Verified:
  resubmitting the same email still returns `303` (idempotent), `completed_registrations`
  stayed at 2.

* [x] T091 [US7] **Manual**: US4 — submit feedback without a prior registration; confirm
  success. Verified: `303 See Other → /feedback/confirmation`.

* [ ] T092 [US7] **Manual**: US5 — confirm `https://YOUR_DOMAIN/metrics` reflects the test
  activity, including at least one `landing_visit` recorded via the new client-side beacon
  (T072/research.md Decision 9), and that the three conversion rates compute correctly.
  **Partially verified**: registration/feedback/CTA-click counts all update correctly and
  conversion rates compute; `landing_visit` specifically was not exercised (would require
  loading the static page in a real browser to fire the client-side beacon — not something a
  `curl` test can trigger, since `GET /` is served as pre-rendered static content from S3,
  not the Lambda `landing()` route).

* [ ] T093 [US7] **Manual**: US6 — confirm disclaimer messaging is visible near the Amazon
  example and CTA/registration, and that no prohibited guaranteed-return/financial-advice
  language appears anywhere on the live site.

**Checkpoint**: All six original User Stories pass against the real production domain.

---

# Phase 12 (revised): Independent-Release & Persistence Verification

**Purpose**: Prove production data survives redeployment, and that static and Lambda
releases are genuinely independent of each other (FR-027/FR-028, SC-012/SC-013).

* [x] T094 [US7] **Manual**: record the T089 registration's state via `/metrics` before
  redeploying anything. Verified: `completed_registrations: 2`, `feedback_submissions: 1`.

* [x] T095 [US7] **Manual**: re-run `deploy/release_static.sh` only; confirm the DynamoDB
  registration from T089 and its `/metrics` count are unaffected. Verified: counts unchanged
  after the static-only release; landing page still 200.

* [x] T096 [US7] **Manual**: re-run `deploy/release_lambda.sh` only; confirm the same
  registration and `/metrics` count are unaffected, and that the live site still serves the
  same committed Amazon snapshot with no live workflow/OpenAI execution. Verified: counts
  unchanged after the Lambda-only release.

**Checkpoint**: A static-site release and a Lambda release each leave DynamoDB data intact,
independently of one another.

---

# Final Release Checklist (revised)

* [ ] T097 [US7] Confirm the real custom domain resolves to the CloudFront distribution and
  HTTPS is valid via the ACM certificate.

* [x] T098 [US7] Confirm the static landing page (S3/CloudFront) and all four Lambda-routed
  path prefixes (`/register*`, `/feedback*`, `/events*`, `/metrics*`) work end-to-end.
  Verified: landing page 200, `POST /register` and `POST /feedback` both 303 to their
  confirmation pages, `POST /events` 200, `GET /metrics` 200 with correct counts.

* [x] T099 [US7] Confirm no changes were made to `aic.dcf`, `aic.research`, `aic.bullbear`,
  `aic.committee`, `aic.report`, or `aic.workflow`, and that no public request triggers
  `run_investment_workflow` or a live OpenAI API call (FR-016, FR-022). Verified: `git diff`
  against those directories is empty, and the only "OpenAI" reference under `aic.public` is
  the comment in `presentation.py` explaining why that dependency chain is excluded.

* [x] T100 [US7] Record the production URL, deployment date, and AWS resource identifiers
  (DynamoDB table names, Lambda function ARN, CloudFront distribution ID, ACM certificate
  ARN) in the project release notes. Recorded in
  `specs/011-public-mvp-validation/release-notes.md` (no ACM certificate yet — no custom
  domain purchased).

---

# Final Checkpoint

Feature 011 is complete only when all of the following are true:

```text
[✓] Public application implemented
[✓] Amazon validated snapshot published
[✓] Registration works
[✓] Feedback works
[✓] Funnel analytics work
[✓] Disclaimer/trust messaging present
[✓] Full automated test suite green (including DynamoDbStorage, moto-mocked)
[ ] DynamoDB tables provisioned (On-Demand)
[ ] Lambda function + Function URL provisioned, least-privilege IAM role
[ ] S3 bucket + CloudFront distribution provisioned (OAC for both origins)
[ ] ACM certificate issued (us-east-1) and DNS configured
[ ] HTTPS custom domain live
[ ] Public funnel validated end-to-end (including the landing_visit beacon)
[ ] Registration survives an independent static-site release
[ ] Registration survives an independent Lambda release
[ ] No investment-engine changes
[ ] No live workflow/OpenAI execution per visitor
```

The feature's finish line is:

```text
Landing (static, S3/CloudFront)
  ↓
Product understanding
  ↓
Amazon example
  ↓
CTA
  ↓
Registration (Lambda + DynamoDB)
  ↓
Feedback (Lambda + DynamoDB)
  ↓
Measurement (Lambda + DynamoDB)
  ↓
Serverless AWS deployment
  ↓
HTTPS custom domain
  ↓
Real-user validation
```

It does **not** include:

```text
Registration
  ↓
Account platform
  ↓
Portfolio
  ↓
Trading
  ↓
Brokerage
  ↓
Subscriptions
  ↓
Production investment platform
```

---

# Dependencies & Execution Order

## Phase Dependencies

* **Phase 1** blocks Phase 2.
* **Phase 2** blocks User Stories 1–6.
* **User Stories 1–6** are already implemented and validated.
* **Phase 9** is the final local regression gate.
* **Phase 10 (SUPERSEDED)** is historical only — not a dependency of anything below.
* **Phase 10 (revised)** depends on Phase 9.
* **Phase 11 (revised)** depends on successful completion of the first production release
  (T084–T086).
* **Phase 12 (revised)** depends on a working production deployment (Phase 11 passing).
* The Final Release Checklist depends on Phases 10 (revised)–12 (revised).

## Deployment Dependencies (current architecture)

```text
T069 ─┐
T070 ─┼──→ T071 ─────────────────────────────┐
      │                                       │
T072 ─┘ (independent — track.js only)         │
                                               ▼
T073 ─────────────────────────→ T078 ◄── T077 ┤
                                   │           │
T069 ─→ T074 (tests, independent) │           │
                                   │           │
T075 ─→ T076 ─→ T082 ──────────────────────────┼──→ T085 ─┐
                  │                             │          │
T075 ─→ T081 ─────┘                             │          ▼
                                                 │      T089-T093
T075/T076/T077 → T080 (remove superseded files)  │          │
                                                 │          ▼
                          T083 ──→ T084 ─────────┘      T094-T096
                            ↑
                          T077

T086 depends on T084
T087-T093 depend on T086
T097-T100 depend on Phases 10 (revised)–12 (revised)
```

## Parallel Opportunities

Application code (no shared-file conflicts):

```text
T069  DynamoDbStorage in storage.py
T070  pyproject.toml dependency additions
T072  track.js landing_visit beacon
```

(T071 depends on both T069 and T070 completing; T073 has no dependency on any of T069-T072.)

Deployment scripts (independent files):

```text
T075  provision_data.sh
T076  provision_lambda.sh
T077  provision_cdn.sh
```

Manual AWS provisioning must happen in dependency order (T081 → T082 → T083), not in
parallel, since each later step's script references identifiers the earlier step creates.

## Parallel Example: New Application Code

```bash
# Can be worked on together:
Task: "Add DynamoDbStorage to src/aic/public/storage.py"
Task: "Add mangum/boto3/moto to pyproject.toml and run uv sync"
Task: "Add the landing_visit beacon to src/aic/public/static/track.js"
```

---

# Implementation Strategy

## Current State

Do **not** restart the implementation from Phase 1. Do **not** execute anything in the
SUPERSEDED Phase 10 above.

The public application and validation funnel are already implemented and tested. The
current work begins at:

```text
T069
```

## Recommended Execution Sequence

1. `DynamoDbStorage` (T069), dependencies (T070), `track.js` beacon (T072) — can be done
   together.
2. `lambda_handler.py` (T071).
3. `DynamoDbStorage` tests against `moto` (T074) — confirm the storage layer is correct
   before anything AWS-specific is provisioned.
4. `build_static_site.py` (T073).
5. The three provisioning scripts (T075–T077) and the two release scripts (T078–T079).
6. Remove the five superseded Lightsail files (T080).
7. Run `pytest`, `ruff check .`, `mypy src` across the whole repo — confirm the new code
   doesn't regress anything before touching a real AWS account.
8. Provision DynamoDB (T081), then Lambda (T082), then CloudFront/S3/ACM (T083); configure
   DNS.
9. Release static (T084) and Lambda (T085); confirm HTTPS (T086).
10. Execute the complete production funnel (T087–T093).
11. Verify independent-release persistence (T094–T096).
12. Complete the Final Release Checklist (T097–T100).

---

# Important Constraints

* The real domain is a required deployment input. **Never invent one.**
* AWS credentials belong to the user/operator and must not be embedded in repository files.
* Production secrets must not be committed.
* `release_static.sh` and `release_lambda.sh` must never touch DynamoDB data.
* The Lambda execution role must be scoped to exactly the three table ARNs plus CloudWatch
  Logs — no administrator or wildcard-resource policy (FR-024).
* The Amazon snapshot remains static and read-only at request time.
* The public application must never execute the investment workflow for an individual
  visitor, in Lambda or locally.
* No new financial figures may be introduced during deployment.
* No changes to DCF, research, Bull/Bear, committee, report, workflow, domain, or
  LLM-provider logic are permitted.
* No authentication, accounts, portfolios, trading, payments, subscriptions, or other
  production SaaS functionality is introduced.
* No API Gateway, unless a later revision demonstrates it's required and the spec is
  formally revised (spec.md "Explicitly Forbidden for Feature 011").
* The deployment architecture must remain intentionally minimal and serverless — no
  always-running compute.

---

# Notes

* T001–T034 are retained as completed — the application layer is unaffected by the
  deployment architecture pivot.
* T035–T039 remain marked complete because that work genuinely happened, but their output
  (five files under `deploy/`) is superseded and removed by T080; do not treat them as
  currently-correct deployment guidance.
* T069–T080 are repository implementation tasks (application code + deployment scripts) and
  can be authored/tested before AWS access exists — T074 in particular gives real
  confidence in `DynamoDbStorage` via `moto` without needing a real AWS account.
* T081–T100 require a real AWS account and/or real domain and therefore cannot be executed
  or verified in a sandboxed environment.
* DynamoDB is the source of truth for registrations, feedback, and validation events in
  production; SQLite remains the source of truth locally and in tests (FR-021).
* A successful deployment is not sufficient by itself: Feature 011 is complete only after
  the real public funnel is exercised and a registration is demonstrated to survive both an
  independent static-site release and an independent Lambda release.
* The final success criterion remains validation of user interest, not proof of
  product-market fit or readiness for a production investment platform.
