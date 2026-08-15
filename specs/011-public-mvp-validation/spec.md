# Feature Specification: Public MVP Validation

**Feature Branch**: `011-public-mvp-validation`

**Created**: 2026-08-15

**Status**: Draft

**Input**: User description: "Build the public-facing validation layer for AI Investment Committee... The purpose is to validate the MVP with real users before starting the next architectural phase... Create the minimum public validation system necessary to answer: 'Do real target users find this AI-assisted investment committee workflow useful enough to want to try it, register, or provide feedback?'" (full description supplied verbatim by the user; see also the project's `aic-brand-landing` skill for brand/positioning guidance consulted while writing this spec).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Understand the Value Proposition Within Seconds (Priority: P1)

A first-time visitor — an individual investor, serious retail investor, or finance
professional — lands on the AIC public page and, without any prior knowledge of the
system's internal architecture, understands within seconds what AI Investment Committee
is, who it is for, and what problem it solves.

**Why this priority**: This is the entry point of the entire validation funnel. If a
visitor doesn't grasp the value proposition immediately, no CTA, example, or registration
mechanism downstream matters — everything else in this feature depends on this working.

**Independent Test**: Show only the page's opening section to a person from the target
audience and confirm they can state, in their own words, what AIC does and who it's for,
without reading further or needing an explanation of DCF/LLM internals.

**Acceptance Scenarios**:

1. **Given** a first-time visitor with no prior context, **When** they open the page,
   **Then** they see AIC's name, a concise value proposition, and a plain-language summary
   of the investment workflow (Data → Research → Thesis → Bull → Bear → DCF → Committee →
   Memo) without technical jargon.
2. **Given** the same visitor, **When** they read the opening section, **Then** nothing on
   the page implies AIC is an autonomous trading bot, a stock-picking oracle, or a source of
   guaranteed investment returns.

---

### User Story 2 - Inspect a Real, Trustworthy Investment Example (Priority: P1)

The visitor wants proof the workflow produces something substantive before trusting it
enough to register. They inspect the existing, validated Amazon (AMZN) investment case and
can clearly tell apart what is a reported fact, what is a calculation, what is a forecast
assumption, and what is AI-generated analysis.

**Why this priority**: Credibility is the product's core value proposition (evidence
traceability, deterministic valuation, adversarial bull/bear analysis). Without a
trustworthy, legible example, the CTA has nothing to point to and the "credible and
professional" bar from this feature's own objective is not met.

**Independent Test**: Present the Amazon example section on its own and confirm a target
user can identify the DCF implied value per share, the committee recommendation and
conviction, the thesis/bull/bear summaries, and can correctly sort a sample of the
displayed figures into "fact," "assumption/calculation," or "AI analysis" buckets.

**Acceptance Scenarios**:

1. **Given** the Amazon example section, **When** the visitor reads it, **Then** they see:
   company identity (Amazon.com, Inc. / AMZN), DCF implied value per share, committee
   recommendation, conviction, a concise investment thesis, bull case, bear case, key
   assumptions, key risks, and evidence traceability — rendered in human-readable prose and
   labels, not as raw Python/Pydantic object output.
2. **Given** the same section, **When** the visitor looks at any individual figure or claim,
   **Then** it is visibly labeled or otherwise distinguishable as a reported fact, a
   calculation, a forecast assumption, or AI-generated analysis.
3. **Given** the same section, **When** the visitor reads it in full, **Then** every figure
   shown traces back to the existing, already-validated Feature 009/010 Amazon workflow
   output — no additional or different financial figures are introduced for the public
   presentation.

---

### User Story 3 - Express Interest With Minimal-Friction Registration (Priority: P1)

A visitor who is convinced by the value proposition and example wants to register interest
in early access. They click a clear call to action and complete a short form asking only
for an email address, with everything else optional.

**Why this priority**: Registration completion is the primary quantitative signal this
whole feature exists to measure ("do users want to try it, register"). Without a working,
low-friction registration path, the feature cannot answer its own stated objective.

**Independent Test**: Click the primary CTA, submit a form with only an email address
filled in, and confirm the registration succeeds and is recorded, with confirmation shown
to the visitor.

**Acceptance Scenarios**:

1. **Given** a visitor on the page, **When** they click the primary CTA, **Then** they are
   taken to a short registration form requesting only an email address as required, with
   role/investor profile, investment experience, sectors/companies of interest, and
   free-text feedback all optional.
2. **Given** the visitor fills in only the email field and submits, **When** the email is
   valid, **Then** the registration completes successfully and the visitor sees a
   confirmation that they have joined an early-access/validation program (not a live
   product).
3. **Given** the visitor submits an invalid or malformed email, **When** they submit,
   **Then** the form rejects it with a clear message and does not record a completed
   registration.
4. **Given** the visitor submits the form, **When** registration completes, **Then** no
   password, account, or authentication session is created or required.

---

### User Story 4 - Provide Qualitative Feedback (Priority: P2)

A visitor — whether or not they registered — wants to share qualitative impressions: what
they'd use AIC for, what they trust or don't, and whether they'd pay for it.

**Why this priority**: Quantitative funnel counts alone cannot answer "do users find this
useful" with enough nuance to guide the next architectural phase; qualitative answers are
this feature's other primary source of learning. Ranked after registration (P1) because a
working funnel is the prerequisite signal, while feedback depth is a secondary, richer
signal collected from a subset of visitors.

**Independent Test**: Open the feedback mechanism, answer the six specified questions,
submit, and confirm the response is stored (or exported) in a form that can be reviewed
later.

**Acceptance Scenarios**:

1. **Given** a visitor opens the feedback mechanism, **When** they view it, **Then** they
   see exactly these six questions: (1) what they'd use AIC for, (2) what part of the
   analysis is most valuable, (3) what would prevent them from trusting the output, (4)
   whether they'd use it regularly, (5) whether they'd pay for it, (6) what they'd expect
   before using it for a real investment decision.
2. **Given** the visitor answers and submits, **When** submission succeeds, **Then** the
   response is persisted (or exported) with enough context (timestamp; optionally the
   associated email if the visitor chose to link it) to be reviewed later, independent of
   whether that visitor also completed registration.

---

### User Story 5 - Measure the Validation Funnel (Priority: P2)

Someone evaluating this experiment (the product owner) needs to retrieve, for a given time
window, landing page visits, CTA clicks, completed registrations, demo/example engagement,
and feedback submissions, and compute the CTA conversion rate, registration conversion
rate, and qualified-interest rate from those counts.

**Why this priority**: Without measurement, this feature cannot fulfill its own stated
purpose — validating market interest before further investment. Ranked P2 because the
funnel only becomes meaningful once real visitor activity exists (US1-US3 first).

**Independent Test**: Generate a handful of simulated visits, CTA clicks, and registrations,
then confirm the recorded counts are retrievable and the three conversion rates can be
computed correctly from them.

**Acceptance Scenarios**:

1. **Given** a sequence of visitor actions (page visits, CTA clicks, demo engagement,
   registration starts/completions, feedback submissions), **When** each occurs, **Then**
   a corresponding event is recorded with enough detail (event type, timestamp) to be
   counted later.
2. **Given** a recorded set of events for a time window, **When** the counts are retrieved,
   **Then** CTA conversion rate (CTA clicks / landing page visitors), registration
   conversion rate (completed registrations / landing page visitors), and qualified-interest
   rate (qualified registrations / completed registrations) can all be computed from those
   counts alone.

---

### User Story 6 - See Explicit Trust and Disclaimer Messaging (Priority: P3)

A visitor evaluating whether to trust or register for AIC sees, near the example and near
the CTA/registration, explicit language stating that valuation is model-dependent,
assumptions affect results, AI-generated analysis can be wrong, outputs are research
assistance and not financial advice, and users should verify source information
independently.

**Why this priority**: Required for legal/ethical positioning and explicitly demanded by
the feature description ("must not imply that AIC provides financial advice or guarantees
investment returns"). Ranked P3 because it is cross-cutting content layered onto the
sections built in US1-US3 rather than a separate functional path of its own.

**Independent Test**: Review the full page and confirm disclaimer language is present near
both the Amazon example and the CTA/registration form, and that no instance of
guaranteed-return, financial-advice, or "get rich" language appears anywhere on the page.

**Acceptance Scenarios**:

1. **Given** the Amazon example section, **When** the visitor reads it, **Then** disclaimer
   language is visible in or immediately adjacent to that section.
2. **Given** the CTA/registration section, **When** the visitor reads it, **Then**
   disclaimer language is visible in or immediately adjacent to that section, explicitly
   stating the output is research assistance, not financial advice.

---

### Edge Cases

- What happens when a visitor submits the registration form with every optional field
  blank except email? It MUST still succeed — only email is required (US3/AC1).
- What happens when a visitor clicks the primary CTA multiple times without ever
  completing registration? Each click is counted individually toward the CTA-click metric;
  only a successful submission counts toward completed registrations.
- What happens when a visitor submits feedback without ever registering? It MUST still
  succeed and be recorded — feedback submission is a metric independent of registration
  completion (US4/US5).
- What happens when the same visitor registers more than once (e.g., resubmits with the
  same email)? Duplicate submissions with the same email MUST NOT be double-counted as
  separate completed registrations in the funnel metrics.
- What happens if the underlying Feature 009/010 Amazon workflow output is later
  regenerated with different assumptions or a newer model run? The public example MUST be
  updated deliberately (a new validated snapshot published), not silently diverge from what
  is actually displayed — the page MUST NOT recompute the example live per visitor (see
  Assumptions).
- What happens if a visitor's browser blocks the analytics mechanism (e.g., ad blocker)?
  Registration and feedback submission MUST still succeed independent of whether the
  visit/CTA-click event was successfully recorded — analytics failure must not block the
  core funnel actions.

## Non-Goals *(explicitly out of scope)*

Feature 011 exists to validate the MVP with real users, not to turn it into a production
SaaS platform. The following are explicitly out of scope for this feature, regardless of
how small an initial version might seem:

- **Product expansion**: portfolio management, portfolio tracking, stock screening,
  watchlists, alerts, trading signals, automated buy/sell recommendations, brokerage
  integration, trade execution, order management, real-time trading functionality.
- **Investment engine expansion**: any change to DCF methodology, valuation formulas, the
  financial forecasting engine, Bull/Bear methodology, Committee decision methodology,
  investment thesis generation logic, the evidence model, or financial domain models.
  Feature 011 consumes the already-validated MVP; it does not change its financial
  reasoning (reinforces FR-013/FR-014).
- **AI architecture**: new autonomous agents, multi-agent orchestration, autonomous loops,
  RAG, vector databases, embeddings infrastructure, agent memory, model-routing
  infrastructure, new LLM providers. No architectural expansion is justified solely by the
  public landing page.
- **User platform**: a complete SaaS account system — complex authentication, OAuth,
  password management, teams, organizations, roles and permissions, billing,
  subscriptions, payment processing, user dashboards, account settings. Registration
  exists only to measure qualified interest (FR-007/FR-008).
- **Infrastructure**: Kubernetes, microservices, queues, event buses, complex serverless
  architectures, production-grade distributed systems, unnecessary AWS services. An
  existing S3/static-hosting setup may be used where appropriate (see Assumptions).
- **Data acquisition**: market-data pipelines, real-time price feeds, financial API
  aggregation, automated SEC ingestion, or web-scraping infrastructure. The Amazon dataset
  already established for Feature 009/010 remains the canonical public demonstration
  dataset (reinforces FR-003).
- **Analytics**: a custom analytics platform. Only the minimum events needed to evaluate
  the validation funnel are collected (FR-010/FR-011) — the objective is measurement, not
  analytics infrastructure.
- **Design system**: a complete, general-purpose design system. Only the visual components
  needed for the landing page, product explanation, investment example, CTA, registration,
  and feedback are in scope. The visual identity should be reusable, but the implementation
  stays intentionally small.
- **Content platform**: a blog, CMS, newsletter infrastructure, SEO content engine, social
  publishing, or documentation portal. The public experience focuses on one product
  proposition and one validated investment example.
- **Legal/compliance platform**: a complete regulatory/compliance system. The MVP only
  needs appropriate research-assistance positioning (FR-012) — not a compliance platform.

**Validation boundary**: this feature's scope ends at

```text
Landing → Product understanding → Example analysis → CTA → Registration → Feedback → Measurement
```

and explicitly does **not** continue into

```text
Registration → Full account → Portfolio → Trading → Subscription → Production investment platform
```

The purpose of this boundary is to preserve learning speed: every implementation decision
in this feature should be justifiable by which of the acceptance scenarios above it serves,
not by anticipated future product needs.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST present a public page establishing AIC's brand identity ("AI
  Investment Committee") and a concise, plain-language value proposition, understandable
  without prior knowledge of the system's internal architecture.
- **FR-002**: The page MUST include a short, plain-language explanation of the investment
  workflow (Data → Research → Investment Thesis → Bull Case → Bear Case → Deterministic DCF
  → Committee Decision → Investment Memo).
- **FR-003**: The page MUST present one representative real-company example (Amazon/AMZN),
  reusing the existing validated Feature 009/010 workflow output, and MUST NOT introduce or
  fabricate financial figures beyond what that validated run produced.
- **FR-004**: The Amazon example MUST be rendered in human-readable form (no raw
  Python/Pydantic object representations) and MUST show: company identity, DCF implied
  value per share, committee recommendation, conviction, a concise investment thesis, bull
  case, bear case, and evidence traceability. (Amended: `key_assumptions`/`key_risks` are
  no longer rendered as their own landing-page sections — see Assumptions, "Landing page
  content trim." They remain present in `AmazonPresentation` and are not deleted from the
  data model, just not surfaced on this page.)
- **FR-005**: The Amazon example MUST visually or textually distinguish reported facts,
  calculations, forecast assumptions, and AI-generated analysis from one another, reusing
  the existing evidence classification (FACT / CALCULATION / ASSUMPTION /
  INTERPRETATION / OPINION) already produced by the engine.
- **FR-006**: The page MUST present a primary call to action inviting the visitor to
  request early access / join the validation program, and MAY present a secondary CTA
  linking to the example section.
- **FR-007**: The CTA MUST lead to a lightweight registration form collecting, at minimum,
  an email address (required), with role/investor profile, investment experience,
  sectors/companies of interest, and free-text feedback all optional.
- **FR-008**: Registration MUST NOT require a password, account, or authentication session
  — capturing interest (email plus optional fields) is sufficient.
- **FR-009**: The system MUST provide a qualitative feedback mechanism presenting the six
  specified questions (intended use, most valuable part, trust blockers, regular-use
  likelihood, willingness to pay, pre-conditions for real-money use) and MUST persist or
  export responses in a form reviewable later, independent of registration status.
- **FR-010**: The system MUST record, at minimum, the following events: landing page visit,
  primary-CTA click, demo/example view, demo/example interaction (where technically
  measurable), registration started, registration completed, and feedback submitted.
- **FR-011**: The system MUST make it possible to compute, for a given time window: CTA
  conversion rate (CTA clicks / landing page visitors), registration conversion rate
  (completed registrations / landing page visitors), and qualified-interest rate (qualified
  registrations / completed registrations).
- **FR-012**: The page MUST display, near both the Amazon example and the CTA/registration,
  explicit disclaimer language stating that valuation is model-dependent, assumptions
  affect results, AI-generated analysis can be wrong, outputs are research assistance and
  not financial advice, and users should verify source information independently.
- **FR-013**: The public-facing layer MUST consume the existing validated workflow output
  through a stable presentation/read model (Feature 009/010's `WorkflowResult`, or an
  equivalent boundary derived from it) rather than reimplementing or duplicating any DCF,
  valuation, thesis-generation, or committee-decision logic, and rather than directly
  coupling the public interface to internal workflow state. The existing dependency
  direction is preserved and extended, not bypassed:

  ```text
  CLI / Public interface
       ↓
  Application
       ↓
  Domain
       ↑
  Infrastructure
  ```

- **FR-014**: Public-facing concerns MUST NOT leak into DCF domain logic, investment
  domain models, LLM provider implementations, or LangGraph orchestration — this feature
  MUST NOT modify, extend, or introduce new logic into any of them.
- **FR-015**: The public experience MUST NOT claim or imply product-market fit, financial
  advice, or guaranteed investment returns anywhere on the page.
- **FR-016**: All pre-existing automated tests MUST remain green; this feature MUST NOT
  alter the observable behavior of `aic.dcf`, `aic.research`, `aic.bullbear`,
  `aic.committee`, `aic.report`, or `aic.workflow`.
- **FR-017**: The system MUST NOT double-count a duplicate registration (same email
  submitted more than once) as a separate completed registration in the funnel metrics.
- **FR-018**: Feedback submission and registration completion MUST each succeed and be
  recorded independently of one another (neither requires the other to have happened
  first).

### Key Entities

- **Early-Access Registration**: One visitor's expression of interest. Required: email.
  Optional: name, role/investor profile, investment experience, sectors/companies of
  interest, free-text feedback. Carries a timestamp and a derived "qualified" classification
  (see Assumptions) for the qualified-interest rate.
- **Feedback Submission**: One visitor's answers to the six qualitative questions.
  Carries a timestamp and an optional link to an Early-Access Registration (if the visitor
  chose to associate their email); usable and recorded whether or not that link exists.
- **Validation Event**: One occurrence of a measurable funnel action (landing page visit,
  CTA click, demo view, demo interaction, registration started, registration completed,
  feedback submitted). Carries an event type and timestamp, with no more visitor-identifying
  detail than the event type itself requires.
- **Amazon Demonstration Snapshot**: A read-only, human-readable projection of one
  already-validated Feature 009/010 `WorkflowResult` run for Amazon/AMZN, deliberately
  captured and published rather than recomputed per visitor (see Assumptions).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A first-time visitor from the target audience can correctly state AIC's value
  proposition (what it does, who it's for) after reading only the opening section.
- **SC-002**: 100% of the figures shown in the Amazon example trace back to Feature
  009/010's validated output — zero fabricated or independently-sourced figures appear on
  the public page.
- **SC-003**: A visitor can complete registration by filling in a single required field
  (email) and submitting.
- **SC-004**: For any given time window, the system can report landing page visits, CTA
  clicks, completed registrations, demo engagement (where measurable), and feedback
  submissions, and correctly compute the three defined conversion rates from those counts.
- **SC-005**: 100% of submitted feedback responses are retrievable or exportable for later
  qualitative review.
- **SC-006**: The public page contains disclaimer language adjacent to both the
  demonstration and the CTA/registration, with zero instances of guaranteed-return or
  financial-advice language anywhere on the page.
- **SC-007**: Every automated test that passed before this feature (221 as of Feature 010)
  continues to pass unmodified after this feature is implemented.

## Assumptions

- **Constitution interaction**: Constitution Principle VIII ("Minimal Architecture, No
  Premature Infrastructure") explicitly excludes "a frontend application" from the MVP.
  This feature deliberately introduces a public-facing page, which is a direct, conscious
  exception to that exclusion — authorized by this explicit, highly-detailed user request
  (and the project's own `aic-brand-landing` skill, written in advance specifically for
  this purpose), which the constitution's own governance section ranks above architecture
  principles when explicit. `/speckit-plan` for this feature MUST record this as an
  explicitly justified deviation (Complexity Tracking) rather than silently overriding it;
  a formal constitution amendment is a reasonable follow-up but is not a prerequisite this
  spec blocks on.
- **Static demonstration, not live recomputation**: The Amazon example is a deliberately
  captured, published snapshot of one validated `run_investment_workflow` execution (e.g.,
  produced via `scripts/mvp_amazon_acceptance.py` or an equivalent), not recomputed live
  per visitor. Recomputing live would call the real OpenAI API on every page view (cost,
  latency, and non-determinism — different visitors could see different AI-generated
  theses/decisions for "the same" example), which contradicts both this feature's "small
  and fast to iterate" goal and the constitution's minimal-infrastructure principle. This
  also keeps the public layer fully decoupled from requiring live LLM provider credentials
  in production.
- **Hosting/delivery mechanism is a planning-level decision**: Whether the page is a fully
  static site (consistent with the `aic-brand-landing` skill's mention of S3 static
  hosting + a custom domain) or served by a minimal backend for registration/feedback
  capture is left to `/speckit-plan`, which should favor the smallest architecture capable
  of landing → CTA → registration → confirmation → analytics, per that skill.
- **"Qualified" registration definition**: In the absence of a more specific definition, a
  registration is treated as "qualified" (for the qualified-interest rate) when the visitor
  selected a role/investor-profile value matching the stated target audience (individual
  investor performing fundamental research, serious retail investor, or finance/investment
  professional) rather than leaving that optional field blank or selecting an
  out-of-audience value. This is a simple, adjustable heuristic, not a hard business rule.
- **No production trading, brokerage, or portfolio functionality** is introduced by this
  feature, consistent with both the feature description's explicit exclusions and existing
  constitution principles.
- **Analytics event naming** follows the `aic-brand-landing` skill's convention
  (`landing_visit`, `hero_cta_click`, `demo_view`, `demo_interaction`, `signup_started`,
  `signup_completed`, `early_access_requested`) so downstream planning/implementation stays
  consistent with that existing guidance rather than inventing a second naming scheme.
  Extended, post-launch, with three positional CTA-click variants
  (`workflow_cta_click`/`example_cta_click`/`final_cta_click`, tracking distinct on-page
  CTA locations beyond the hero) and optional `device`/`source` fields on `ValidationEvent`
  (device classified server-side from the User-Agent header; source read from a `?src=`
  query parameter) — additive to the original event set, not a replacement for it.
- **Landing page content trim and visual identity iteration**: after initial
  implementation, direct user review found the page underwhelming and too
  financially dense. Two rounds of visual redesign followed (Material Design 3 →
  "Exhibit & Phosphor," an evidence-exhibit/financial-terminal design language, first on
  a light kraft-paper ground, then a deep-charcoal ground) and one content restructuring:
  the page now follows an explicit Problem → Quorum Difference → How It Works → Real-World
  Validation → Why It's Different → Evidence → Challenge/Final CTA narrative, the Amazon
  example's full thesis/bull/bear text was replaced with shorter curated copy (same real
  conclusion, condensed for legibility — not a new claim), `key_assumptions`/`key_risks`
  bullet lists were dropped from the page (FR-004), and the full evidence list was
  replaced by a 4-row sample table (`landing_sample_evidence`, data-model.md) plus a link
  through to registration. None of this touched `aic.dcf`/`aic.domain`/`aic.research`/
  `aic.bullbear`/`aic.committee`/`aic.workflow`, FR-013, or FR-014 — it is presentation-
  and copy-only iteration on top of the same real, validated data. This happened through
  direct implementation rather than a formal `/speckit-plan` cycle, consistent with how
  this project has handled other post-launch visual/copy refinement; this note exists so
  the gap between this spec's original mockup-level FR-004 wording and the shipped page is
  traceable rather than silent.
- **Further landing page iteration (CTA hierarchy, semantic color, simplified
  registration)**: a third design pass, explicitly scoped by the user to templates/CSS
  only (no backend/Python changes), made four further changes. (1) Color usage was
  tightened to be strictly semantic — green only for bull/positive, red only for
  bear/downside, amber only for the "WATCH" committee status specifically — with the
  primary CTA button recolored to a neutral bright fill so it no longer doubles as a
  fourth "accent" color competing with those meanings. (2) CTA copy changed from "Request
  early access" to "Get early access," repeated at exactly three in-content positions
  (hero, after the Amazon case, final section) plus the persistent nav, down from five;
  a distinct secondary action ("Explore the Amazon case →") was added to the hero. The
  `workflow_cta_click` event type remains valid in `EventType`/storage (unused, not
  removed — additive schema, per the existing analytics-extension note above). (3) The
  hero gained a compact real-figures strip (Enterprise Value / Equity Value / Value per
  Share, from the same `AmazonPresentation` fields already used lower on the page — no
  new data). (4) The registration form (FR-007) was reduced from six fields to two —
  email (required) and role (now radio buttons: Individual investor / Professional
  investor / Analyst-researcher / Other, mapped to the pre-existing `classify_qualified`
  values with no backend change) — dropping name/experience/interests/feedback from the
  form itself; `EarlyAccessRegistration` and the `/register` route are unchanged and still
  accept those fields if ever reintroduced. A backend addition to show real revenue/
  operating-income/FCF figures in the hero (which would have required a new
  `AmazonPresentation` field and a snapshot re-capture) was attempted and then explicitly
  reverted at the user's request to keep this pass presentation-only; the hero strip uses
  the three valuation figures already available instead.

## Post-Launch Decision Framework *(context — not implemented by this feature)*

This section is not a functional requirement of Feature 011; it records why the feature is
scoped the way it is, so the metrics and feedback this feature produces are interpreted
correctly rather than over- or under-read. Feature 011 produces evidence; it does not
itself decide the next architectural step, and it must not be read as proof that the
current architecture needs to be replaced.

After the validation experiment runs, a human reviews the results against three signals:

- **Signal A — Strong interest** (users understand the proposition and demonstrate
  meaningful interest): the appropriate next step is to identify the highest-value product
  workflow and define the next product iteration, then design whatever architecture that
  iteration actually requires — not to architect speculatively now.
- **Signal B — Interest but unclear proposition** (users register but don't understand the
  product): the appropriate next step is to improve positioning and UX and repeat
  validation — not to rearchitect the investment engine, which is not what this signal
  indicates is wrong.
- **Signal C — Low interest** (the target audience does not demonstrate meaningful
  interest): the appropriate next step is to investigate positioning, target audience, and
  problem selection — not to invest in large-scale architecture on an unvalidated premise.

Every major implementation decision within this feature should be traceable to one of these
guiding questions, which restate this feature's Success Criteria in plain language for
anyone reviewing the resulting data:

1. Do users understand what AIC does?
2. Do they believe the output is credible?
3. Is the evidence-backed approach valuable?
4. Is the Bull/Bear/Committee workflow useful?
5. Would they use this workflow for their own research?
6. Would they return to use it again?
7. Would they be willing to pay for it?

The implementation should maximize reliable learning obtained per unit of engineering
effort — this is the standard against which scope decisions during planning/implementation
should be judged when this spec does not explicitly resolve a question.
