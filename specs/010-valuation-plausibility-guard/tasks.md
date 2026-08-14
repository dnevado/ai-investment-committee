---

description: "Task list template for feature implementation"
---

# Tasks: Valuation Plausibility Guard

**Input**: Design documents from `/specs/010-valuation-plausibility-guard/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/dcf-plausibility-guard.md, quickstart.md

**Tests**: Not explicitly requested as TDD, but the spec (FR-008) requires this guard to be
protected by no-network automated tests covering both the acceptance path and the rejection
path, on top of the constitution's blanket unit-test requirement for DCF logic — these are
included as normal implementation deliverables per story, matching the convention already
used in 006/007/009.

**Organization**: Tasks are grouped by user story (spec.md) to enable independent
implementation and testing of each story. This feature is explicitly authorized by its own
spec/plan to modify two existing files outside its own package —
`tests/unit/dcf/test_engine.py` (narrowing one pre-existing test per the resolved
003/010 conflict) and `specs/003-dcf-valuation-engine/spec.md` (amending its Edge Cases
note) — plus `scripts/mvp_amazon_validation.py` (correcting its capex assumption).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

Single project, `src`-layout (per plan.md). All production code changes are confined to one
existing file, `src/aic/dcf/engine.py` (003) — no new package, module, or dependency is
introduced. Test changes live in `tests/unit/dcf/` (existing directory, already a
network-free unit-test area). No `__init__.py` export changes are needed since
`compute_dcf`'s signature is unchanged (contracts/dcf-plausibility-guard.md).

## Phase 1: Setup

Not applicable — this feature adds behavior to one existing function in an existing
package (`aic.dcf`); no new package shell, dependency, or project scaffolding is required.
Proceeds directly to Phase 2.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The guard itself — every user story's tests exercise this single change.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T001 In `src/aic/dcf/engine.py`'s `compute_dcf`, after computing `fcff_final` and `enterprise_value` (unrounded `Decimal`s) and before constructing `DCFResult`, add two checks in order: (1) raise `ValueError` if `fcff_final <= 0`, with a message stating the terminal-year FCFF check failed and including the computed value; (2) raise `ValueError` if `enterprise_value <= 0`, with a message stating the enterprise-value check failed and including the computed value (contracts/dcf-plausibility-guard.md; FR-001, FR-002, FR-003, FR-009; research.md Decision 2)
- [X] T002 [P] Amend `specs/003-dcf-valuation-engine/spec.md`'s Edge Cases bullet on negative forecast-year FCFF to note that, as of feature 010, this no longer applies to the *terminal* forecast year (interim-year negative FCFF remains allowed and unchanged), with a pointer to `specs/010-valuation-plausibility-guard/spec.md` (research.md Decision 1)

**Checkpoint**: Foundation ready — user story implementation can now begin.

---

## Phase 3: User Story 1 - Reject an Economically Implausible Valuation (Priority: P1) 🎯 MVP

**Goal**: `compute_dcf` never returns a `DCFResult` whose terminal-year FCFF or enterprise
value is non-positive, and the failure halts the pipeline before any research, bull/bear, or
committee stage runs.

**Independent Test**: Compute a DCF with assumptions known to drive terminal-year FCFF (or
enterprise value) to zero or below and confirm an explicit `ValueError` is raised instead of
a `DCFResult`; confirm `run_investment_workflow` propagates the same failure before any
provider call.

### Implementation for User Story 1

- [X] T003 [US1] In `tests/unit/dcf/test_engine.py`, rewrite `test_negative_fcff_year_is_allowed` to use a multi-year forecast where an *interim* (non-terminal) year has negative FCFF and the terminal year has positive FCFF, confirming interim-year negative FCFF is still allowed while satisfying the new guard (depends on T001; research.md Decision 1)
- [X] T004 [US1] In `tests/unit/dcf/test_engine.py`, add `test_rejects_non_positive_terminal_year_fcff` asserting `compute_dcf` raises `ValueError` (message references the terminal-year FCFF check and its computed value) for a single-year forecast whose FCFF is negative, and for one whose FCFF is exactly zero (spec Edge Cases: "terminal-year FCFF is exactly zero... MUST be rejected") (depends on T003, same file; FR-001)
- [X] T005 [US1] In `tests/unit/dcf/test_engine.py`, add `test_rejects_non_positive_enterprise_value` asserting `compute_dcf` raises `ValueError` (message references the enterprise-value check and its computed value) for assumptions producing a positive terminal-year FCFF but a non-positive enterprise value (depends on T004, same file; FR-002)
- [X] T006 [P] [US1] In `tests/unit/workflow/test_workflow_orchestrator.py`, add a test asserting `run_investment_workflow` propagates the `ValueError` raised by `compute_dcf` for an implausible assumption set, with zero calls recorded on `FakeLLMProvider.calls` (mirrors the existing `test_invalid_dcf_assumptions_fail_before_any_llm_call` pattern) (depends on T001; FR-004, FR-009; contracts/dcf-plausibility-guard.md "Caller impact")

**Checkpoint**: User Story 1 is fully functional and independently testable — the guard
rejects implausible valuations and the workflow halts before any LLM call.

---

## Phase 4: User Story 2 - Validate the Full Pipeline Against Amazon's Real Data (Priority: P2)

**Goal**: A reference dataset built from Amazon's real FY2025 financials and an internally
consistent forecast produces a strictly positive, guard-passing DCF result, exercisable both
as a no-network automated fixture and as the existing manual end-to-end validation script.

**Independent Test**: Run `compute_dcf` against the corrected Amazon reference assumptions
and confirm it returns a `DCFResult` with strictly positive enterprise value, equity value,
and implied value per share, with every material figure traceable to evidence.

### Implementation for User Story 2

- [X] T007 [US2] In `scripts/mvp_amazon_validation.py`, replace the flat ~18.4%-of-revenue `capital_expenditure` forecast values with the faded 15% / 12% / 10%-of-revenue figures ($119,368,000,000 / $105,044,000,000 / $95,415,000,000 for Y1/Y2/Y3), and update the surrounding assumption comment and `ev_capex_actual` evidence excerpt to explain the fade rationale (research.md Decision 3 & 4; FR-005, FR-007)
- [X] T008 [P] [US2] Create `tests/unit/dcf/test_amazon_reference_case.py` with a no-network `DCFAssumptions` fixture using the same Amazon figures (revenue, D&A, corrected capex, ΔNWC, 12% operating margin, 19.7% tax rate, 9% WACC, 3% terminal growth) as `scripts/mvp_amazon_validation.py`, asserting `compute_dcf` succeeds and returns strictly positive `enterprise_value`, `equity_value`, and `implied_value_per_share` (data-model.md "Reference Dataset (Amazon)"; FR-005, FR-007, FR-008; SC-002)
- [X] T009 [US2] Manually run `uv run python scripts/mvp_amazon_validation.py` per quickstart.md's "Manual end-to-end validation" section and confirm the printed Enterprise Value, Equity Value, and Value / Share are all strictly positive before the script proceeds to the real OpenAI call (depends on T007; verification task, no code change; SC-002)

**Checkpoint**: User Stories 1 AND 2 both work independently — the guard rejects bad
valuations, and a real, evidence-backed, positive valuation flows through cleanly.

---

## Phase 5: User Story 3 - Understand Why a Valuation Was Rejected (Priority: P3)

**Goal**: A rejected computation's error message alone is enough to identify which check
failed and the offending figure, without reading the DCF engine's source.

**Independent Test**: Trigger each rejection condition and confirm the message names the
specific failing check (terminal-year FCFF or enterprise value) together with its computed
value in the same message.

### Implementation for User Story 3

- [X] T010 [US3] In `tests/unit/dcf/test_engine.py`, add `test_terminal_fcff_rejection_message_reports_offending_value` and `test_enterprise_value_rejection_message_reports_offending_value`, each asserting the raised `ValueError`'s message contains both a check-identifying phrase ("terminal"/"enterprise value") and the exact offending computed figure as a substring, so the failure is diagnosable from the message text alone (depends on T005, same file; FR-003; SC-003)

**Checkpoint**: All three user stories are independently functional — reject, validate, and
diagnose.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [X] T011 Run `pytest`, `ruff check .`, and `mypy src` across the full repository and fix any fallout from the Phase 3 test rewrite (constitution "Required test commands"; SC-004)
- [X] T012 Walk through `quickstart.md` end to end (automated section fully; manual section per T009) and confirm every listed expected outcome holds

---

## Dependencies & Execution Order

### Phase Dependencies

- **Foundational (Phase 2)**: No dependencies — BLOCKS all user stories (T001 in particular; T002 is independent documentation work)
- **User Stories (Phase 3-5)**: All depend on Phase 2 (specifically T001) completing first
  - US1, US2, and US3 can proceed in parallel by file (US1/US3 share `test_engine.py` and must stay sequential against each other; US2's files are independent)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Phase 6)**: Depends on all three user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Depends only on Phase 2 (T001)
- **User Story 2 (P2)**: Depends only on Phase 2 (T001) — independent of US1's file changes
- **User Story 3 (P3)**: Depends on Phase 2 (T001) and, because it shares `test_engine.py`, on US1's T005 completing first (T010 continues the same file)

### Within Each User Story

- T003 → T004 → T005 → T010 are strictly sequential (same file: `tests/unit/dcf/test_engine.py`)
- T006, T008, T009 are independent of that chain (different files)
- T007 must precede T009 (the script must be corrected before it is run)

### Parallel Opportunities

- T001 and T002 (Phase 2) can run in parallel — different files
- T006 (US1) can run in parallel with T003-T005 (US1) and with all of US2 — different files
- T007 and T008 (US2) can run in parallel with each other and with T003-T006 — different files

---

## Parallel Example: Phase 2 + early User Story work

```bash
# Phase 2, in parallel:
Task: "Add the two plausibility checks to compute_dcf in src/aic/dcf/engine.py"
Task: "Amend specs/003-dcf-valuation-engine/spec.md's Edge Cases note"

# After T001 completes, in parallel:
Task: "Rewrite test_negative_fcff_year_is_allowed in tests/unit/dcf/test_engine.py"          # starts the US1 chain
Task: "Add workflow-level propagation test in tests/unit/workflow/test_workflow_orchestrator.py"  # US1, different file
Task: "Correct capex assumptions in scripts/mvp_amazon_validation.py"                        # US2
Task: "Create tests/unit/dcf/test_amazon_reference_case.py"                                   # US2
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 2: Foundational (T001, T002)
2. Complete Phase 3: User Story 1 (T003-T006)
3. **STOP and VALIDATE**: `pytest tests/unit/dcf/ tests/unit/workflow/ -v` — the guard
   rejects implausible valuations and the workflow halts before any LLM call
4. This alone closes the original defect (a negative-EV report silently reaching the
   analyst); US2/US3 add the real-data proof case and message-quality polish

### Incremental Delivery

1. Phase 2 → Foundation ready (guard exists)
2. US1 → Test independently → the core defect is closed
3. US2 → Test independently → Amazon reference case proves the guard passes on real,
   internally-consistent data
4. US3 → Test independently → rejection messages are confirmed diagnosable
5. Phase 6 → full-repo regression pass, quickstart walkthrough

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- T003-T005 and T010 share one file and must be applied in order, even though only some
  carry the [P] designation's absence as a hint — no other task in this feature conflicts
  on a shared file besides that chain
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
