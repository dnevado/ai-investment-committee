---

description: "Task list template for feature implementation"
---

# Tasks: End-to-End Investment Committee Workflow & MVP Completion

**Input**: Design documents from `/specs/009-e2e-investment-workflow/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/workflow-interface.md, quickstart.md

**Tests**: Not explicitly requested as TDD, but the spec requires zero real network calls in
this feature's own test suite, explicit halt-on-failure behavior at every stage, and zero
regression to any pre-existing test — these are included as normal implementation
deliverables per story, not write-first TDD tasks.

**Organization**: Tasks are grouped by user story (spec.md) to enable independent
implementation and testing of each story. Unlike every prior feature (004-008), this one is
explicitly authorized by its own spec to modify two existing files
(`src/aic/report/report.py`, `src/aic/report/document.py`) and to delete one existing,
unused directory (`src/aic/agents/`).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

Single project, `src`-layout (per plan.md): `src/aic/workflow/`, `tests/unit/workflow/`.
Depends on the existing `src/aic/domain/` (002), `src/aic/dcf/` (003),
`src/aic/research/` (004), `src/aic/committee/` (006), `src/aic/bullbear/` (007), and
`src/aic/report/` (005) packages — every one of them reused unchanged in its own public
contract, except the two additive fields this feature adds to `src/aic/report/report.py`.
No new dependency is added. Every test file in `tests/unit/workflow/` uses a
`workflow`-qualified basename from the start, per the lesson from 006/007 (neither
`tests/unit/workflow/` nor any existing test directory is a Python package, so basenames
must stay globally unique across all of them).

## Phase 1: Setup

**Purpose**: Establish the `aic.workflow` package shell and remove genuinely dead code.

- [X] T001 Delete the entire `src/aic/agents/` directory (five prompt scaffold files:
  `bear.md`, `bull.md`, `committee.md`, `research.md`, `valuation.md`), confirmed by
  repository-wide search to be imported nowhere in `src/` or `tests/` (FR-017; research.md
  "src/aic/agents/prompts/*.md is removed, not reconciled in place")
- [X] T002 Create `src/aic/workflow/__init__.py` as an initially empty module, establishing the `aic.workflow` package (contents populated incrementally by later tasks)

**Checkpoint**: Dead code removed; package shell exists. T001 is independent of everything
else in this feature. All later `src/aic/workflow/__init__.py` edits (T007, T009) are
sequential against each other from here on, since they share one file.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The shared types every user story depends on, including the additive
`CommitteeReport` extension every successful workflow run needs.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T003 [P] Create `src/aic/workflow/input.py` with `WorkflowInput` (`company: Company`, `financial_snapshots: list[FinancialSnapshot]` with `min_length=1`, `evidence: list[Evidence]`, `dcf_assumptions: DCFAssumptions`) (data-model.md WorkflowInput)
- [X] T004 [P] Create `src/aic/workflow/result.py` with `WorkflowResult` (`dcf_result: DCFResult`, `valuation_result: ValuationResult`, `thesis: InvestmentThesis`, `bull_assessment: AnalysisAssessment`, `bear_assessment: AnalysisAssessment`, `decision: CommitteeDecision`, `report: CommitteeReport`, `document: str`) (data-model.md WorkflowResult)
- [X] T005 [P] Modify `src/aic/report/report.py` to add `bull_assessment: AnalysisAssessment | None = None` and `bear_assessment: AnalysisAssessment | None = None` to `CommitteeReport` — additive only; the existing `assessment: AnalysisAssessment` field and every other existing field is left required and unchanged (FR-016; data-model.md "CommitteeReport additions"; contracts/workflow-interface.md "CommitteeReport contract addition")
- [X] T006 Modify `src/aic/report/document.py`'s `render_report_document` to render two distinct, labeled sections ("Bull Case Assessment" / "Bear Case Assessment") when both `report.bull_assessment` and `report.bear_assessment` are non-`None`, and to render its exact pre-existing single "Committee Assessment" section (from `report.assessment`) unchanged when either or both are `None` (depends on T005; FR-016; research.md "CommitteeReport gains two additive, optional fields")
- [X] T007 Add `WorkflowInput`, `WorkflowResult` exports to `src/aic/workflow/__init__.py` (depends on T002, T003, T004; same file)

**Checkpoint**: Foundation ready — user story implementation can now begin.

---

## Phase 3: User Story 1 - Run the Complete Investment Workflow End-to-End (Priority: P1) 🎯 MVP

**Goal**: Turn a company, financial snapshot(s), evidence, and DCF assumptions into a
validated `CommitteeReport` and rendered document via a single call, with every stage's
output correctly threaded into the next — zero manual assembly, one DCF computation reused
everywhere, both Bull and Bear represented in the final report, and the committee decision's
valuation reference correctly set.

**Independent Test**: Supply a complete `WorkflowInput` and a test-double provider to
`run_investment_workflow`; confirm it returns a validated `WorkflowResult` whose report's
evidence, thesis, valuation figures, Bull/Bear content, and committee decision are all
mutually consistent.

### Implementation for User Story 1

- [X] T008 [US1] Create `src/aic/workflow/orchestrator.py` with `run_investment_workflow(input: WorkflowInput, provider: LLMProvider) -> WorkflowResult` implementing the full control flow from data-model.md: `compute_dcf` first; a transient placeholder `InvestmentThesis` used only to construct the initial `InvestmentCase`; `generate_thesis` via `ResearchContext`; an updated `InvestmentCase` carrying the real thesis (via `model_copy`); `to_valuation_result` (fixed `confidence=1.0`, `valuation_date` = latest financial snapshot's `as_of`) to derive the `ValuationResult` Bull/Bear needs; `generate_bull_assessment` and `generate_bear_assessment` via `BullBearContext`; `generate_decision` via `CommitteeAdjudicationContext`, with its `valuation_reference` set via `model_copy` to the derived `ValuationResult`'s id; and a final `CommitteeReport` with `assessment=bull_assessment` plus both new `bull_assessment`/`bear_assessment` fields populated, rendered via `render_report_document` — no step catches any exception from an earlier step (depends on T003, T004, T006, T007; FR-001 through FR-010; data-model.md "Computation / control flow")
- [X] T009 [US1] Add `run_investment_workflow` export to `src/aic/workflow/__init__.py` (depends on T007, T008; same file)
- [X] T010 [P] [US1] Create `tests/unit/workflow/workflow_fakes.py` with a configurable `FakeLLMProvider` implementing `aic.research.provider.LLMProvider`, branching on the requested `schema` (and, for the two calls sharing `AssessmentDraft`, on distinguishing content in `system_prompt`, e.g. "Bull" vs "Bear") to return per-stage-configured content, or to raise a per-stage-configured error — local to this test directory, named `workflow_fakes.py` to avoid a collision with every other test directory's own fakes module (depends on T003 for import context, though structurally independent of production code)
- [X] T011 [US1] Create `tests/unit/workflow/test_workflow_orchestrator.py` covering the happy path: a full pipeline run returns a `WorkflowResult` whose `decision.valuation_reference` equals `valuation_result.valuation_id`; whose `report.bull_assessment`/`report.bear_assessment` are both populated; whose `document` contains the single `dcf_result`'s own figures; and whose `thesis` is the generated thesis, never the transient placeholder (depends on T008, T010; FR-001 through FR-010; spec US1 acceptance scenarios 1-4)
- [X] T012 [P] [US1] Create `tests/unit/workflow/test_workflow_input.py` covering `WorkflowInput` required-field validation and round-trip serialization (depends on T003)
- [X] T013 [P] [US1] Create `tests/unit/workflow/test_workflow_result.py` covering `WorkflowResult` construction and round-trip serialization with all fields populated (depends on T004)
- [X] T014 [P] [US1] Create `tests/unit/report/test_report_dual_assessment.py` covering: `CommitteeReport` accepts `bull_assessment`/`bear_assessment` as optional fields defaulting to `None`; constructing a `CommitteeReport` without them behaves exactly as the pre-existing single-`assessment` path; `render_report_document` shows two labeled sections when both are present, and its original single "Committee Assessment" section when both are absent — this file is new and does not modify `tests/unit/report/test_report.py` or `test_report_document.py` (depends on T006; FR-016; data-model.md "CommitteeReport additions")

**Checkpoint**: User Story 1 is fully functional and independently testable — this alone is the MVP.

---

## Phase 4: User Story 2 - Fail Explicitly and Stop the Pipeline When Any Stage Fails (Priority: P2)

**Goal**: A provider error or invalid intermediate result at any stage (research, Bull,
Bear, or committee) halts the whole workflow immediately, with no report ever produced.

**Independent Test**: Configure the fake provider to fail (or return an invalid response) at
each stage in turn, and confirm the workflow halts immediately with an explicit error and
produces no `WorkflowResult` in every case.

### Implementation for User Story 2

- [X] T015 [US2] Extend `tests/unit/workflow/test_workflow_orchestrator.py` with: a `DCFAssumptions` that is itself invalid (e.g., WACC not exceeding terminal growth) raising before a `WorkflowInput` can even be constructed; a research-stage provider error/invalid-response halting before any Bull, Bear, committee, or report stage is ever attempted; a Bull-stage failure halting before Bear, committee, or report; a Bear-stage failure halting before committee or report; a committee-stage failure halting before report — each using `workflow_fakes.py`'s per-stage error injection (depends on T008, T010; FR-011; spec US2 acceptance scenarios 1-4)

**Checkpoint**: User Stories 1 AND 2 both work independently.

---

## Phase 5: User Story 3 - Verify the Complete Workflow Without Calling Real External Providers (Priority: P3)

**Goal**: This feature's test suite is provably runnable with zero real provider credentials
or network access, and assembling the workflow introduced zero regression to any
pre-existing test.

**Independent Test**: Run the full `workflow` test suite with no provider credentials
configured and confirm it still passes completely; run the complete pre-existing test suite
and confirm every test that passed before this feature still passes, unmodified.

### Implementation for User Story 3

- [X] T016 [US3] Create `tests/unit/workflow/test_workflow_no_network_dependency.py` asserting `AppSettings` loads successfully with `AIC_OPENAI_API_KEY` unset and that no test in `tests/unit/workflow/` constructs or exercises a real `OpenAIProvider`/`openai` SDK client (depends on T010; FR-015; SC-003; spec US3 acceptance scenario 1)
- [X] T017 [US3] Run `uv run pytest tests/unit/domain tests/unit/dcf tests/unit/research tests/unit/bullbear tests/unit/committee tests/unit/report tests/unit/test_smoke.py -v` (every test that existed before this feature) and confirm every one still passes with no change to its own assertions (depends on T001, T005, T006; FR-016; SC-004; spec US3 acceptance scenario 2)

**Checkpoint**: All three user stories are independently functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Whole-feature validation against the spec's Success Criteria.

- [X] T018 [P] Run `uv run pytest -q` (the complete repository test suite) and confirm every test passes — validates SC-001, SC-002, SC-003, SC-004
- [X] T019 [P] Run `uv run ruff check .` and `uv run mypy src` and resolve any reported issues
- [X] T020 [P] Verify no LangGraph, no new financial calculation, and no second `LLMProvider`/`LLMCompletion`/`OpenAIProvider` definition anywhere in `src/aic/workflow/` — inspect every file (FR-012, FR-013, FR-014; contracts/workflow-interface.md non-goals)
- [X] T021 [P] Verify `src/aic/agents/` no longer exists and confirm zero remaining references to `aic.agents`/`agents/prompts` anywhere in `src/` or `tests/` (FR-017)
- [X] T022 [P] Verify `CommitteeReport.assessment`'s existing required-field contract is unchanged, and that neither `tests/unit/report/test_report.py` nor `tests/unit/report/test_report_document.py` needed any modification to keep passing (FR-016)
- [X] T023 Run the full `quickstart.md` validation sequence end-to-end and confirm every snippet behaves exactly as documented

---

## Phase 7: Convergence

- [X] T024 Add a test in `tests/unit/workflow/test_workflow_orchestrator.py` running the complete workflow with an empty `evidence` list, confirming it succeeds and that `thesis.supporting_evidence`, `bull_assessment.supporting_evidence`, `bear_assessment.supporting_evidence`, and `decision.referenced_evidence` are all empty rather than fabricated, per spec.md Edge Cases (missing)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: T001 is independent; T002 is independent of T001
- **Foundational (Phase 2)**: T003, T004, T005 are `[P]` (independent files); T006 depends on T005 (same conceptual change, different file); T007 depends on T002, T003, T004 (same file, `src/aic/workflow/__init__.py`) — BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational (Phase 2) completion
- **Polish (Phase 6)**: Depends on all three user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Depends only on Foundational — no dependency on US2/US3
- **User Story 2 (P2)**: Depends on `run_investment_workflow` (T008) and `workflow_fakes.py` (T010, both from US1) — extends US1's own test file with additional failure-mode tests, not new production code
- **User Story 3 (P3)**: Depends on `workflow_fakes.py` (T010, from US1) for T016; T017 depends on the Foundational changes (T001, T005, T006) being in place so the pre-existing suite can be re-verified against the final state

### Important: shared-file constraints

- `src/aic/workflow/__init__.py`: T002 → T007 → T009 must be applied in that order (same file)
- `src/aic/report/report.py` → `src/aic/report/document.py`: T005 must land before T006 (different files, but T006 reads the fields T005 adds)
- `tests/unit/workflow/test_workflow_orchestrator.py`: T011 → T015 must be applied in that order (same file)

### Parallel Opportunities

- T001 (delete `agents/`) can run in parallel with T002 (package shell) — fully independent
- T003, T004, T005 (Foundational) can run in parallel — independent files
- T010 (workflow_fakes.py) can run in parallel with T008 (orchestrator.py) — independent files, both only depend on Foundational
- T012, T013, T014 (US1 tests) can run in parallel with each other and with T011 once their respective dependencies land
- T016 (US3) can run in parallel with US2's T015 once T010 lands — independent files
- T018, T019, T020, T021, T022 (Polish) can all run in parallel — independent verification passes

---

## Parallel Example: Foundational Phase

```bash
# Launch the independent Foundational tasks together:
Task: "Create src/aic/workflow/input.py with WorkflowInput"
Task: "Create src/aic/workflow/result.py with WorkflowResult"
Task: "Modify src/aic/report/report.py to add bull_assessment/bear_assessment fields"
```

## Parallel Example: User Story 1 implementation and test-fixture creation

```bash
# Once Foundational is done, these proceed in parallel — different files:
Task: "Implement src/aic/workflow/orchestrator.py (US1)"
Task: "Create tests/unit/workflow/workflow_fakes.py (US1)"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: `uv run pytest tests/unit/workflow tests/unit/report -v` passes
   for the happy-path orchestration, both new `CommitteeReport` fields, and every
   `WorkflowInput`/`WorkflowResult` test, with zero real network calls
5. This alone delivers the MVP's defining deliverable — a working, evidence-traceable,
   single-DCF-computation, both-sides-represented end-to-end workflow

### Incremental Delivery

1. Setup + Foundational → dead code removed, `WorkflowInput`/`WorkflowResult`/
   `CommitteeReport` extension ready
2. Add User Story 1 → validate independently → working end-to-end workflow (MVP)
3. Add User Story 2 → validate independently → explicit halt-on-failure guarantee at every
   stage
4. Add User Story 3 → validate independently → zero-network property and zero-regression
   property both explicitly checked
5. Polish → full quickstart.md pass + scope/dependency verification

---

## Notes

- `[P]` tasks touch different files with no dependency between them
- `[Story]` label maps a task to its user story for traceability; Setup/Foundational/Polish
  tasks carry no story label
- `src/aic/workflow/__init__.py` is a shared file edited incrementally — respect the
  sequential order noted above
- This feature adds no new third-party dependency, reuses every existing stage's own
  contract unchanged (except the two additive `CommitteeReport` fields), and is the first
  feature in this project explicitly authorized to modify existing files and delete an
  existing, unused directory
- Commit after each task or logical group
- Stop at any checkpoint to validate a story independently
