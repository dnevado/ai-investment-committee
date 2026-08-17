# Feature Specification: Public MVP Validation

**Feature Branch**: `011-public-mvp-validation`

**Status**: Final / Pre-deployment

## Objective

Feature 011 provides the final public validation layer for Quorum.

The landing page, Amazon demonstration, registration flow, feedback mechanism and minimum validation analytics are considered functionally complete.

The remaining objective is to make the existing validation experience publicly accessible using the smallest practical AWS serverless architecture, with a strong emphasis on minimal operational cost and minimal infrastructure.

The public deployment MUST use:

* Amazon S3 for static landing-page hosting
* Amazon CloudFront for HTTPS/custom-domain delivery
* AWS Lambda for the small public backend required by CTA, registration, feedback and validation events
* Amazon DynamoDB for persistent public validation data
* AWS IAM for least-privilege access between Lambda and DynamoDB/S3 where required
* AWS Certificate Manager for the TLS certificate used by CloudFront
* Route 53 only if the domain DNS is hosted in Route 53; otherwise the existing DNS provider MAY be used

The deployment MUST NOT use:

* Amazon Lightsail
* EC2
* systemd
* Caddy
* an always-running Python server
* a persistent FastAPI/Uvicorn process in AWS
* SQLite as the production persistence layer
* Kubernetes
* ECS/EKS
* RDS
* ElastiCache
* API Gateway unless implementation requires it and the additional cost/complexity is justified
* any additional AWS service that is not required by the public validation funnel

The Python application code remains the canonical local implementation for now.

The public AWS backend is a thin Lambda adapter around the minimum registration/feedback/event persistence functionality required by the landing page. The investment workflow itself continues to run locally and is NOT executed by Lambda.

The validation boundary is:

```text
Landing
→ Example
→ CTA
→ Registration
→ Feedback
→ Analytics
→ AWS Serverless Deployment
→ Custom Domain
```

The production architecture is intentionally split:

```text
                    ┌─────────────────────┐
                    │   Custom Domain     │
                    └──────────┬──────────┘
                               │
                         HTTPS / CloudFront
                               │
                 ┌─────────────┴─────────────┐
                 │                           │
                 ▼                           ▼
          ┌─────────────┐              ┌─────────────┐
          │ S3 Bucket   │              │ AWS Lambda  │
          │ Static Site │              │ Public API  │
          └─────────────┘              └──────┬──────┘
                                              │
                                              ▼
                                      ┌──────────────┐
                                      │  DynamoDB    │
                                      │ registrations│
                                      │ feedback     │
                                      │ events       │
                                      └──────────────┘
```

The existing Amazon investment analysis is published as a static validated snapshot. Lambda MUST NOT execute the investment workflow or call the OpenAI API for normal page visits.

The purpose of this feature remains:

> Do real target users find this AI-assisted investment committee workflow useful enough to want to try it, register, or provide feedback?

---

# User Scenarios & Testing

## User Story 1 - Understand the Value Proposition Within Seconds (Priority: P1)

A first-time visitor — an individual investor, serious retail investor, or finance professional — lands on the public Quorum page and, without any prior knowledge of the system's internal architecture, understands within seconds what AI Investment Committee is, who it is for, and what problem it solves.

**Why this priority**: This is the entry point of the entire validation funnel.

**Independent Test**: Show only the page's opening section to a person from the target audience and confirm they can state, in their own words, what AIC does and who it is for.

### Acceptance Scenarios

1. **Given** a first-time visitor with no prior context, **When** they open the page, **Then** they see AIC's name, a concise value proposition, and a plain-language summary of the investment workflow:

   ```text
   Data → Research → Investment Thesis → Bull Case → Bear Case → DCF → Committee → Memo
   ```

2. **Given** the same visitor, **When** they read the opening section, **Then** nothing implies that AIC is an autonomous trading bot, stock-picking oracle, financial adviser, or source of guaranteed returns.

---

## User Story 2 - Inspect a Real, Trustworthy Investment Example (Priority: P1)

The visitor wants proof the workflow produces something substantive before trusting it enough to register.

They inspect the existing validated Amazon (AMZN) investment case and can distinguish reported facts, calculations, forecast assumptions and AI-generated analysis.

### Acceptance Scenarios

1. **Given** the Amazon example section, **When** the visitor reads it, **Then** they see:

   * Amazon.com, Inc.
   * AMZN
   * DCF implied value per share
   * committee recommendation
   * conviction
   * concise investment thesis
   * bull case
   * bear case
   * evidence traceability

2. Every displayed figure or claim is visibly distinguishable as:

   * reported fact
   * calculation
   * forecast assumption
   * AI-generated analysis

3. Every financial figure shown traces back to the existing validated Feature 009/010 Amazon workflow output.

4. The public page uses a deliberately captured snapshot and MUST NOT recompute the Amazon analysis per visitor.

---

## User Story 3 - Express Interest With Minimal-Friction Registration (Priority: P1)

A visitor convinced by the proposition and example wants to register interest in early access.

The public landing page contains a clear CTA.

The CTA invokes the public Lambda backend.

The backend persists the registration in DynamoDB.

No account, password or authentication system is created.

### Acceptance Scenarios

1. **Given** a visitor on the page, **When** they click the primary CTA, **Then** they reach the lightweight registration mechanism.

2. The registration requires only:

   * email

3. The role/investor profile MAY be collected to support qualified-interest measurement.

4. The registration MUST NOT require:

   * password
   * account
   * OAuth
   * authentication session
   * subscription
   * payment

5. **Given** a valid email, **When** the visitor submits, **Then** Lambda persists the registration in DynamoDB and returns a successful response.

6. **Given** an invalid email, **When** the visitor submits, **Then** the backend rejects the request and does not record a completed registration.

7. Duplicate submissions using the same normalized email MUST NOT create duplicate completed registrations.

---

## User Story 4 - Provide Qualitative Feedback (Priority: P2)

A visitor — whether or not they registered — can provide qualitative feedback.

Feedback is submitted to the Lambda backend and persisted in DynamoDB.

### Acceptance Scenarios

1. The feedback mechanism presents exactly these six questions:

   1. What would you use AIC for?
   2. What part of the analysis is most valuable?
   3. What would prevent you from trusting the output?
   4. Would you use it regularly?
   5. Would you pay for it?
   6. What would you expect before using it for a real investment decision?

2. Feedback submission MUST NOT require prior registration.

3. Feedback MAY optionally include an email.

4. Lambda persists the feedback with a timestamp.

5. Every successfully submitted feedback response remains retrievable for later review.

---

## User Story 5 - Measure the Validation Funnel (Priority: P2)

The product owner needs to retrieve validation activity for a given time window.

The public backend records the minimum events necessary to evaluate the experiment.

### Minimum Event Types

```text
landing_visit
hero_cta_click
workflow_cta_click
example_cta_click
final_cta_click
demo_view
demo_interaction
signup_started
signup_completed
feedback_submitted
early_access_requested
```

The additional CTA variants are retained because the landing page contains multiple CTA positions.

### Acceptance Scenarios

1. Visitor activity generates validation events where technically measurable.

2. Events contain at minimum:

   * event type
   * timestamp

3. Events MAY additionally contain:

   * device classification
   * source
   * request metadata required for aggregate analysis

4. Analytics failure MUST NOT prevent registration or feedback submission.

5. The system MUST make it possible to compute:

   ```text
   CTA conversion rate
   = CTA clicks / landing page visitors

   Registration conversion rate
   = completed registrations / landing page visitors

   Qualified-interest rate
   = qualified registrations / completed registrations
   ```

6. Duplicate registration submissions MUST NOT inflate completed-registration counts.

---

## User Story 6 - See Explicit Trust and Disclaimer Messaging (Priority: P3)

The visitor sees explicit trust/disclaimer language near the Amazon example and near the registration CTA.

### Required positioning

The public experience MUST communicate that:

* valuation is model-dependent
* assumptions affect results
* AI-generated analysis can be wrong
* outputs are research assistance
* outputs are not financial advice
* source information should be independently verified

The public page MUST NOT imply:

* guaranteed returns
* financial advice
* product-market fit
* autonomous trading
* guaranteed investment performance

---

# User Story 7 - Deploy the Public Validation Layer Using AWS Serverless Infrastructure (Priority: P1)

The already-built and locally validated public experience becomes publicly accessible through a minimal AWS architecture.

The deployment is intentionally serverless.

There is no long-running application server.

### Architecture

```text
Browser
   │
   ▼
Custom Domain
   │
   ▼
CloudFront
   │
   ├──────────────► S3
   │                 │
   │                 └── index.html
   │                     CSS
   │                     JS
   │                     assets
   │                     Amazon snapshot
   │
   └──────────────► Lambda
                       │
                       ▼
                    DynamoDB
```

CloudFront provides the HTTPS/custom-domain delivery layer while S3 stores the static site. S3 website endpoints themselves do not provide HTTPS, so the public HTTPS endpoint is CloudFront rather than the raw S3 website endpoint.

The preferred S3/CloudFront configuration uses a private S3 bucket with CloudFront Origin Access Control rather than exposing the bucket directly. AWS documents this pattern for secure static websites.

### AWS Responsibilities

#### S3

S3 stores:

* landing page HTML
* CSS
* JavaScript
* static assets
* public Amazon presentation snapshot
* any other static content required by the landing page

S3 MUST NOT store:

* registration data
* feedback data
* analytics events
* credentials
* secrets

#### CloudFront

CloudFront provides:

* HTTPS
* custom domain delivery
* CDN caching
* S3 origin access
* public static content delivery

#### Lambda

Lambda provides the minimum dynamic backend:

```text
POST /register
POST /feedback
POST /events
GET  /metrics
```

The Lambda implementation MUST remain thin.

It MUST NOT:

* run the investment workflow
* invoke OpenAI for normal public requests
* execute DCF calculations
* generate investment theses
* execute Bull/Bear analysis
* execute Committee logic
* modify Feature 009/010 financial logic

Lambda exists only to provide the public validation persistence boundary.

#### DynamoDB

DynamoDB is the production persistence layer for public validation data.

The initial deployment SHOULD use DynamoDB On-Demand capacity mode because the validation workload is expected to be small, irregular and experimental. On-Demand provides pay-per-request capacity without requiring provisioned throughput planning.

DynamoDB stores at minimum:

```text
registrations
feedback_submissions
validation_events
```

The implementation MAY use:

* one DynamoDB table with typed entity records
* or multiple DynamoDB tables

The simplest design that satisfies the access patterns SHOULD be selected.

For the MVP, no relational database is required.

#### IAM

Lambda MUST have only the DynamoDB permissions it needs.

The deployment MUST NOT use broad administrator permissions for the runtime Lambda role.

#### TLS

The public custom domain MUST use HTTPS through CloudFront.

An ACM certificate is required for the custom domain.

#### DNS

The custom domain MAY remain with the existing registrar/DNS provider.

Route 53 is NOT required solely for this feature.

If Route 53 is already used, it MAY manage the DNS record pointing the domain to CloudFront.

---

# Requirements

## Functional Requirements

### FR-001

The system MUST present a public page establishing AIC's brand identity:

> AI Investment Committee

and a concise plain-language value proposition.

### FR-002

The page MUST include the investment workflow explanation:

```text
Data → Research → Investment Thesis → Bull Case → Bear Case → Deterministic DCF → Committee Decision → Investment Memo
```

### FR-003

The page MUST present one representative real-company example:

```text
Amazon / AMZN
```

using the existing validated Feature 009/010 workflow output.

### FR-004

The Amazon example MUST be human-readable and MUST NOT expose raw Python/Pydantic representations.

### FR-005

The example MUST distinguish:

* FACT
* CALCULATION
* ASSUMPTION
* INTERPRETATION
* OPINION

using the existing evidence classification.

### FR-006

The page MUST present a primary CTA for early access/validation.

### FR-007

The CTA MUST provide a lightweight registration mechanism requiring only an email.

### FR-008

Registration MUST NOT require authentication, password, account creation or payment.

### FR-009

The system MUST provide the six-question qualitative feedback mechanism.

### FR-010

The system MUST record the minimum validation event set.

### FR-011

The system MUST support calculation of the three funnel conversion rates.

### FR-012

Disclaimer language MUST be present near both the Amazon example and CTA/registration.

### FR-013

The public presentation MUST consume the existing validated workflow through a stable presentation/read model.

### FR-014

Public-facing concerns MUST NOT leak into:

* DCF domain logic
* investment domain models
* research logic
* Bull/Bear logic
* Committee logic
* LLM provider implementations
* workflow orchestration

### FR-015

The public experience MUST NOT claim or imply:

* product-market fit
* financial advice
* guaranteed returns
* autonomous trading

### FR-016

All pre-existing automated tests MUST remain green.

Observable behavior of:

```text
aic.dcf
aic.research
aic.bullbear
aic.committee
aic.report
aic.workflow
```

MUST remain unchanged.

### FR-017

Duplicate registrations using the same normalized email MUST NOT be counted as multiple completed registrations.

### FR-018

Registration and feedback MUST work independently.

### FR-019 — AWS Static Hosting

The public landing page MUST be deployable as static content to an Amazon S3 bucket.

The browser MUST NOT require a running Python web server to render the landing page.

### FR-020 — AWS Public Backend

The dynamic public operations MUST be handled by AWS Lambda.

At minimum:

```text
register
feedback
events
metrics
```

MUST be supported by the Lambda backend.

### FR-021 — DynamoDB Persistence

Production registrations, feedback submissions and validation events MUST be persisted in DynamoDB.

SQLite MUST NOT be the production persistence mechanism.

SQLite MAY remain available for local development/tests.

### FR-022 — No Public Workflow Execution

The AWS public deployment MUST NOT execute:

```text
run_investment_workflow
```

for normal visitor requests.

The Amazon example MUST remain a static published snapshot.

### FR-023 — Cost-Minimal Architecture

The deployment MUST avoid always-running compute.

No EC2, Lightsail, ECS, EKS or equivalent persistent compute service is permitted.

The default architecture is:

```text
S3
+
CloudFront
+
Lambda
+
DynamoDB On-Demand
```

with ACM and DNS as required for HTTPS/custom-domain operation.

### FR-024 — Lambda Backend Scope

The Lambda backend MUST be limited to the public validation concerns.

It MUST NOT become a replacement for the existing application architecture.

The investment workflow continues to execute locally.

### FR-025 — Analytics Resilience

If analytics/event recording fails, the registration or feedback operation MUST still be allowed to succeed whenever possible.

Analytics is secondary to the validation funnel itself.

### FR-026 — Secrets

OpenAI credentials and other development secrets MUST NOT be required by the public Lambda.

The public deployment MUST NOT expose:

```text
AIC_OPENAI_API_KEY
```

or equivalent credentials.

### FR-027 — Data Durability

DynamoDB is the durable production store for:

* registrations
* feedback
* validation events

Redeploying the static site or Lambda MUST NOT delete or overwrite existing DynamoDB data.

### FR-028 — Deployment Separation

Static deployment and backend deployment MUST be independently repeatable.

Updating:

```text
S3 static assets
```

MUST NOT require recreating the DynamoDB data.

Updating:

```text
Lambda code
```

MUST NOT recreate the DynamoDB data.

---

# Key Entities

## Early-Access Registration

Required:

* email

Optional:

* role/investor profile
* name if later reintroduced
* investment experience if later reintroduced
* sectors/companies of interest if later reintroduced
* free-text feedback if later reintroduced

Derived:

* timestamp
* qualified

Production storage:

```text
DynamoDB
```

## Feedback Submission

Contains:

* six answers
* timestamp
* optional email

Production storage:

```text
DynamoDB
```

## Validation Event

Contains:

* event type
* timestamp
* optional source
* optional device classification

Production storage:

```text
DynamoDB
```

## Amazon Demonstration Snapshot

A read-only projection of one validated Feature 009/010 `WorkflowResult`.

Production storage:

```text
S3
```

It MUST NOT be recomputed per visitor.

---

# AWS Deployment Constraints

## Required AWS Services

The production MVP SHOULD use only:

```text
Amazon S3
Amazon CloudFront
AWS Lambda
Amazon DynamoDB
AWS Certificate Manager
AWS IAM
```

DNS MAY use:

```text
Route 53
```

but Route 53 is not mandatory if the domain is managed elsewhere.

## Explicitly Forbidden for Feature 011

The deployment MUST NOT introduce:

```text
Lightsail
EC2
ECS
EKS
Kubernetes
RDS
ElastiCache
SQS
SNS
Step Functions
Cognito
API Gateway
```

unless a later implementation demonstrates that one is technically required and the feature scope is formally revised.

In particular, **API Gateway is intentionally excluded from the baseline architecture**.

If Lambda must be exposed publicly through an HTTP endpoint, the implementation SHOULD first evaluate the simplest available Lambda HTTP invocation mechanism that satisfies the required security and CORS behavior before adding another managed service.

The goal is not to build a generalized AWS platform.

The goal is to expose four tiny public validation operations at minimum cost.

---

# Production vs Local Architecture

## Local

The existing local architecture remains:

```text
CLI / Local Public App
        ↓
Application
        ↓
Domain
        ↑
Infrastructure
```

The existing Feature 009/010 workflow continues to run locally.

## Production

Production becomes:

```text
Browser
   │
   ├── static content ──► CloudFront ──► S3
   │
   └── validation actions ──► Lambda ──► DynamoDB
```

The investment engine remains outside the production request path.

---

# Success Criteria

## SC-001

A target user can understand AIC from the opening section.

## SC-002

100% of financial figures displayed in the Amazon example trace back to validated Feature 009/010 output.

## SC-003

A visitor can register using only an email.

## SC-004

The system can report:

* landing visits
* CTA clicks
* registrations
* demo engagement
* feedback submissions

and calculate all three funnel conversion rates.

## SC-005

100% of submitted feedback remains retrievable.

## SC-006

Required disclaimer language is visible near the Amazon example and CTA/registration.

## SC-007

Every pre-existing automated test continues to pass unmodified.

## SC-008

The public landing page is accessible over HTTPS using the real custom domain.

## SC-009

A real visitor can submit a registration from the public page and the registration is persisted in DynamoDB.

## SC-010

A real visitor can submit feedback without first registering.

## SC-011

A real visitor's validation events can be persisted and later queried for funnel measurement.

## SC-012

Redeploying the static site does not remove DynamoDB data.

## SC-013

Redeploying the Lambda does not remove DynamoDB data.

## SC-014

The public deployment does not require an always-running server.

## SC-015

The public deployment does not require the OpenAI API key.

## SC-016

The AWS public request path never executes the investment workflow.

---

# Assumptions

## Static Demonstration

The Amazon example is a deliberately captured snapshot of one validated workflow execution.

It is not recomputed live.

This prevents:

* OpenAI costs per visitor
* latency
* non-deterministic public results
* production dependency on the LLM provider

## Existing Investment Engine

Feature 011 consumes Feature 009/010.

It does not modify:

* DCF
* research
* Bull/Bear
* Committee
* workflow
* financial domain models

## Qualified Registration

A registration is considered qualified when the selected role matches one of the target audience categories:

* individual investor performing fundamental research
* serious retail investor
* finance/investment professional

Blank or out-of-audience selections are not qualified.

This remains an adjustable validation heuristic.

## Landing Page Content

The latest reviewed landing page remains the canonical presentation.

The current design direction is:

```text
Problem
→ Quorum Difference
→ How It Works
→ Real-World Validation
→ Why It's Different
→ Evidence
→ Challenge / Final CTA
```

The Amazon presentation remains based on real validated data.

The condensed thesis/bull/bear copy is presentation copy derived from the same validated conclusion and MUST NOT introduce new financial claims.

## Registration Form

The current simplified registration form contains:

* email
* role

The backend model MAY continue accepting additional optional fields for compatibility.

No new backend fields are required merely to support the current visual form.

## Analytics

Analytics exists only to validate the MVP.

It is not intended to become a general analytics platform.

## Cost

The architecture is optimized for a low-volume validation experiment.

AWS cost is expected to be usage-driven for the serverless components rather than based on an always-running server.

Actual AWS cost depends on traffic, storage, data transfer, Lambda execution and CloudFront usage. The architecture therefore minimizes idle infrastructure rather than promising a fixed monthly cost.

## Deployment

AWS credentials are supplied by the user/operator.

The deployment MUST NOT hard-code:

* AWS credentials
* account IDs
* domain names
* API keys
* DynamoDB secrets

## Python

Python remains the implementation language for the public backend Lambda.

The rest of the Python application continues to run locally.

The public Lambda is an adapter, not a second investment engine.

---

# Non-Goals

Feature 011 does NOT include:

* portfolio management
* portfolio tracking
* stock screening
* watchlists
* alerts
* trading signals
* brokerage integration
* trade execution
* order management
* subscriptions
* payment processing
* SaaS accounts
* authentication
* OAuth
* password management
* teams
* organizations
* billing
* production investment platform
* live market-data ingestion
* SEC ingestion
* scraping infrastructure
* RAG
* vector database
* embeddings
* autonomous agents
* multi-agent orchestration
* agent memory
* model routing
* new LLM providers
* DCF changes
* investment-engine changes
* Kubernetes
* EC2
* Lightsail
* ECS/EKS
* RDS
* API Gateway in the baseline architecture
* production FastAPI/Uvicorn server
* production SQLite
* generalized AWS infrastructure
* generalized analytics infrastructure

---

# Validation Boundary

Feature 011 ends at:

```text
Landing
→ Product Understanding
→ Example Analysis
→ CTA
→ Registration
→ Feedback
→ Measurement
→ Public HTTPS Deployment
```

It does NOT continue into:

```text
Registration
→ Full Account
→ Portfolio
→ Trading
→ Subscription
→ Production Investment Platform
```

---

# Post-Launch Decision Framework

Feature 011 produces evidence.

It does not decide the next architecture.

After the validation experiment, the product owner reviews:

### Signal A — Strong Interest

Users understand the proposition and demonstrate meaningful interest.

Next step:

* identify highest-value workflow
* define next product iteration
* design architecture required by that iteration

Do not architect speculatively before this evidence exists.

### Signal B — Interest but Unclear Proposition

Users register but do not understand the product sufficiently.

Next step:

* improve positioning
* improve UX
* repeat validation

Do not rearchitect the investment engine based on this signal.

### Signal C — Low Interest

The target audience does not demonstrate meaningful interest.

Next step:

* investigate positioning
* target audience
* problem selection

Do not invest in large-scale architecture on an unvalidated premise.

---

# Guiding Questions

Every implementation decision should maximize reliable learning per unit of engineering effort.

The resulting validation experiment should answer:

1. Do users understand what AIC does?
2. Do they believe the output is credible?
3. Is the evidence-backed approach valuable?
4. Is the Bull/Bear/Committee workflow useful?
5. Would they use this workflow for their own research?
6. Would they return to use it again?
7. Would they be willing to pay for it?

---

# Final Architecture Decision

The production architecture for Feature 011 is intentionally:

```text
                     QUORUM PUBLIC MVP

                         Custom Domain
                              │
                              ▼
                         CloudFront
                              │
                  ┌───────────┴───────────┐
                  │                       │
                  ▼                       ▼
             S3 Static Site          Lambda Backend
                  │                       │
                  │                       ▼
                  │                  DynamoDB
                  │                       │
                  └──── Static ───────────┘

        Local machine:
        Feature 009/010 workflow + OpenAI + tests
```

The central architectural rule is:

> **Keep the public surface serverless and minimal; keep the investment engine local until real-user validation justifies expanding the architecture.**

This preserves the original purpose of Feature 011: validate the product before investing in the next architectural phase.

