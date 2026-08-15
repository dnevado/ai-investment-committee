# Data Model: Public MVP Validation

All new types live in `src/aic/public/` and are Pydantic `BaseModel`s (constitution
Principle III). None of these extend or modify any existing `aic.domain`/`aic.dcf`/etc.
type — `AmazonPresentation` is built *from* a `WorkflowResult` at capture time but is its
own independent read model.

## `AmazonPresentation` (`aic/public/presentation.py`)

The static, human-readable projection of one validated Amazon `WorkflowResult` (feature
009/010), loaded from `data/amazon_snapshot.json` at server startup.

| Field | Type | Notes |
|---|---|---|
| `company_name` | `str` | e.g. "Amazon.com, Inc." |
| `ticker` | `str` | e.g. "AMZN" |
| `implied_value_per_share` | `str` | pre-formatted with currency symbol, e.g. `"$75.07"` — formatting happens once at capture time, not in templates |
| `enterprise_value` | `str` | pre-formatted, e.g. `"$843.19B"` |
| `equity_value` | `str` | pre-formatted |
| `recommendation` | `str` | one of `Recommendation`'s values (`"BUY"`/`"WATCH"`/`"AVOID"`), copied verbatim from `CommitteeDecision.recommendation` |
| `conviction` | `float` | `CommitteeDecision`'s confidence, `0.0-1.0`, copied from the underlying `CommitteeDecisionDraft.confidence` surfaced in the decision |
| `thesis_summary` | `str` | `InvestmentThesis.summary`, unchanged |
| `bull_summary` | `str` | `bull_assessment.conclusion` |
| `bear_summary` | `str` | `bear_assessment.conclusion` |
| `key_assumptions` | `list[str]` | `InvestmentThesis.key_assumptions` |
| `key_risks` | `list[str]` | `InvestmentThesis.key_risks` |
| `evidence` | `list[EvidenceItemView]` | see below — every evidence item referenced anywhere in the run, deduplicated |
| `captured_at` | `date` | when the snapshot was generated (for "this example was last updated on..." framing, not a live timestamp) |

**Computed property** (not a stored field): `landing_sample_evidence -> list[EvidenceItemView]`
— returns up to 4 items for the landing page's compact evidence table, preferring a
curated set of real, known-good titles (one FACT, one CALCULATION, two ASSUMPTIONs) when
present, and falling back to whatever evidence exists otherwise so the table is never
empty. Added post-launch (see spec.md Assumptions "Landing page content trim") to reduce
financial-information density on the public page without inventing sample data — every
row is still a real, traceable `EvidenceItemView`, just a small selection rather than the
full list.

### `EvidenceItemView` (nested)

| Field | Type | Notes |
|---|---|---|
| `title` | `str` | from `Evidence.title` |
| `excerpt` | `str` | from `Evidence.excerpt` |
| `classification` | `str` | human label derived from `Evidence.evidence_type` (FR-005): `FACT` → "Reported fact", `CALCULATION` → "Calculation", `ASSUMPTION` → "Forecast assumption", `INTERPRETATION`/`OPINION` → "AI analysis" |
| `source` | `str` | from `Evidence.source` |
| `reference` | `str \| None` | from `Evidence.reference` |

**Validation rule**: `AmazonPresentation` is only ever constructed by
`scripts/capture_amazon_snapshot.py` from a real `WorkflowResult` — the public app never
constructs one from arbitrary input, so no additional runtime validation beyond normal
Pydantic field typing is needed (FR-003: no fabricated figures, enforced by construction
path, not by a schema rule).

## `EarlyAccessRegistration` (`aic/public/registration.py`)

| Field | Type | Notes |
|---|---|---|
| `registration_id` | `UUID` | generated server-side |
| `email` | `EmailStr` | required (FR-007); validated by Pydantic's email format check |
| `name` | `str \| None` | optional |
| `role` | `str \| None` | optional; one of a fixed set of target-audience values or free text |
| `experience` | `str \| None` | optional investment-experience level |
| `interests` | `str \| None` | optional companies/sectors of interest |
| `feedback` | `str \| None` | optional free-text feedback captured at registration time (distinct from the dedicated `FeedbackSubmission` flow, US4) |
| `qualified` | `bool` | derived at creation time via `classify_qualified(role)` (research.md Decision 4) |
| `created_at` | `datetime` | server-set |

**Validation rules**:
- `email` MUST be a syntactically valid email address (FR: rejects malformed email, spec
  US3/AC3); invalid submissions are rejected before a row is written.
- A second registration with the same `email` (case-insensitively normalized) MUST NOT
  create a second row counted toward completed registrations (FR-017) — implemented as a
  `UNIQUE` constraint on a normalized email column; a duplicate submission upserts/returns
  the existing record rather than erroring loudly at the user, and is not double-counted.

## `FeedbackSubmission` (`aic/public/feedback.py`)

| Field | Type | Notes |
|---|---|---|
| `feedback_id` | `UUID` | generated server-side |
| `intended_use` | `str \| None` | Q1: "What would you use AIC for?" |
| `most_valuable_part` | `str \| None` | Q2 |
| `trust_blockers` | `str \| None` | Q3 |
| `regular_use` | `str \| None` | Q4: "Would you use this regularly?" |
| `willing_to_pay` | `str \| None` | Q5 |
| `pre_conditions` | `str \| None` | Q6 |
| `email` | `EmailStr \| None` | optional link to a registration (US4/AC2) |
| `created_at` | `datetime` | server-set |

**Validation rule**: at least one of the six answer fields MUST be non-empty for a
submission to be accepted (an entirely blank feedback form carries no signal) — all six are
individually optional, but not all six blank simultaneously.

## `ValidationEvent` (`aic/public/events.py`)

| Field | Type | Notes |
|---|---|---|
| `event_id` | `UUID` | generated server-side |
| `event_type` | `Literal["landing_visit", "hero_cta_click", "demo_view", "demo_interaction", "signup_started", "signup_completed", "early_access_requested"]` | fixed set, per `aic-brand-landing` skill naming (research.md Decision 5) |
| `created_at` | `datetime` | server-set |

No visitor-identifying detail beyond event type + timestamp (spec Key Entities: "no more
visitor-identifying detail than the event type itself requires").

## `FunnelMetrics` (`aic/public/events.py`, computed, not persisted)

| Field | Type | Notes |
|---|---|---|
| `window_start` / `window_end` | `datetime` | the requested reporting window |
| `landing_visits` | `int` | count of `landing_visit` events in window |
| `cta_clicks` | `int` | count of `hero_cta_click` events in window |
| `completed_registrations` | `int` | count of `registrations` rows created in window |
| `qualified_registrations` | `int` | count of `registrations` rows with `qualified=True` created in window |
| `feedback_submissions` | `int` | count of `feedback_submissions` rows created in window |
| `cta_conversion_rate` | `float` | `cta_clicks / landing_visits` (0 if `landing_visits == 0`) |
| `registration_conversion_rate` | `float` | `completed_registrations / landing_visits` (0 if `landing_visits == 0`) |
| `qualified_interest_rate` | `float` | `qualified_registrations / completed_registrations` (0 if `completed_registrations == 0`) |

Directly implements FR-011/SC-004's three named formulas — computed on read from the three
SQLite tables, never stored redundantly.

## Storage schema (`aic/public/storage.py`, SQLite)

```sql
CREATE TABLE registrations (
    registration_id TEXT PRIMARY KEY,
    email TEXT NOT NULL,
    email_normalized TEXT NOT NULL UNIQUE,
    name TEXT,
    role TEXT,
    experience TEXT,
    interests TEXT,
    feedback TEXT,
    qualified INTEGER NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE feedback_submissions (
    feedback_id TEXT PRIMARY KEY,
    intended_use TEXT,
    most_valuable_part TEXT,
    trust_blockers TEXT,
    regular_use TEXT,
    willing_to_pay TEXT,
    pre_conditions TEXT,
    email TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE validation_events (
    event_id TEXT PRIMARY KEY,
    event_type TEXT NOT NULL,
    created_at TEXT NOT NULL
);
```

## Relationships

- `AmazonPresentation` has no relationship to the storage schema — it is read-only, static
  content, loaded independently of the three tables above.
- `FeedbackSubmission.email`, if present, is a soft, non-enforced link to a
  `registrations.email` row — no foreign key, since feedback MUST succeed whether or not a
  matching registration exists (spec Edge Cases).
- `ValidationEvent` has no relationship to any other table — pure counters.
