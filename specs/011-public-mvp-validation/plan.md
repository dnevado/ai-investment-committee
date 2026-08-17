# Implementation Plan: Public MVP Validation

**Branch**: `011-public-mvp-validation` | **Date**: 2026-08-16 (revised again) | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/011-public-mvp-validation/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command; its definition describes the execution workflow.

**Revision history**:
- **2026-08-16 (first revision)**: `spec.md` was replaced with a short deployment directive.
  This plan was revised to add a single-Lightsail-instance deployment (systemd + Caddy +
  SQLite-on-disk). `deploy/quorum.service`, `deploy/Caddyfile`, `deploy/provision.sh`,
  `deploy/release.sh`, `deploy/backup_to_s3.sh` were written against that design.
- **2026-08-16 (this revision)**: `spec.md` was replaced again, this time with a complete,
  detailed spec (proper User Stories/FR/SC format) that **explicitly forbids** everything
  the first revision built: Lightsail, EC2, systemd, Caddy, an always-running Python server,
  and SQLite as the production store (FR-019–FR-023, "Explicitly Forbidden for Feature
  011"). It mandates S3 + CloudFront + Lambda + DynamoDB instead. **The five `deploy/*`
  files from the first revision are now superseded and must be replaced** — this plan
  documents the new design; replacing those files is implementation work for after
  `/speckit-tasks` regenerates tasks, not something this planning pass does itself.

## Summary

**Application (done, frozen where the spec still allows)**: A Python web application
presents Quorum's brand and value proposition, shows the already-validated Amazon/AMZN
investment example (feature 009/010) as a static, human-readable snapshot, and captures
CTA-driven early-access registrations, qualitative feedback, and validation-funnel events.
The Amazon example is captured once from a real `run_investment_workflow` run (no live LLM
calls at request time), converted into a stable presentation/read model. No DCF, valuation,
thesis, bull/bear, or committee logic is touched by any of this (FR-014, FR-016 — still
true, unconditionally).

**This revision (new)**: Publish the application on AWS using a serverless architecture
the spec specifies in detail: the landing page (`GET /` only) becomes a **pre-rendered
static file** served from **S3 behind CloudFront**; every dynamic operation (register,
feedback, events, metrics — including each one's own GET/POST routes) is served by the
**existing, unmodified FastAPI route handlers**, now invoked through **AWS Lambda** (via a
Mangum adapter) behind a **Lambda Function URL**, with **CloudFront routing by path**
between the two origins. Production persistence moves from SQLite to **DynamoDB** — the
only genuine *application* code addition this revision requires, and it is added as a new
implementation of the existing `Storage` protocol (constitution Principle X: "depending on
protocols/interfaces that infrastructure implements"), not a rewrite of anything upstream
of it. Local development is unaffected: `uv run uvicorn aic.public.app:app --reload` keeps
using `SqliteStorage` exactly as before (FR-021: "SQLite MAY remain available for local
development/tests").

## Technical Context

**Language/Version**: Python 3.12+ (unchanged).

**Primary Dependencies (existing, unchanged)**: `fastapi`, `uvicorn` (local dev only now),
`jinja2`, `python-multipart`.

**Primary Dependencies (new this revision)**:
- `mangum` — adapts the existing ASGI `FastAPI` app to the Lambda Function URL's request/
  response event shape with no route-handler changes. Chosen over hand-writing a native
  Lambda handler because it lets every existing route (`register.py`/`feedback.py`/
  `events.py` logic, Pydantic validation, Jinja2 rendering for the GET form/confirmation
  pages) run unmodified — see research.md Decision 7.
- `boto3` — AWS SDK, for the new `DynamoDbStorage` implementation of the existing `Storage`
  protocol. Already an implicit transitive presence in most Python AWS tooling; added
  explicitly since `aic.public.storage` will import it directly.

**Storage**: Two `Storage` protocol implementations now coexist, selected by which code
constructs the app, never by an environment-variable branch inside `app.py` itself
(preserves the existing dependency-injection pattern exactly):
- `SqliteStorage` (existing, unchanged) — used by local dev (`app.py`'s module-level
  `app = create_app()`) and every test.
- `DynamoDbStorage` (new) — used only by the new `src/aic/public/lambda_handler.py`, which
  constructs `create_app(storage=DynamoDbStorage(...), presentation=...)` and wraps the
  result in `Mangum(...)`.

**Testing**: `pytest` with FastAPI's `TestClient` (unchanged) for everything except
`DynamoDbStorage`, which is tested against a local DynamoDB emulation (`moto`'s DynamoDB
mock, already a common lightweight choice — no real AWS calls in the test suite; see
research.md Decision 8). `ruff check .` and `mypy src` MUST still pass across the whole
repo.

**Target Platform**:
- Local: unchanged — `uv run uvicorn aic.public.app:app --reload`, `SqliteStorage`.
- Production: no persistent server process anywhere (FR-023, SC-014). The landing page is
  a static file on S3; every dynamic route runs inside AWS Lambda, invoked only per-request.

**Project Type**: Unchanged — single Python project, no `backend/`/`frontend/` split. This
revision adds one new script (static-site build) and one new module
(`lambda_handler.py` + a `DynamoDbStorage` class), not a new project.

**Performance Goals**: Unchanged — N/A beyond "responsive for a small validation
experiment." Lambda cold starts are the one new latency consideration; not addressed with
provisioned concurrency in this pass (adds cost for a low-traffic validation experiment —
constitution VIII, "low operating cost").

**Constraints (updated this revision)**:
- MUST NOT modify `aic.dcf`, `aic.domain`, `aic.research`, `aic.bullbear`, `aic.committee`,
  `aic.report`, or `aic.workflow` (FR-016 — still true, unconditionally).
- MUST NOT make a real OpenAI call at request-serving time, in Lambda or locally (FR-022 —
  still true).
- MUST NOT introduce authentication/sessions (still true — Non-Goals).
- MUST NOT use Lightsail, EC2, systemd, Caddy, an always-running Python server, or SQLite as
  the production persistence layer (spec.md "The deployment MUST NOT use" — new, explicit,
  and directly overrides the first revision's design).
- MUST NOT introduce API Gateway "unless implementation requires it and the additional
  cost/complexity is justified" (spec.md) — Lambda Function URLs satisfy the HTTP-invocation
  requirement without it; see research.md Decision 7.
- This execution environment has no AWS credentials and cannot provision or verify real AWS
  resources — every deployment artifact produced for this feature MUST be reviewed and
  executed by the user with their own AWS credentials.
- The custom domain name, AWS account/region, and any AWS resource identifiers are required
  user inputs and MUST NOT be invented or assumed available.

## Deployment Technical Context

**Static site (S3 + CloudFront)**: Only the landing page (`GET /`) plus its static assets
(`style.css`, `track.js`, `reveal.js`) are pre-rendered/copied into a build output directory
and uploaded to a **private** S3 bucket, fronted by CloudFront using **Origin Access
Control** (OAC) — not a public bucket, not the S3 static-website-hosting endpoint (which
has no native HTTPS; spec.md notes this explicitly). A new script,
`scripts/build_static_site.py`, renders `templates/landing.html` (with `templates/
base.html`) through the *same* Jinja2 environment and `AmazonPresentation` snapshot
`app.py` already uses — confirmed safe: no template references `request`/`url_for`, so
rendering outside a live FastAPI request context produces byte-identical output. This
script does not touch `register.html`/`feedback.html` — see next paragraph for why.

**Dynamic routes (Lambda)**: `GET/POST /register` (+ `/register/confirmation`), `GET/POST
/feedback` (+ `/feedback/confirmation`), `POST /events`, and `GET /metrics` all run inside
one Lambda function that wraps the **existing, unmodified** `aic.public.app` FastAPI app
via Mangum. Reasoning for including the GET form/confirmation pages in Lambda's scope
(rather than pre-rendering them too): spec.md's S3 content list names only "landing page
HTML" explicitly, and FR-020 says Lambda "at minimum" supports `register`/`feedback`/
`events`/`metrics` as whole operations, not just their POST halves; splitting a single path
prefix's GET and POST across two different origins would require method-aware CloudFront
routing (Lambda@Edge/CloudFront Functions), which is meaningfully more complexity for zero
functional benefit here — routing the whole `/register*` and `/feedback*` path prefixes to
Lambda is simpler, still spec-compliant, and reuses 100% of the existing route code
unmodified. Exposed via a **Lambda Function URL** (`AuthType: AWS_IAM`), not API Gateway —
matches spec.md's explicit instruction to prefer "the simplest available Lambda HTTP
invocation mechanism" before adding another managed service. CloudFront reaches the
Function URL using **Origin Access Control for Lambda** (supported since 2024) so the
Function URL cannot be invoked directly, bypassing CloudFront — see research.md Decision 7.

**CloudFront routing**: one distribution, two origins, path-pattern behaviors:
`/register*` → Lambda, `/feedback*` → Lambda, `/events*` → Lambda, `/metrics*` → Lambda,
default (`/`, `/static/*`) → S3.

**Persistence (DynamoDB)**: Three tables mirroring the existing SQLite schema 1:1 — the
"simplest design that satisfies the access patterns" per spec.md, and the design most
directly traceable to the already-tested `Storage` protocol's existing method contracts.
On-Demand capacity mode (spec.md explicit preference). `registrations` is keyed by
`email_normalized` directly (not a generated ID) so the idempotent-registration requirement
(FR-017) is a single atomic `put_item` with `ConditionExpression="attribute_not_exists(
email_normalized)"` — no separate uniqueness index needed. See data-model.md for full
table designs.

**IAM**: One Lambda execution role, scoped to `PutItem`/`GetItem`/`Query`/`Scan` on exactly
the three table ARNs plus the standard CloudWatch Logs write permissions — no
account-administrator or wildcard-resource policy (FR-024's IAM requirement).

**TLS & DNS**: One ACM certificate for the custom domain, **in `us-east-1`** regardless of
which region other resources live in (a hard CloudFront requirement — ACM certificates
used by CloudFront must be requested in `us-east-1`). DNS: an ALIAS/CNAME record pointing
the custom domain at the CloudFront distribution's domain name, in Route 53 if the zone is
already there, otherwise at whatever registrar/DNS provider the user already uses (spec.md:
Route 53 not required).

**Deployment mechanism**: Shell scripts + AWS CLI (no Terraform/CDK, matching the reasoning
already established in research.md Decision 6 for a single feature this size, extended here
to the new resource set) — provisioning script(s) for the DynamoDB tables, Lambda function
+ Function URL + IAM role, and CloudFront distribution + S3 bucket + OAC, plus a release
script that rebuilds the static site, uploads it to S3, invalidates the CloudFront cache
for `/` and `/static/*`, and updates the Lambda function code. Concretely replaces the five
`deploy/*` files from the first revision — new filenames are proposed in the updated
Project Structure below; actually writing them is `/speckit-tasks` + implementation work,
not this planning pass.

**Scale/Scope**: `src/aic/public/` gains one new module (`lambda_handler.py`) and one new
class (`DynamoDbStorage`, likely within `storage.py` alongside `SqliteStorage`, same file,
same `Storage` protocol). One new top-level script
(`scripts/build_static_site.py`). `deploy/` is rewritten (five old files removed, replaced
with S3/CloudFront/Lambda/DynamoDB-oriented artifacts — enumerated in Project Structure).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Check | Result |
|---|---|---|
| I. Evidence Before Opinion | Unchanged — presentation model still preserves FACT/CALCULATION/ASSUMPTION labels; no new claims invented | PASS |
| II. LLM Proposes, Code Computes | Unchanged — no LLM call in any request path, Lambda included | PASS |
| III. Structured Outputs Only | Unchanged, and reinforced: `DynamoDbStorage` still speaks the same Pydantic-modeled `Storage` protocol as `SqliteStorage` — no new untyped interface introduced | PASS |
| IV. Bull/Bear Symmetry | N/A — unchanged | N/A |
| V. Explicit Assumptions | Unchanged | PASS |
| VI. Deterministic Valuation | Unchanged — DCF engine untouched | PASS |
| VII. Traceability | Unchanged | PASS |
| **VIII. Minimal Architecture, No Premature Infrastructure** | AWS deferral condition remains satisfied (application built and tested, per the earlier revision's finding). The specific services now mandated (S3, CloudFront, Lambda, DynamoDB) are not among VIII's still-excluded items (no Kubernetes, no microservices/Kafka/Redis, no RDS/PostgreSQL, no complex event-driven architecture) and are explicitly, narrowly scoped by spec.md's own "Explicitly Forbidden" list to stay minimal | **PASS** |
| IX. No RAG in MVP | N/A — unchanged | N/A |
| X. Provider Abstraction | **Directly exercised, not violated**: `DynamoDbStorage` is a second implementation of the pre-existing `Storage` protocol, exactly the pattern this principle calls for ("depending on protocols/interfaces that infrastructure implements") | PASS |

**Historical gap, already justified (not repeated here)**: The original "frontend
application" exclusion override is documented in Complexity Tracking below and remains
accurate; nothing about this revision changes that reasoning.

**New consideration, not a violation**: Swapping SQLite for DynamoDB in production is a
spec-mandated (FR-021), narrowly-scoped change to one already-abstracted layer
(`aic.public.storage`), consistent with — not in tension with — constitution Principle X.
No new Complexity Tracking entry is needed for it.

No other unjustified violations.

## Project Structure

### Documentation (this feature)

```text
specs/011-public-mvp-validation/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
src/aic/public/                     # existing package — unchanged except as noted (*)
├── __init__.py
├── app.py                          # FastAPI app factory + route wiring — UNCHANGED;
│                                    # the same app object is used locally (uvicorn) and
│                                    # in Lambda (via lambda_handler.py + Mangum)
├── lambda_handler.py               # (*) NEW — `handler = Mangum(create_app(
│                                    #   storage=DynamoDbStorage(...), presentation=...))`;
│                                    #   the only file that knows this app can run on Lambda
├── presentation.py                 # UNCHANGED
├── registration.py                 # UNCHANGED
├── feedback.py                     # UNCHANGED
├── events.py                       # UNCHANGED
├── storage.py                      # (*) gains `DynamoDbStorage`, a second implementation
│                                    #   of the existing `Storage` protocol, alongside the
│                                    #   unchanged `SqliteStorage`
├── templates/                      # UNCHANGED (still used both for local serving AND as
│                                    #   the source templates for the static-site build)
└── static/                         # UNCHANGED (copied verbatim into the static-site build
                                     #   output; still also served locally by FastAPI)

data/
└── amazon_snapshot.json            # UNCHANGED

scripts/
├── capture_amazon_snapshot.py      # UNCHANGED
└── build_static_site.py            # NEW — renders landing.html via the same Jinja2
                                     # environment/snapshot as app.py, copies static/,
                                     # writes a build output directory (e.g. `dist/`) ready
                                     # for S3 upload

deploy/                             # REWRITTEN this revision — the five files from the
│                                    # first revision (quorum.service, Caddyfile,
│                                    # provision.sh, release.sh, backup_to_s3.sh) are
│                                    # superseded and will be removed; replaced with:
├── provision_data.sh               # one-time: create the 3 DynamoDB tables (AWS CLI)
├── provision_lambda.sh             # one-time: create the Lambda function, its execution
│                                    # role/policy, and its Function URL
├── provision_cdn.sh                # one-time: create the private S3 bucket, the
│                                    # CloudFront distribution (2 origins, OAC for both),
│                                    # and request the ACM certificate
├── release_static.sh               # repeatable: run build_static_site.py, sync `dist/`
│                                    # to S3, invalidate the CloudFront cache
└── release_lambda.sh               # repeatable: package src/aic/public/ + dependencies
                                     # and update the Lambda function code
                                     # (exact script boundaries/names may be refined during
                                     # /speckit-tasks — this is the planning-level shape)

tests/unit/public/                  # existing tests unchanged; gains new test module(s)
│                                    # for DynamoDbStorage (moto-mocked, no real AWS calls)
├── public_fakes.py
├── test_public_presentation.py
├── test_public_registration.py
├── test_public_feedback.py
├── test_public_events.py
├── test_public_storage.py          # gains DynamoDbStorage coverage alongside existing
│                                    # SqliteStorage coverage (same file, or a sibling
│                                    # test_public_storage_dynamodb.py — decided in tasks)
└── test_public_app.py              # unchanged — still exercises the FastAPI app directly
                                     # via TestClient, independent of which Storage it's
                                     # constructed with
```

**Structure Decision**: Still a single existing Python project, no `backend/`/`frontend/`
split, no new top-level project. The only genuinely new *application* code is
`lambda_handler.py` (a thin adapter, ~5 lines) and `DynamoDbStorage` (a new class behind an
existing protocol) — everything else in `src/aic/public/` is unchanged. `deploy/` and
`scripts/build_static_site.py` remain outside `src/`, containing no code the running
application imports, consistent with the existing "no code that only exists for deployment
leaks into the application" boundary.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|---------------------------------------|
| Constitution VIII: "a frontend application" is explicitly excluded from the MVP, but this feature adds one (`src/aic/public/` + Jinja2 templates) | Feature 011's entire purpose is market validation with real external users, which is impossible without something a browser can render; the spec (explicit, detailed user requirement) and the pre-written `aic-brand-landing` skill both authorize this exception, and the constitution's own Governance section ranks an explicit user requirement above architecture principles | A CLI-only or notebook-only demonstration was rejected because it cannot reach "individual investors, serious retail investors, finance professionals" as the spec's target audience requires, nor can it collect the CTA-click/registration/feedback signals the spec's Success Criteria (SC-001–SC-006) depend on |
