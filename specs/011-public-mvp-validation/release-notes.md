# Release Notes: Public MVP Validation (Feature 011)

## 2026-08-17 — First production deployment

**Production URL**: https://d2bd8kteboaclo.cloudfront.net/ (CloudFront default domain — no
custom domain purchased yet; T097/T086 remain open until one is bought, at which point
`DOMAIN=yourdomain.com ./deploy/provision_cdn.sh` adds it to this same distribution and
requests the ACM certificate).

**Architecture**: S3 + CloudFront (static landing page) + Lambda via Mangum (dynamic routes)
+ DynamoDB — research.md Decision 7, amended same day (see below).

**AWS resource identifiers** (account `064374365425`, region `eu-central-1` for everything
except the ACM certificate, which CloudFront always requires in `us-east-1`):

* S3 bucket: `quorum-public-site-064374365425`
* CloudFront distribution ID: `EB7QPHIMA507`
* Lambda function ARN: `arn:aws:lambda:eu-central-1:064374365425:function:quorum-public`
* Lambda execution role: `quorum-public-lambda-role`
* DynamoDB tables: `quorum-registrations`, `quorum-feedback-submissions`,
  `quorum-validation-events`
* ACM certificate: none yet (no custom domain)

**Known issue fixed same day — CloudFront OAC cannot sign POST requests from real
browsers**: The original design routed the Lambda origin through CloudFront's Origin Access
Control (OAC) with the Function URL's `AuthType: AWS_IAM`. Every real `POST /register` /
`POST /feedback` failed with `403 InvalidSignatureException`, because OAC's SigV4 signing
requires the *viewer* request to already carry a precomputed `x-amz-content-sha256`
body-hash header — something no plain HTML `<form>` submission ever sends. Replaced with the
standard shared-secret custom-header pattern: the Function URL's `AuthType` is now `NONE`,
CloudFront injects a fixed secret (`deploy/.origin-verify-secret`, generated locally, never
committed) as the `x-quorum-origin-verify` header on every request to the Lambda origin, and
`lambda_handler.py` rejects anything that doesn't carry it. See research.md Decision 7's
2026-08-17 amendment for the full writeup.

**Verified end-to-end** (T087–T099): static landing page (200), `POST /register` (303 →
confirmation, duplicate-email idempotency confirmed), `POST /feedback` (303 → confirmation),
`POST /events` (200), `GET /metrics` (200, counts correct), independent `release_static.sh`
and `release_lambda.sh` releases both leave DynamoDB data untouched, no investment-engine
code (`aic.dcf`/`research`/`bullbear`/`committee`/`report`/`workflow`) touched or reachable
from any public route.

**Not yet done**: T086/T097 (custom domain + its ACM cert — no domain purchased yet), T092's
`landing_visit` beacon (needs a real browser load to fire, not exercisable via `curl`).
