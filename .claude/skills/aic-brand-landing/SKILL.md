# AIC Brand & Landing Skill

## Purpose

Design and implement the public-facing validation experience
for AI Investment Committee.

The objective is not to build a complete SaaS product.

The objective is to validate whether the target audience:

1. understands the product,
2. trusts the proposition,
3. wants to try it,
4. is willing to identify themselves,
5. and can successfully reach the MVP.

---

## Product positioning

AI Investment Committee is an AI-assisted investment research workflow.

The MVP transforms:

Data
→ Research
→ Bull Case
→ Bear Case
→ Valuation
→ Committee
→ Investment Memo

into a structured and auditable investment analysis.

The product should be positioned around:

- structured investment research
- evidence-backed reasoning
- deterministic valuation
- explicit bull/bear analysis
- committee-style decision making
- traceability

Avoid positioning the product as:

- an autonomous trading bot
- a stock-picking oracle
- guaranteed investment advice
- an AI that predicts stock prices

---

## Landing page objective

The landing page exists to validate demand.

Primary CTA:

"Request early access"

or an equivalent professional formulation.

Secondary CTA:

"See how it works"

The visitor should understand the proposition within seconds.

---

## Landing structure

Preferred structure:

1. Hero
2. Problem
3. Product mechanism
4. Example investment analysis
5. Why it is different
6. Trust / methodology
7. Early-access CTA
8. Minimal registration form

---

## Hero

The hero should communicate:

- what AIC is
- who it is for
- what problem it solves
- why it is different

Avoid generic AI language.

Avoid:

"Revolutionizing investing with AI."

Prefer concrete language around:

"evidence-backed investment research"

and

"structured investment committee analysis."

---

## Product demonstration

Use the Amazon MVP validation as the canonical demonstration.

The example should show:

- company
- financial inputs
- evidence
- DCF valuation
- bull case
- bear case
- committee recommendation

The demonstration must clearly distinguish:

FACT
ASSUMPTION
CALCULATION

Do not imply that the Amazon result is an investment recommendation to the visitor.

---

## Brand

The visual identity should communicate:

- institutional
- analytical
- modern
- trustworthy
- precise

Avoid:

- crypto aesthetics
- excessive gradients
- generic AI imagery
- futuristic robot imagery
- excessive animations

The product should feel closer to:

investment research
+
institutional workflow
+
modern software

than to a consumer AI chatbot.

---

## Registration

Keep registration extremely simple.

Initial form:

- email
- optional name
- optional role

Do not require:

- company details
- investment portfolio
- financial information
- lengthy questionnaires

The objective is conversion measurement, not user profiling.

---

## Analytics

Track at minimum:

- landing_visit
- hero_cta_click
- demo_view
- demo_interaction
- signup_started
- signup_completed
- early_access_requested

The funnel should allow calculation of:

CTA conversion
signup conversion
completion rate

---

## Infrastructure

An existing S3 bucket may be used for static hosting.

A custom domain should be used.

Do not introduce a complex backend unless required.

Prefer the smallest architecture capable of:

landing
→ CTA
→ registration
→ confirmation
→ analytics

---

## Validation principle

The landing page is an experiment.

Do not optimize for visual complexity.

Optimize for learning.

Every major design decision should answer:

> What hypothesis are we testing?

---

## CTA

The CTA should create a clear next step.

Preferred language:

"Request early access"

"Join the private beta"

"Test the investment workflow"

Avoid:

"Buy now"

"Start trading"

"Get guaranteed insights"

---

## Output

When asked to implement this skill:

1. inspect the existing repository
2. inspect existing MVP validation
3. preserve existing product terminology
4. reuse the Amazon validation as the canonical demo
5. create the smallest viable landing
6. keep the MVP investment engine untouched
7. add analytics hooks
8. test the registration flow
9. report the resulting funnel