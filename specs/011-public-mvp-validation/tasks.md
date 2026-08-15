---

description: "Task list template for feature implementation"
---

# Tasks: Public MVP Validation

**Input**: Design documents from `/specs/011-public-mvp-validation/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/public-interface.md, quickstart.md

**Tests**: Included as normal implementation deliverables per story (not write-first TDD),
matching the convention used in 006/007/009/010 — this feature's own FR-016/SC-007 also
require the entire pre-existing suite to stay green, which is verified in Polish.

**Organization**: Tasks are grouped by user story (spec.md) to enable independent
implementation and testing of each story. This is the first feature in this project with a
new top-level dependency addition (`fastapi`, `uvicorn`, `jinja2`, `python-multipart`) and
the first with an external HTTP surface — both explicitly authorized by this feature's own
spec/plan as a justified Constitution VIII deviation (see plan.md Complexity Tracking).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1-US6)
- Include exact file paths in descriptions

## Path Conventions

Single project, `src`-layout: new package `src/aic/public/`, new script
`scripts/capture_amazon_snapshot.py`, new data file `data/amazon_snapshot.json`, new test
directory `tests/unit/public/` (all basenames `public_`/`test_public_`-prefixed from the
start, per the 006/007/009/010 lesson on cross-directory test-module collisions). Depends
on `scripts/mvp_amazon_dataset.py` (010) and `aic.workflow.run_investment_workflow` (009)
only at snapshot-capture time — never at request-serving time (research.md Decision 2).

## Phase 1: Setup

**Purpose**: Add the new dependencies and establish the `aic.public` package shell.

- [X] T001 Add `fastapi`, `uvicorn`, `jinja2`, `python-multipart` to `pyproject.toml`'s `dependencies`, then run `uv sync` (research.md Decision 1)
- [X] T002 Create `src/aic/public/__init__.py` as an initially empty module, establishing the `aic.public` package (contents populated incrementally by later tasks)

**Checkpoint**: Dependencies installed; package shell exists.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The shared read model, storage layer, snapshot data, and app scaffold every
user story depends on.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T003 [P] Create `src/aic/public/storage.py`: a `Storage` protocol plus a `SqliteStorage` implementation covering the three tables from data-model.md (`registrations` with `email_normalized UNIQUE`, `feedback_submissions`, `validation_events`), constructible against a file path or `":memory:"` for tests (research.md Decision 3; data-model.md "Storage schema")
- [X] T004 [P] Create `src/aic/public/presentation.py`: `EvidenceItemView` and `AmazonPresentation` Pydantic models, plus `build_presentation(result: WorkflowResult) -> AmazonPresentation` mapping every field per data-model.md's `AmazonPresentation` table, including the FACT/CALCULATION/ASSUMPTION/INTERPRETATION/OPINION → human-label mapping for `EvidenceItemView.classification` (data-model.md; FR-004, FR-005)
- [X] T005 [P] Create `src/aic/public/registration.py`: `EarlyAccessRegistration` Pydantic model (`email: EmailStr` required, rest optional) and `classify_qualified(role: str | None) -> bool` per research.md Decision 4
- [X] T006 [P] Create `src/aic/public/feedback.py`: `FeedbackSubmission` Pydantic model (six optional answer fields + optional `email`) per data-model.md
- [X] T007 [P] Create `src/aic/public/events.py`: `ValidationEvent` (`event_type: Literal[...]` per the seven-value set) and `FunnelMetrics` Pydantic models, plus `compute_funnel_metrics(storage, since=None, until=None) -> FunnelMetrics` implementing FR-011's three rate formulas with zero-denominator guards (data-model.md "FunnelMetrics")
- [X] T008 Create `scripts/capture_amazon_snapshot.py`: builds a `WorkflowInput` via `scripts/mvp_amazon_dataset.build_workflow_input()`, runs `run_investment_workflow` with a real `OpenAIProvider` (mirrors `mvp_amazon_acceptance.py`'s settings/provider setup), converts the result via `presentation.build_presentation`, and writes `data/amazon_snapshot.json` (`model_dump_json`) (depends on T004; research.md Decision 2)
- [X] T009 Run `uv run python scripts/capture_amazon_snapshot.py` to generate `data/amazon_snapshot.json` and commit the resulting file — makes a real OpenAI API call; requires `AIC_OPENAI_API_KEY` configured (depends on T008)
- [X] T010 Create `src/aic/public/app.py`: a `create_app(*, storage: Storage | None = None, presentation: AmazonPresentation | None = None) -> FastAPI` factory that, absent overrides, loads `data/amazon_snapshot.json` and opens the default SQLite file at startup — accepting overrides so tests never touch the real snapshot file or a real database (depends on T003, T004); module-level `app = create_app()` for `uvicorn aic.public.app:app`
- [X] T011 Add `AmazonPresentation`, `EarlyAccessRegistration`, `FeedbackSubmission`, `ValidationEvent`, `FunnelMetrics`, `Storage`, `SqliteStorage`, `create_app` exports to `src/aic/public/__init__.py` (depends on T002-T007, T010; same file as T002)

**Checkpoint**: Foundation ready — user story implementation can now begin.

---

## Phase 3: User Story 1 - Understand the Value Proposition Within Seconds (Priority: P1) 🎯 MVP

**Goal**: `GET /` renders AIC's brand identity, value proposition, and a plain-language
workflow explanation, and records one `landing_visit` event per request.

**Independent Test**: Request `GET /` and confirm the response contains the brand name,
value proposition, and workflow summary without technical jargon, and that exactly one
`landing_visit` event is recorded per request.

### Implementation for User Story 1

- [X] T012 [US1] Create `src/aic/public/templates/base.html` (shared layout/head) and `src/aic/public/templates/landing.html`'s hero + workflow-explanation sections (brand name "AI Investment Committee", concise value proposition, Data → Research → Thesis → Bull → Bear → DCF → Committee → Memo explanation), avoiding "revolutionizing," autonomous-trading-bot, or guaranteed-return language throughout (FR-001, FR-002; `aic-brand-landing` skill "Hero")
- [X] T013 [US1] Wire `GET /` in `src/aic/public/app.py` to render `landing.html` with the loaded `AmazonPresentation` and record one `landing_visit` `ValidationEvent` synchronously before responding (depends on T010, T012; contracts/public-interface.md "GET /")
- [X] T014 [US1] Create `tests/unit/public/public_fakes.py` (in-memory `Storage` fixture helper) and `tests/unit/public/test_public_app.py` with `test_get_landing_page_returns_value_proposition` and `test_get_landing_page_records_one_landing_visit_event` (depends on T013)

**Checkpoint**: User Story 1 is independently functional — the hero/value-proposition
content renders and visits are counted.

---

## Phase 4: User Story 2 - Inspect a Real, Trustworthy Investment Example (Priority: P1)

**Goal**: The landing page's example section renders the Amazon `AmazonPresentation` in
human-readable form, with every figure labeled fact/calculation/assumption/AI analysis.

**Independent Test**: Request `GET /` and confirm the response contains company identity,
implied value/share, recommendation, conviction, thesis/bull/bear summaries, key
assumptions/risks, and a labeled evidence list — with zero raw Python/Pydantic
representations.

### Implementation for User Story 2

- [X] T015 [US2] Extend `src/aic/public/templates/landing.html` with the Amazon example section: company identity, implied value/share, recommendation, conviction, thesis/bull/bear summaries, key assumptions, key risks, and an evidence list rendering each `EvidenceItemView`'s title/excerpt/classification/source (depends on T012, same file; FR-004, FR-005)
- [X] T016 [US2] In `tests/unit/public/test_public_presentation.py`, add `test_build_presentation_maps_workflow_result_fields` and `test_build_presentation_classifies_evidence_types` using a fixture `WorkflowResult` (construct via existing `tests/unit/workflow/workflow_fakes.py`-style fakes or a hand-built result), asserting every `AmazonPresentation` field and the FACT→"Reported fact"/CALCULATION→"Calculation"/ASSUMPTION→"Forecast assumption"/INTERPRETATION,OPINION→"AI analysis" mapping (depends on T004)
- [X] T017 [US2] In `tests/unit/public/test_public_app.py`, add `test_get_landing_page_shows_amazon_example_in_human_readable_form` asserting the response HTML contains the snapshot's implied-value-per-share string and recommendation, and does not contain a raw `repr(...)`/`model_dump()`-style fragment (depends on T015)

**Checkpoint**: User Stories 1 AND 2 both work independently — visitors see the value
proposition and a trustworthy, legible real example.

---

## Phase 5: User Story 3 - Express Interest With Minimal-Friction Registration (Priority: P1)

**Goal**: The primary CTA leads to a form requiring only email; submission succeeds,
duplicates are not double-counted, no account/session is created.

**Independent Test**: `POST /register` with only an email set succeeds and is recorded; an
invalid email is rejected; resubmitting the same email does not create a second row.

### Implementation for User Story 3

- [X] T018 [US3] Create `src/aic/public/templates/register.html` (email required; name, role, experience, interests, feedback optional; primary CTA link on `landing.html` points here) and `src/aic/public/templates/register_confirmation.html` (states this is early access/validation, not a live product) (FR-006, FR-007; spec US3/AC2)
- [X] T019 [US3] Wire `GET /register` and `POST /register` in `app.py`: validate via `EarlyAccessRegistration`, classify `qualified` via `classify_qualified`, persist via `storage.create_registration` (idempotent on `email_normalized`), record `signup_completed` and `early_access_requested` events on success, redirect `303` to the confirmation page; on invalid email, re-render the form with `422` and an error message (depends on T005, T010, T018; contracts/public-interface.md "POST /register")
- [X] T020 [US3] In `tests/unit/public/test_public_registration.py`, add tests for: email-only submission valid; malformed email rejected; `classify_qualified` returns `True` for each target-audience role value and `False` for blank/out-of-audience values (depends on T005)
- [X] T021 [US3] In `tests/unit/public/test_public_storage.py`, add `test_duplicate_email_registration_does_not_create_second_row` exercising the `email_normalized UNIQUE` constraint (depends on T003)
- [X] T022 [P] [US3] In `tests/unit/public/test_public_app.py`, add `test_post_register_with_only_email_redirects_to_confirmation`, `test_post_register_with_malformed_email_returns_422`, and `test_post_register_duplicate_email_is_not_double_counted` (depends on T019)

**Checkpoint**: User Stories 1-3 all work independently — the core P1 funnel (understand →
trust → register) is complete. This is the feature's MVP slice.

---

## Phase 6: User Story 4 - Provide Qualitative Feedback (Priority: P2)

**Goal**: The six-question feedback form works whether or not the visitor registered.

**Independent Test**: `POST /feedback` with at least one answer succeeds and is recorded,
with no prior registration required; an all-blank submission is rejected.

### Implementation for User Story 4

- [X] T023 [US4] Create `src/aic/public/templates/feedback.html` (the exact six questions from spec US4/AC1) and `src/aic/public/templates/feedback_confirmation.html` (FR-009)
- [X] T024 [US4] Wire `GET /feedback` and `POST /feedback` in `app.py`: reject an all-six-blank submission with `422`, otherwise persist via `storage.create_feedback` and redirect to the confirmation page — no registration lookup or requirement (depends on T006, T010, T023; contracts/public-interface.md "POST /feedback"; FR-018)
- [X] T025 [US4] In `tests/unit/public/test_public_feedback.py`, add tests for: all-blank rejected; single non-blank answer accepted; submission succeeds with no associated `email` (depends on T006)
- [X] T026 [P] [US4] In `tests/unit/public/test_public_app.py`, add `test_post_feedback_succeeds_without_prior_registration` and `test_post_feedback_all_blank_returns_422` (depends on T024)

**Checkpoint**: User Stories 1-4 all work independently.

---

## Phase 7: User Story 5 - Measure the Validation Funnel (Priority: P2)

**Goal**: `POST /events` records interaction events; `GET /metrics` reports counts and the
three defined conversion rates for a given time window.

**Independent Test**: Record a small set of events/registrations, then confirm `GET
/metrics` returns matching counts and correctly computed CTA/registration/qualified-interest
rates.

### Implementation for User Story 5

- [X] T027 [US5] Wire `POST /events` in `app.py`: record the given `event_type` as a `ValidationEvent` and always respond `202 Accepted`, even for a malformed/unknown `event_type` (best-effort; depends on T007, T010; contracts/public-interface.md "POST /events")
- [X] T028 [US5] Wire `GET /metrics` in `app.py`: parse optional `since`/`until` query params, call `compute_funnel_metrics`, and return the `FunnelMetrics` as JSON (depends on T007, T010; contracts/public-interface.md "GET /metrics")
- [X] T029 [US5] In `tests/unit/public/test_public_events.py`, add tests for: each event type records correctly; `compute_funnel_metrics` computes all three rates correctly against a constructed set of events/registrations, including the 0-visits and 0-registrations zero-denominator cases (depends on T007)
- [X] T030 [P] [US5] In `tests/unit/public/test_public_app.py`, add `test_post_events_always_returns_202_even_for_unknown_type` and `test_get_metrics_reflects_recorded_activity` (depends on T027, T028)

**Checkpoint**: User Stories 1-5 all work independently — the full quantitative funnel is
measurable end to end.

---

## Phase 8: User Story 6 - See Explicit Trust and Disclaimer Messaging (Priority: P3)

**Goal**: Disclaimer language is visible near the Amazon example and near the
CTA/registration; no guaranteed-return or financial-advice language appears anywhere.

**Independent Test**: Review `GET /` and `GET /register` and confirm disclaimer text is
present adjacent to both the example and the registration form.

### Implementation for User Story 6

- [X] T031 [US6] Create a shared `src/aic/public/templates/_disclaimer.html` partial (valuation is model-dependent; assumptions affect results; AI-generated analysis can be wrong; outputs are research assistance, not financial advice; verify source information independently) and include it in `landing.html` (adjacent to the Amazon example) and `register.html` (adjacent to the CTA/registration form) (depends on T012, T015, T018; FR-012)
- [X] T032 [P] [US6] In `tests/unit/public/test_public_app.py`, add `test_landing_page_shows_disclaimer_near_example`, `test_register_page_shows_disclaimer_near_cta`, and `test_no_guaranteed_return_language_anywhere` (asserting phrases like "guaranteed," "get rich," "revolutionizing" do not appear in `/`, `/register`, or `/feedback` responses) (depends on T031)

**Checkpoint**: All six user stories are independently functional.

---

## Phase 9: Polish & Cross-Cutting Concerns

- [X] T033 Run `pytest`, `ruff check .`, and `mypy src` across the full repository; confirm every pre-existing test (221, per feature 010) still passes unmodified and only new `tests/unit/public/` tests were added (FR-016; SC-007)
- [X] T034 Walk through `quickstart.md`'s manual browser section end to end (`uv run uvicorn aic.public.app:app --reload`) and confirm every listed expected outcome holds, including the duplicate-registration and `/metrics` consistency checks

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — BLOCKS Foundational (T003+ need `fastapi`/`jinja2` importable)
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories (in particular, every route-wiring task depends on T010's `create_app`)
- **User Stories (Phase 3-8)**: All depend on Phase 2 completing
  - US1/US2 share `landing.html` and must stay sequential against each other (T012 → T015)
  - US3, US4, US5, US6 each touch their own template file(s) and are otherwise independent
    of one another, though US6's disclaimer partial (T031) depends on US1/US2/US3's
    templates already existing (T012, T015, T018)
  - `app.py` (T010) is shared by every story's route-wiring task (T013, T019, T024, T027,
    T028) — these must be applied sequentially against each other even though they belong
    to different stories
- **Polish (Phase 9)**: Depends on all six user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Depends only on Phase 2
- **User Story 2 (P1)**: Depends on Phase 2 and on US1's `landing.html`/`T012` existing (same file)
- **User Story 3 (P1)**: Depends only on Phase 2 — independent of US1/US2's files
- **User Story 4 (P2)**: Depends only on Phase 2 — independent of every other story's files
- **User Story 5 (P2)**: Depends only on Phase 2 — independent of every other story's files
- **User Story 6 (P3)**: Depends on Phase 2 and on US1/US2/US3's templates already existing (T012, T015, T018)

### Within Each User Story

- T012 → T015 (US1 → US2, same file: `landing.html`)
- T013, T019, T024, T027, T028 are all edits to `app.py` and must be applied in some
  sequential order relative to each other, regardless of their `[P]`/story grouping
- Each story's own test-file additions depend on that story's own implementation tasks
  completing first

### Parallel Opportunities

- T003-T007 (Phase 2 models/storage) can all run in parallel — five independent new files
- T020/T021 (US3), T025 (US4), T029 (US5) can run in parallel with each other — different
  test files, no shared state
- T022, T026, T030, T032 (each story's `test_public_app.py` additions) are all edits to one
  shared test file and must be applied sequentially against each other, even though each
  is tagged `[P]` relative to its *own* story's other tasks

---

## Parallel Example: Phase 2

```bash
# After Phase 1 completes, in parallel:
Task: "Create src/aic/public/storage.py (Storage protocol + SqliteStorage)"
Task: "Create src/aic/public/presentation.py (AmazonPresentation + build_presentation)"
Task: "Create src/aic/public/registration.py (EarlyAccessRegistration + classify_qualified)"
Task: "Create src/aic/public/feedback.py (FeedbackSubmission)"
Task: "Create src/aic/public/events.py (ValidationEvent + FunnelMetrics + compute_funnel_metrics)"
```

---

## Implementation Strategy

### MVP First (User Stories 1-3 Only)

1. Complete Phase 1: Setup (T001-T002)
2. Complete Phase 2: Foundational (T003-T011) — including the real snapshot capture (T009)
3. Complete Phase 3-5: User Stories 1, 2, 3 (T012-T022)
4. **STOP and VALIDATE**: `pytest tests/unit/public/ -v`, then the quickstart's manual
   browser walkthrough steps 1-5 — a visitor can understand the proposition, trust the
   Amazon example, and register
5. This alone answers the feature's core question ("do users want to try it, register");
   US4/US5/US6 add qualitative depth, measurement, and trust polish

### Incremental Delivery

1. Setup + Foundational → snapshot captured, app scaffold ready
2. US1 → Test independently → hero/value prop renders
3. US2 → Test independently → Amazon example renders, trustworthy and legible
4. US3 → Test independently → registration works end to end (MVP complete)
5. US4 → Test independently → qualitative feedback flows in
6. US5 → Test independently → funnel is measurable
7. US6 → Test independently → disclaimers present everywhere required
8. Phase 9 → full-repo regression pass, quickstart walkthrough

---

## Notes

- [P] tasks = different files, no dependencies (except where explicitly noted as a shared
  file needing sequential application despite the `[P]` tag on other tasks in the same
  story)
- [Story] label maps task to specific user story for traceability
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- T009 (snapshot capture) and T034 (manual quickstart walkthrough) are the only tasks in
  this feature that touch the network — every other task, including all automated tests,
  is network-free
