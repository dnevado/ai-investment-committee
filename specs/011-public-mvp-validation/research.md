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

## Decision 6 (revised 2026-08-16, now SUPERSEDED by Decision 7 below — preserved for history): Deployment — single Lightsail instance, not S3-only static hosting

**Superseded note**: `spec.md` was replaced again the same day with a complete,
explicit spec that forbids everything this decision chose (Lightsail, EC2, systemd, Caddy,
SQLite in production) and mandates S3 + CloudFront + Lambda + DynamoDB instead. See
Decision 7. This section is kept for history only — do not implement against it.

**Context for the revision**: The original Decision 6 (below, preserved for history)
deferred deployment entirely. The current spec.md now scopes Feature 011 to actually
publishing the application on AWS behind a custom domain. The constitution's AWS-deferral
condition ("until the local vertical slice has been validated") is met — the application is
built and its full test suite passes (see plan.md Constitution Check) — so this decision
replaces the old one rather than amending it as a footnote.

**Decision**: Run the existing, unmodified FastAPI application on a single AWS Lightsail
instance (`uvicorn` under `systemd`), with Caddy on the same instance handling TLS
termination and automatic Let's Encrypt certificate issuance/renewal for the user-supplied
custom domain. The production SQLite file lives on the instance's persistent volume and is
backed up periodically to a private S3 bucket. No Terraform/CDK — a small set of shell
scripts under `deploy/` (AWS CLI + `rsync`/`scp`) is the entire deployment mechanism, run
manually by the user with their own AWS credentials (this environment has none).

**Why not literal "S3 public artifact" (pure S3 static-website hosting)**: S3 static-website
hosting can only serve pre-built static files — it cannot execute the FastAPI app's Python
code or persist writes from `POST /register`, `POST /feedback`, or `POST /events`. The
current spec.md itself says registration, feedback, and analytics are "existing" and must
carry through to the published site, and separately says the backend is "frozen" (no
Python changes in this phase). Reconciling both meant S3 could not be the primary hosting
surface without either (a) rewriting the app to be stateless/static (contradicts "frozen"
and "existing registration/feedback/analytics"), or (b) moving persistence to a networked
service like DynamoDB (a code change, and a new AWS service the constitution doesn't
currently call for). S3's role instead became private backups of the one stateful file the
app depends on — genuinely useful, without requiring any application change.

**Alternatives considered**:
- *AWS Lambda + API Gateway (e.g., via Mangum)*: rejected. Lambda's execution environment
  has no persistent local disk across invocations/instances (only ephemeral `/tmp`), which
  is fundamentally incompatible with a single-file SQLite database used for durable
  registration/feedback/event storage, without migrating storage to a networked database —
  a code change this deployment-only pass must not make.
- *ECS Fargate + Application Load Balancer*: rejected as more infrastructure than "simple"
  calls for — a container registry, task definitions, an ALB, and a VPC/security-group
  setup for a single low-traffic instance is meaningfully more moving parts than one
  Lightsail instance, for no benefit at this traffic scale.
- *AWS App Runner*: a reasonable simpler alternative to ECS, but its instances also use
  ephemeral storage that isn't guaranteed to persist across redeploys/scaling events —
  same SQLite-durability problem as Lambda unless paired with an external volume/database,
  which reintroduces the complexity Lightsail's plain persistent disk avoids.
- *Terraform or AWS CDK for the infrastructure*: rejected for this "simple" tier — this
  environment cannot install providers or run `plan`/`apply` to verify the configuration
  actually works, so a state file I cannot test is riskier than a small, readable,
  independently-auditable shell/AWS-CLI script the user runs and can inspect line by line.
- *S3 + CloudFront static mirror of `src/aic/public/static/`*: considered as an optional
  optimization (lower latency for CSS/JS via CDN edge caching); not implemented in this
  pass — the app already serves these files correctly itself via `StaticFiles`, and adding
  a second delivery path is unjustified complexity for a validation-stage traffic volume
  (constitution VIII).

---

### Original Decision 6 (2026-08-15, superseded above — preserved for history)

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

---

## Decision 7 (2026-08-16, current): Deployment — S3 + CloudFront (static landing page) + Lambda via Mangum (dynamic routes) + DynamoDB, no API Gateway

**Context**: `spec.md` was replaced a second time with a complete, explicit specification
that mandates this exact service set and explicitly forbids Decision 6's approach
(Lightsail/EC2/systemd/Caddy/production SQLite). This decision supersedes Decision 6.

**Decision, broken into its parts**:

1. **Landing page → static, on S3 behind CloudFront (OAC, private bucket)**. A new script,
   `scripts/build_static_site.py`, renders `templates/landing.html`/`base.html` through the
   same Jinja2 environment and `AmazonPresentation` snapshot `app.py` already uses, and
   copies `static/` verbatim, into a build output directory uploaded to S3. Verified safe:
   no template in `src/aic/public/templates/` references `request` or `url_for`, so
   rendering outside a live FastAPI request produces byte-identical HTML. S3's own
   static-website-hosting endpoint is not used (spec.md notes it has no native HTTPS);
   CloudFront is the public HTTPS endpoint, reaching the bucket via Origin Access Control
   rather than a public-read bucket policy — AWS's documented secure pattern for this.

2. **Every dynamic route stays inside the existing FastAPI app, run on Lambda via Mangum,
   behind a Lambda Function URL — not API Gateway.** `GET/POST /register` (+
   `/register/confirmation`), `GET/POST /feedback` (+ `/feedback/confirmation`), `POST
   /events`, and `GET /metrics` are routed to Lambda as whole path prefixes (`/register*`,
   `/feedback*`, `/events*`, `/metrics*`); everything else (`/`, `/static/*`) goes to S3.
   Routing whole prefixes — rather than trying to send a path's GET to S3 and its POST to
   Lambda — avoids needing method-aware routing (Lambda@Edge/CloudFront Functions), which
   would be real added complexity for zero benefit at this traffic scale. This choice means
   `register.html`/`feedback.html`/their confirmation pages are *not* pre-rendered by
   `build_static_site.py` — they continue to be served by the same `Jinja2Templates`
   rendering already in `app.py`, just executed inside Lambda instead of `uvicorn`. Mangum
   is chosen over a hand-written native Lambda handler specifically so that zero route
   logic, validation, or template rendering code has to be rewritten or duplicated.

   **Amendment (2026-08-17): OAC for the Lambda origin does not work for POST and was
   replaced with a shared-secret custom header.** The original design below (CloudFront
   reaches the Function URL via Origin Access Control, `AuthType: AWS_IAM`) was implemented
   and deployed, but every real `POST /register` / `POST /feedback` request returned
   `403 InvalidSignatureException`. Root cause, confirmed against AWS's own OAC-for-Lambda
   documentation: CloudFront's SigV4 signing of the origin request requires the *viewer*
   request to already carry a precomputed `x-amz-content-sha256` body-hash header — a plain
   HTML `<form>` POST from a real browser never sends one (only a scripted client that
   computes the hash itself, per AWS's own example, would work). CloudFront Functions
   (which could otherwise inject that header automatically) have no access to the request
   body at all; only Lambda@Edge does, and only with a 40KB text-body cap, mandatory
   `us-east-1` deployment, and its own IAM trust/versioning setup — real added
   infrastructure just to make signing work, contradicting this feature's "no complex
   backend" principle. Instead, the Lambda origin now uses the standard shared-secret
   pattern for restricting a public custom origin to one CloudFront distribution: the
   Function URL's `AuthType` is `NONE` (technically public), CloudFront injects a fixed
   secret value as a custom header (`x-quorum-origin-verify`) on every request it forwards
   to the Lambda origin (`deploy/provision_cdn.sh`, secret generated locally by
   `deploy/provision_lambda.sh`, never committed), and `lambda_handler.py` rejects any
   request missing or mismatching that header before doing any work (no DynamoDB access).
   This works identically for GET and POST, any body, with zero client-side JavaScript.
   The original (superseded) design:

   ~~CloudFront reaches the Function URL via **Origin Access Control for Lambda** (supported
   since 2024), so the Function URL cannot be invoked directly, bypassing CloudFront and its
   caching/logging — the Function URL's own `AuthType` is set to `AWS_IAM`, and only
   CloudFront's OAC principal is granted `lambda:InvokeFunctionUrl`.~~

3. **Production persistence → DynamoDB, three tables, On-Demand capacity.** One new class,
   `DynamoDbStorage`, implements the existing `Storage` protocol (`storage.py`) — the exact
   pattern constitution Principle X calls for. `registrations` is keyed directly by
   `email_normalized` (not a generated ID as the partition key) so the idempotent-
   registration requirement (FR-017) is a single atomic `put_item` with
   `ConditionExpression="attribute_not_exists(email_normalized)"`, with no separate unique
   index needed — see data-model.md.

4. **IAM**: one Lambda execution role, scoped to `PutItem`/`GetItem`/`Query`/`Scan` on
   exactly the three table ARNs, plus standard CloudWatch Logs write access. No
   administrator or wildcard-resource policy (FR-024).

5. **TLS/DNS**: one ACM certificate for the domain, requested in `us-east-1` specifically
   (a hard requirement for any certificate CloudFront uses, regardless of where other
   resources live — easy to get wrong). DNS: an ALIAS/CNAME at the domain's existing
   provider (or Route 53 if already in use) pointing at the CloudFront distribution domain.

**Rationale**: Every element above is either explicitly named by spec.md ("The deployment
MUST use: S3... CloudFront... Lambda... DynamoDB... IAM... ACM") or is the most literal,
lowest-complexity reading of an ambiguous point in it (the GET-route routing question in
part 2). Mangum + unmodified FastAPI app is the single biggest complexity-reduction lever
available here: it means the *entire* existing, already-tested route layer (six user
stories' worth of behavior, all of `tests/unit/public/test_public_app.py`) needs zero
changes to run on Lambda — only the storage backend and the entry-point wrapper are new.

**Alternatives considered**:
- *API Gateway (REST or HTTP API) in front of Lambda*: rejected — spec.md explicitly
  excludes API Gateway from the baseline and explicitly instructs evaluating "the simplest
  available Lambda HTTP invocation mechanism" first; Lambda Function URLs satisfy the same
  need (a public HTTPS-invokable endpoint with a request/response shape Mangum understands)
  with one fewer managed service and no additional per-request cost tier.
  a native Lambda handler (`def handler(event, context): ...` dispatching by path) was
  rejected because it means re-implementing routing, form parsing, and Pydantic validation
  that `aic.public.app`'s FastAPI routes already do correctly and are already tested;
  Mangum's translation layer is a well-established, narrowly-scoped dependency, not a
  second implementation of the same logic.
- *Splitting GET/POST for `/register` and `/feedback` across S3 and Lambda respectively*:
  considered, to more literally match "S3 stores landing page HTML" reading narrowly;
  rejected because CloudFront cache behaviors route by path pattern, not HTTP method — same-
  path dual-origin routing needs Lambda@Edge or a CloudFront Function to inspect the method
  and branch, which is more moving parts than routing the whole path prefix to Lambda, for
  a distinction (static vs. dynamic *form display*) that has no user-facing effect either
  way (the form page's content is identical regardless of which origin renders it).
- *One DynamoDB table with a type-discriminator attribute (single-table design)*: considered
  (a common DynamoDB pattern for related entities with overlapping access patterns);
  rejected in favor of three tables because `registrations`/`feedback_submissions`/
  `validation_events` have no query patterns that span entities (nothing ever needs "all
  items of any type for X"), so single-table design's main benefit — one round-trip for
  multi-entity access patterns — doesn't apply, and three plain tables map most directly
  onto the three existing SQLite tables and the three existing `Storage` protocol method
  groups, minimizing the conceptual distance between the two implementations (spec.md: "The
  simplest design that satisfies the access patterns SHOULD be selected").
- *DynamoDB Streams / EventBridge for anything*: not introduced — nothing in the spec's
  requirements needs asynchronous fan-out; would be exactly the "unnecessary managed
  service" spec.md's Explicitly Forbidden section is warning against.

## Decision 8 (2026-08-16): Testing `DynamoDbStorage` — `moto`, no real AWS calls

**Decision**: Test the new `DynamoDbStorage` class against `moto`'s DynamoDB mock (an
in-process, in-memory emulation of the DynamoDB API), added as a new `dev` dependency-group
entry. No real AWS account, credentials, or network access is used or required by the test
suite — consistent with every other test in this repository.

**Rationale**: Constitution's Quality/Observability section and this feature's own FR-016/
SC-007 require the full test suite to stay green and network-free. `moto` intercepts
`boto3` calls at the HTTP layer, so `DynamoDbStorage`'s actual production code path
(`boto3` resource/client calls, `ConditionExpression`, key schemas) is exercised exactly as
written — not a hand-rolled fake that could silently drift from real DynamoDB semantics
(e.g., `moto` correctly rejects a `put_item` that violates a `ConditionExpression`,
verifying the FR-017 idempotency logic actually works, not just that the Python code
compiles).

**Alternatives considered**:
- *A hand-written in-memory fake `Storage` implementation, like `SqliteStorage`'s
  `:memory:` mode*: rejected as the primary test vehicle for `DynamoDbStorage` specifically
  — the whole point of testing this class is to verify its actual DynamoDB API usage
  (condition expressions, key schema, item shape) is correct; a hand-written fake that just
  mimics the `Storage` protocol's Python-level behavior would not catch a wrong
  `ConditionExpression` string or an incorrect key schema, defeating the purpose. (A
  lightweight fake MAY still be used elsewhere, e.g. for `lambda_handler.py`-level tests
  that don't care about DynamoDB specifics — decided during tasks.)
- *DynamoDB Local (the real downloadable DynamoDB server, run via Docker/Java)*: rejected
  for the default test suite — requires either Docker or a JVM available in the test
  environment, a heavier dependency than `moto` for equivalent fidelity on the operations
  this project actually uses (`put_item` with a condition expression, `get_item`, `scan`/
  `query` for metrics aggregation). Could still be used for a separate, optional
  integration-test tier later if `moto`'s emulation ever proves insufficient — not needed
  for this feature's scope.

## Decision 9 (2026-08-16): `landing_visit` measurement moves from server-side to a client-side beacon in production

**The gap**: `GET /`'s existing implementation records one `landing_visit` `ValidationEvent`
server-side, specifically so it is not dependent on client-side JS (original spec Edge
Case, still quoted in contracts/public-interface.md). Once the landing page becomes a
pre-rendered static file served by CloudFront/S3 (Decision 7), that route only ever
executes once, at build time — never per real visitor — so this server-side count
mechanism silently stops working in production. SC-004 still requires landing visits to be
part of the reportable funnel, so this cannot be left unresolved.

**Decision**: In production, `landing_visit` is recorded the same way the *other* funnel
events already are — a client-side beacon. `static/track.js` gains one additional call,
fired on `DOMContentLoaded` on the landing page specifically, POSTing `{"event_type":
"landing_visit"}` to `/events` (which already routes to Lambda via CloudFront path
behavior, Decision 7). No new event type, no new route, no new infrastructure — reuses the
exact mechanism `hero_cta_click`/`demo_view`/etc. already use.

**Trade-off, stated explicitly rather than hidden**: this makes `landing_visit` counts
subject to the same JS-disabled/ad-blocker undercounting the original design deliberately
avoided by recording it server-side. Given the chosen architecture is static-hosting-first
(spec.md's explicit, repeated instruction), this trade-off is a direct, unavoidable
consequence of that choice — not an oversight. Locally (`uvicorn`, `SqliteStorage`), the
existing server-side recording in `GET /` is unaffected and remains the more robust
mechanism there; production and local intentionally differ on this one point.

**Alternatives considered**:
- *Parse CloudFront/S3 access logs for visit counts*: rejected — meaningfully more
  infrastructure (log delivery configuration, a parser, somewhere to store the parsed
  counts) for one metric, in a spec that explicitly warns against "any additional AWS
  service that is not required by the public validation funnel."
  a scheduled Lambda to periodically tally logs into DynamoDB: same objection, plus adds
  latency between a visit and it being reflected in `/metrics` (batch, not real-time).
- *A Lambda@Edge / CloudFront Function on the default (S3) behavior that increments a
  counter on every request*: technically closer to "server-side" in spirit, but is
  meaningfully more complex to write/deploy/test than a one-line addition to the already-
  existing `track.js` beacon pattern, for a validation-stage experiment where "maximize
  reliable learning per unit of engineering effort" (spec.md Guiding Questions) argues for
  the simpler option.
