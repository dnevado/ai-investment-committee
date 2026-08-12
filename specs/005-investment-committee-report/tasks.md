---

description: "Task list template for feature implementation"
---

# Tasks: Investment Committee Report

**Input**: Design documents from `/specs/005-investment-committee-report/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/report-interface.md, quickstart.md

**Tests**: Not explicitly requested as TDD, but the spec requires explicit rejection of
incomplete reports and explicit indication of absent dissent — these are included as normal
implementation deliverables per story, not write-first TDD tasks.

**Organization**: Tasks are grouped by user story (spec.md) to enable independent
implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

Single project, `src`-layout (per plan.md): `src/aic/report/`, `tests/unit/report/`.
Depends on the existing `src/aic/domain/` (002) and `src/aic/dcf/` (003) packages,
unmodified by this feature. No existing file is touched and no new dependency is added.

## Phase 1: Setup

**Purpose**: Establish the `aic.report` package shell.

- [X] T001 Create `src/aic/report/__init__.py` as an initially empty module, establishing the `aic.report` package (contents populated incrementally by later tasks)

**Checkpoint**: Package shell exists. All later `src/aic/report/__init__.py` edits (T003, T006) are sequential against each other from here on, since they share one file.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared prerequisites needed by more than one user story, beyond the package shell.

Unlike prior features in this project, this feature has no shared type that isn't itself a
user story's own deliverable — `CommitteeReport` is User Story 1's primary deliverable (see
Phase 3), not standalone shared infrastructure, and this feature adds no new dependency and
no provider abstraction. **No tasks are appended to this phase.**

---

## Phase 3: User Story 1 - Assemble a Complete, Structured Investment Committee Report (Priority: P1) 🎯 MVP

**Goal**: Compose an already-produced company, financial snapshot(s), investment thesis
(with evidence), DCF valuation result, committee assessment, and committee decision into one
validated `CommitteeReport`, without altering, recomputing, or fabricating any of it.

**Independent Test**: Supply a complete set of already-validated inputs and confirm
`CommitteeReport` construction returns a structured report containing all of them unchanged;
confirm a missing required input raises an explicit validation error.

### Implementation for User Story 1

- [X] T002 [US1] Create `src/aic/report/report.py` with `CommitteeReport` (`company: Company`, `financial_snapshots: list[FinancialSnapshot]` with `min_length=1`, `thesis: InvestmentThesis`, `dcf_result: DCFResult`, `assessment: AnalysisAssessment`, `decision: CommitteeDecision`) — direct Pydantic construction is the "assembly" step, no separate service function (FR-001, FR-002, FR-004, FR-005, FR-006, FR-007, FR-013, FR-014; data-model.md CommitteeReport; research.md "direct, validated Pydantic bundle")
- [X] T003 [US1] Add `CommitteeReport` export to `src/aic/report/__init__.py` (depends on T001, T002; same file)
- [X] T004 [P] [US1] Create `tests/unit/report/test_report.py` covering: valid construction with every composed value (company, snapshots, thesis with its evidence, dcf_result, assessment, decision with recommendation and dissent) preserved unchanged; a `pydantic.ValidationError` for each missing required field; `financial_snapshots` rejects an empty list; a decision with recorded dissent and a decision with no dissent are both preserved unchanged on the report (depends on T002; FR-001, FR-002, FR-004, FR-005, FR-006, FR-007, FR-013, FR-014; spec US1 acceptance scenarios 1-4)

**Checkpoint**: User Story 1 is fully functional and independently testable — this alone is the MVP.

---

## Phase 4: User Story 2 - Render the Report Into a Human-Readable Document (Priority: P2)

**Goal**: Deterministically render a validated `CommitteeReport` into a Markdown document
suitable for human review and downstream AI Committee analysis.

**Independent Test**: Render the same `CommitteeReport` twice and confirm the two documents
are identical and contain exactly the report's structured content, including an explicit
indication when no dissent was recorded.

### Implementation for User Story 2

- [X] T005 [US2] Create `src/aic/report/document.py` with `render_report_document(report: CommitteeReport) -> str` — pure Markdown rendering of the company, financial snapshots, investment thesis (summary, supporting evidence, key assumptions, key risks, invalidation conditions), DCF valuation (enterprise value, equity value, implied value per share, per-year FCFF), committee assessment (conclusion, confidence, arguments, assumptions, risks), and committee decision (recommendation, rationale, dissent — printing an explicit "No dissent recorded." line when `decision.dissent` is empty), no I/O, no randomness (depends on T002; FR-002, FR-003, FR-004, FR-005, FR-006, FR-008, FR-009; data-model.md render_report_document; research.md "dissent rendering")
- [X] T006 [US2] Add `render_report_document` export to `src/aic/report/__init__.py` (depends on T003, T005; same file)
- [X] T007 [P] [US2] Create `tests/unit/report/test_report_document.py` (named to avoid a pytest module-name collision with `tests/unit/research/test_document.py`, since neither `tests/unit/report/` nor `tests/unit/research/` is a package) covering: the document contains exactly the report's thesis/evidence/valuation/assumptions/risks/invalidation-conditions/assessment/recommendation with no invented content; two renders of the same report are byte-identical; a report with recorded dissent lists each dissent entry; a report with no dissent renders "No dissent recorded."; empty evidence/assumptions/risks render without error (depends on T005; FR-006, FR-008, FR-009; spec US2 acceptance scenarios 1-2)

**Checkpoint**: User Stories 1 AND 2 both work independently.

---

## Phase 5: User Story 3 - Keep the Report Free of New Valuation Logic or Recommendations (Priority: P3)

**Goal**: Provide an explicit, tested guarantee that composing several already-trusted prior
features together introduces no new valuation shortcut and never overrides the committee's
actual recommendation.

**Independent Test**: Inspect a generated report and its rendered document and confirm every
valuation figure traces exactly to the DCF engine's own output, and confirm the feature
never computes, infers, or overrides the committee decision's recommendation.

### Implementation for User Story 3

- [X] T008 [P] [US3] Create `tests/unit/report/test_no_new_valuation_logic.py` asserting every valuation figure shown by `render_report_document` (enterprise value, equity value, implied value per share, per-year FCFF) matches the corresponding `report.dcf_result` value exactly for a constructed report, and asserting `report.decision.recommendation` on the assembled `CommitteeReport` is identical to the `Recommendation` passed into the original `CommitteeDecision` (depends on T002, T005; FR-003, FR-005, FR-010; SC-002, SC-006; spec US3 acceptance scenarios 1-2)

**Checkpoint**: All three user stories are independently functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Whole-feature validation against the spec's Success Criteria.

- [X] T009 [P] Run `uv run pytest tests/unit/report -v` and confirm every test passes — validates SC-001, SC-002, SC-003, SC-004, SC-005
- [X] T010 [P] Run `uv run ruff check .` and `uv run mypy src` and resolve any reported issues
- [X] T011 [P] Verify no new financial calculation exists anywhere in `src/aic/report/` — inspect every file for arithmetic on `Money`/`Decimal` values; every valuation figure must be a direct pass-through of `dcf_result` (FR-003, FR-010; SC-006)
- [X] T012 [P] Verify no persistence, API, UI, scheduling, or market-data integration exists anywhere in `src/aic/report/` — inspect every file (FR-011, FR-012; SC-007)
- [X] T013 Run the full `quickstart.md` validation sequence end-to-end and confirm every snippet behaves exactly as documented

---

## Phase 7: Convergence

- [X] T014 Add a test asserting `CommitteeReport` and `render_report_document` accept and present multiple `FinancialSnapshot`s with differing `as_of` fiscal periods and differing currencies as-is, with no reconciliation or error, in `tests/unit/report/test_report.py` per spec.md Edge Cases (missing)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: T001 only
- **Foundational (Phase 2)**: No tasks — proceed directly to Phase 3
- **User Stories (Phase 3-5)**: All depend on Phase 1 (package shell) completion
- **Polish (Phase 6)**: Depends on all three user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Depends only on Phase 1 — no dependency on US2/US3
- **User Story 2 (P2)**: Depends on `CommitteeReport` existing (T002, from US1) — `document.py` imports it as its input type, so US2's implementation cannot start before T002 lands, though US2's own test file (T007) is independent of US1's test file (T004)
- **User Story 3 (P3)**: Depends on both `CommitteeReport` (T002) and `render_report_document` (T005) existing, since it verifies fidelity across both the structured report and its rendering

### Important: shared-file constraints

- `src/aic/report/__init__.py`: T001 → T003 → T006 must be applied in that order (same file)

### Parallel Opportunities

- T004 (US1 test) can proceed in parallel with T005/T006 (US2 implementation) once T002 lands — different files
- T007 (US2 test) and T008 (US3 test) can run in parallel once T005 lands — independent files
- T009, T010, T011, T012 (Polish) can all run in parallel — independent verification passes

---

## Parallel Example: After User Story 1's CommitteeReport lands

```bash
# Once T002 (CommitteeReport) is done, these proceed in parallel — different files:
Task: "Write tests/unit/report/test_report.py (US1)"
Task: "Implement src/aic/report/document.py (US2)"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 3: User Story 1
3. **STOP and VALIDATE**: `uv run pytest tests/unit/report -v` passes for `CommitteeReport`
   construction and required-field validation
4. This alone delivers the feature's core value — a validated, composed report object with
   zero recalculation or fabrication

### Incremental Delivery

1. Setup → package shell ready
2. Add User Story 1 → validate independently → working `CommitteeReport` (MVP)
3. Add User Story 2 → validate independently → deterministic Markdown rendering
4. Add User Story 3 → validate independently → explicit valuation-fidelity and
   recommendation-integrity guarantee
5. Polish → full quickstart.md pass + scope verification

---

## Notes

- `[P]` tasks touch different files with no dependency between them
- `[Story]` label maps a task to its user story for traceability; Setup/Polish tasks carry
  no story label; Phase 2 (Foundational) has no tasks for this feature
- `src/aic/report/__init__.py` is a shared file edited incrementally — respect the
  sequential order noted above
- This feature adds no new third-party dependency and modifies no existing file — everything
  is new, additive code under `src/aic/report/`
- Commit after each task or logical group
- Stop at any checkpoint to validate a story independently
