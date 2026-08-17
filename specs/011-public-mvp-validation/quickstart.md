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

## 4. Deploy to AWS — S3 + CloudFront + Lambda + DynamoDB (manual, requires the user's own AWS credentials and a real domain)

**Superseded note**: an earlier revision of this section described a single-Lightsail-
instance runbook (`deploy/provision.sh` + `deploy/release.sh` + `deploy/backup_to_s3.sh`).
`spec.md` now explicitly forbids that architecture. This section describes the current one
(research.md Decision 7); the old `deploy/*` files still exist on disk but are stale and
will be replaced during `/speckit-tasks` + implementation.

This section requires things this environment does not have: an AWS account/credentials
and a real domain name. Nothing here can be executed or verified in this sandbox — treat
it as a runbook to follow locally, not a step that has already run. Exact script names are
proposed in plan.md's Project Structure; the sequence below describes the *steps*, which
will not change even if a script name does during tasks/implementation.

**Prerequisites**:

- A domain name you control, and access to its DNS (either directly, or via delegation to
  Route 53). Substitute it for every `YOUR_DOMAIN` placeholder below — none is invented or
  assumed available (plan.md Constraints).
- AWS credentials via **IAM Identity Center (SSO)** — short-lived, expiring session
  credentials, never a static access key/secret key pair sitting on disk (never
  hard-coded, never committed, never pasted into a chat/tool transcript either way):
  1. Enable IAM Identity Center for the account, if not already (AWS Console → IAM
     Identity Center — a standalone AWS account can enable this without belonging to an
     AWS Organization).
  2. Create a **Permission Set** (IAM Identity Center → Permission sets → Create →
     "Custom permissions policy") and paste in `deploy/iam-policy-provisioning.json`'s
     contents (committed in this repo — it's a policy *document*, not a secret; unchanged
     in substance from the IAM-user version, just attached as a Permission Set instead of
     to a long-lived user). Name it e.g. `QuorumDeploymentProvisioning`. It's scoped to
     exactly what `provision_data.sh`/`provision_lambda.sh`/`provision_cdn.sh` need:
     DynamoDB/Lambda/S3 actions restricted to resource names starting with `quorum-`, IAM
     restricted to creating/configuring the one Lambda execution role
     (`quorum-public-lambda-role`) `provision_lambda.sh` itself creates — not
     administrator access. CloudFront/ACM actions can't be scoped below `Resource: "*"`
     (their ARNs don't exist until after creation), which is normal for these two
     services.
  3. Assign yourself to the target AWS account with that Permission Set (IAM Identity
     Center → AWS accounts → the account → Assign users or groups).
  4. Run `aws configure sso` **yourself, directly in your own terminal** — type
     `! aws configure sso` in the prompt so it runs outside this conversation (see the
     session's own guidance on the `!` prefix). It walks through your SSO start URL,
     region, and account/permission-set choice, then opens a browser to authenticate — no
     secret key is ever typed or stored. This writes a profile (e.g. `quorum-deploy`) to
     `~/.aws/config`.
  5. Add `export AWS_PROFILE=quorum-deploy` to your shell's startup file (`~/.bashrc` for
     Git Bash, `$PROFILE` for PowerShell) — not a one-off `export`, since each command in
     an assistant-driven session starts a fresh shell and a startup-file entry is what
     actually persists across those. None of the `deploy/*` scripts need changes for this:
     every `aws` CLI call and every `boto3.resource(...)` already relies on the default
     credential chain, which resolves SSO profiles the same way it resolves static ones.
  6. The SSO session expires (typically hours, depending on how the Identity Center
     instance is configured) — when a script starts failing with an expired-token/
     unauthorized error, run `! aws sso login --profile quorum-deploy` yourself to
     refresh it. This periodic re-auth is the point, not a rough edge: nothing long-lived
     is sitting on disk to leak.
  7. Ongoing releases (`release_static.sh`/`release_lambda.sh`) only need
     `lambda:UpdateFunctionCode`, `s3:PutObject`/`DeleteObject` on the one bucket, and
     `cloudfront:CreateInvalidation` — no IAM permissions at all. Create a second, narrower
     Permission Set for day-to-day use once initial provisioning (T081–T083 / §4.1–4.3
     below) is done, if you want the SSO role itself least-privileged per phase too.

**4.1 Provision the data layer (one time)**: create the three DynamoDB tables
(`registrations` keyed by `email_normalized`, `feedback_submissions` keyed by
`feedback_id`, `validation_events` keyed by `event_id`; On-Demand capacity — data-model.md).

**4.2 Provision the Lambda backend (one time)**: create the Lambda function (packaged
`src/aic/public/` + dependencies + `lambda_handler.py`), its execution role (scoped to the
three table ARNs + CloudWatch Logs — research.md Decision 7 part 4), and its Function URL
(`AuthType: NONE` — research.md Decision 7 amendment: OAC/SigV4 signing cannot work for a
plain HTML `<form>` POST. Access is instead restricted by a shared secret, generated locally
into `deploy/.origin-verify-secret`, that `lambda_handler.py` requires on every request).

**4.3 Provision the static/CDN layer (one time)**: create a private S3 bucket, request an
ACM certificate for `YOUR_DOMAIN` **in `us-east-1`** (required for CloudFront regardless of
where other resources live), and create the CloudFront distribution with two origins (S3
via OAC, the Lambda Function URL via a shared-secret custom header — research.md Decision 7
amendment) and the path-pattern behaviors from research.md Decision 7 (`/register*`,
`/feedback*`, `/events*`, `/metrics*` → Lambda; default → S3). Point `YOUR_DOMAIN`'s DNS at
the resulting CloudFront distribution domain name (ALIAS/CNAME, via Route 53 if already in
use, otherwise the existing DNS provider).

**4.4 Release the static site**:

```sh
uv run python scripts/build_static_site.py
```

then sync the build output directory to the S3 bucket and invalidate CloudFront's cache
for `/` and `/static/*`. Expected: renders `landing.html` through the same Jinja2
environment/snapshot `app.py` uses locally, byte-for-byte equivalent to what `GET /` would
render (verified: no template references `request`/`url_for` — research.md Decision 7).

**4.5 Release the Lambda backend**: re-package `src/aic/public/` + dependencies and update
the Lambda function code. Safe to run independently of 4.4 (FR-028: static and backend
releases are independently repeatable, neither recreates DynamoDB data).

**4.6 Confirm end-to-end**:

- `https://YOUR_DOMAIN/` loads the pre-rendered landing page over a valid ACM/CloudFront
  TLS certificate.
- Repeat the manual walkthrough from §3 above against `https://YOUR_DOMAIN/` instead of
  `127.0.0.1:8000` — every outcome listed there (US1-US6) MUST hold identically for the
  Lambda-served routes (register/feedback/events/metrics); the landing page itself is now
  static, so its content should match what §3 step 1-3 describe, just not re-rendered per
  visit.
- Confirm `landing_visit` events are being recorded via the new client-side beacon
  (research.md Decision 9) — submit a page load, then check `https://YOUR_DOMAIN/metrics`
  reflects it.
- `https://YOUR_DOMAIN/metrics` returns the same JSON shape as local (see the deployment
  note on this route in `contracts/public-interface.md` — it is intentionally
  unauthenticated).

**4.7 Verify redeployment safety (FR-027/SC-012/SC-013)**: submit a real test registration,
note it in `/metrics`, then repeat 4.4 (static release) and separately 4.5 (Lambda release)
— confirm the registration and its `/metrics` count are unaffected by either.

## Non-goal reminder

This quickstart's deployment section (§4) is a manual runbook, not something this
environment executes — every AWS/DNS action requires the user's own credentials and domain,
and nothing above has been run or verified here.
