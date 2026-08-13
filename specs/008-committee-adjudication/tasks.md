---

description: "Task list template for feature implementation"
---

# Tasks: Committee Adjudication Layer

**Input**: Design documents from `/specs/008-committee-adjudication/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/adjudication-interface.md, quickstart.md

**Tests**: Not TDD — this feature adds no new code (see plan.md Summary). Every task below is
a **verification** task: it re-runs or inspects existing, already-passing artifacts from
006-committee-decision-engine to demonstrate that this spec's requirements are already
satisfied, per the plan's Constitution Check and Complexity Tracking conclusion (reuse, not
reimplementation).

**Organization**: Tasks are grouped by user story (spec.md) to enable independent
verification of each story, mirroring how they would be organized if this were new work.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (independent commands, no shared state)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Include exact file paths for every artifact inspected or command run

## Path Conventions

Single project, `src`-layout (per plan.md). No new file under `src/` or `tests/` is
created by this feature — every task below runs against the existing
`src/aic/committee/` and `tests/unit/committee/` (006-committee-decision-engine), and
`tests/unit/report/` (005-investment-committee-report).

## Phase 1: Setup

**Purpose**: Confirm the environment matches what the plan requires — no new dependency.

- [X] T001 Run `uv sync` from the repository root and confirm it completes with no new package installed, per `quickstart.md` Prerequisites (plan.md Technical Context: "no new dependency")

**Checkpoint**: Environment confirmed ready. No project structure changes needed — this
feature adds none (plan.md Project Structure).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared types every user story depends on.

Every shared type this feature's user stories depend on
(`CommitteeAdjudicationContext`, `CommitteeDecisionDraft`, the existing
`aic.domain.CommitteeDecision`) already exists, from 002-domain-model and
006-committee-decision-engine (data-model.md). **No tasks are appended to this phase.**

---

## Phase 3: User Story 1 - Adjudicate Bull and Bear Cases Into a Structured Committee Decision (Priority: P1) 🎯 MVP

**Goal**: Confirm that `CommitteeAdjudicationContext` assembly and `generate_decision`
already turn an investment case, DCF result, bull assessment, and bear assessment into a
validated, evidence-traceable, non-averaging decision — exactly as this spec's FR-001–FR-008,
FR-014, and FR-017 require.

**Independent Test**: Run the quickstart snippet and the existing generator/context/prompt
test files below with no changes to any source file; all must pass.

### Verification for User Story 1

- [X] T002 [US1] Run the quickstart snippet in `specs/008-committee-adjudication/quickstart.md` ("User Story 1 — Adjudicate bull/bear cases into a decision") and confirm it prints `WATCH 1 1`, verifying `CommitteeAdjudicationContext` assembly (FR-001), decision synthesis via the existing provider abstraction (FR-002, FR-003), draft validation (FR-004), read-only DCF consumption (FR-006), and non-averaging rationale composition (FR-007) against `src/aic/committee/generator.py`
- [X] T003 [P] [US1] Run `uv run pytest tests/unit/committee/test_committee_generator.py -v` and confirm all 5 tests pass, verifying evidence-ID validation and rejection of untraceable references (FR-005), schema-invalid-response rejection (FR-004), recommendation restricted to the existing enum (FR-008), and provider-error propagation without a fabricated decision (FR-014)
- [X] T004 [P] [US1] Run `uv run pytest tests/unit/committee/test_committee_context.py tests/unit/committee/test_committee_prompt.py -v` and confirm all 8 tests pass, verifying `CommitteeAdjudicationContext` required-field validation and deterministic, context-derived prompt construction (FR-001)

**Checkpoint**: User Story 1 confirmed fully satisfied by existing code — no gap found.

---

## Phase 4: User Story 2 - Present Dissent When the Chair Overrules a Side (Priority: P2)

**Goal**: Confirm dissent is recorded when the Chair does not fully adopt one side, and left
empty (never fabricated) when the two sides are materially aligned — this spec's FR-009.

**Independent Test**: Run the existing dissent test file with no source changes; both cases
must pass.

### Verification for User Story 2

- [X] T005 [US2] Run `uv run pytest tests/unit/committee/test_dissent.py -v` and confirm both tests pass, verifying non-empty dissent is preserved unchanged when the fake provider supplies it, and dissent is empty (not fabricated) when it does not (FR-009, SC-004)

**Checkpoint**: User Story 2 confirmed fully satisfied by existing code — no gap found.

---

## Phase 5: User Story 3 - Verify Adjudication Without Calling a Real External LLM Service (Priority: P3)

**Goal**: Confirm this feature's full verification suite runs with zero real network calls
and no LLM provider credentials configured — this spec's FR-003, SC-003.

**Independent Test**: Run the entire `tests/unit/committee/` suite with no
`OPENAI_API_KEY`/`AIC_OPENAI_API_KEY` set; all tests must still pass.

### Verification for User Story 3

- [X] T006 [US3] Run `uv run pytest tests/unit/committee -v` with no LLM provider credentials configured and confirm all 16 tests pass with zero network access, per `tests/unit/committee/test_committee_no_network_dependency.py` (FR-003, SC-003)

**Checkpoint**: All three user stories confirmed independently satisfied by existing code.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Whole-feature validation against this spec's Success Criteria, including the
two criteria (FR-018/SC-008) that are specific to this spec and not covered by 006's own
task list.

- [X] T007 [P] Run `uv run pytest tests/unit/report -v` and confirm all 19 tests pass, verifying the existing `CommitteeDecision` this feature's adjudication step produces is already consumable by `CommitteeReport.decision` with no new adapter code anywhere in the repository (FR-018, SC-008)
- [X] T008 [P] Run `uv run ruff check .` and `uv run mypy src` and confirm zero issues across all 39 source files, verifying this feature left the codebase exactly as it found it
- [X] T009 Run the full `specs/008-committee-adjudication/quickstart.md` "Full validation in one pass" command sequence end-to-end and confirm every command behaves exactly as documented
- [X] T010 Confirm zero files were added or modified under `src/` or `tests/` by this feature (`git status` shows no changes attributable to 008 beyond its own `specs/008-committee-adjudication/` documentation), verifying the plan's Complexity Tracking conclusion that reuse — not reimplementation — satisfies this spec (FR-017; constitution Principle VIII)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: T001 only
- **Foundational (Phase 2)**: No tasks — proceed directly to Phase 3
- **User Stories (Phase 3-5)**: Independent of each other; all depend only on Phase 1 (environment confirmed)
- **Polish (Phase 6)**: Depends on all three user stories being verified

### User Story Dependencies

- **User Story 1 (P1)**: Depends only on Phase 1 — no dependency on US2/US3
- **User Story 2 (P2)**: Independent of US1/US3 — exercises a dedicated test file
- **User Story 3 (P3)**: Independent of US1/US2 — exercises the whole `committee` suite's network posture, not new behavior

### Parallel Opportunities

- T003 and T004 (US1) can run in parallel — independent pytest invocations
- T007 and T008 (Polish) can run in parallel — independent commands
- US1, US2, and US3's verification tasks (T002–T006) can all run in parallel once T001 completes — none depends on another

---

## Parallel Example: After Setup

```bash
# Once T001 (uv sync) completes, these proceed in parallel — independent commands:
Task: "Run tests/unit/committee/test_committee_generator.py (US1)"
Task: "Run tests/unit/committee/test_dissent.py (US2)"
Task: "Run tests/unit/committee (US3, no-network posture)"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 3: User Story 1 verification
3. **STOP and VALIDATE**: `uv run pytest tests/unit/committee/test_committee_generator.py tests/unit/committee/test_committee_context.py tests/unit/committee/test_committee_prompt.py -v` passes
4. This alone confirms the feature's core value — evidence-traceable, non-averaging
   adjudication — is already delivered

### Incremental Delivery

1. Setup → environment confirmed
2. Verify User Story 1 → confirmed (MVP)
3. Verify User Story 2 → confirmed (dissent handling)
4. Verify User Story 3 → confirmed (zero-network posture)
5. Polish → full quickstart.md pass + report-layer consumption + scope verification

---

## Notes

- Every task in this file is a verification task; none creates or modifies a source file
- `[P]` tasks are independent commands with no shared state
- `[Story]` label maps a task to its user story for traceability; Setup/Foundational/Polish
  tasks carry no story label; Phase 2 (Foundational) has no tasks for this feature
- This feature adds no new third-party dependency and modifies no existing file
- All ten tasks were executed and confirmed passing during `/speckit-plan` and
  `/speckit-tasks` for this feature (2026-08-13) — see `specs/008-committee-adjudication/quickstart.md` for the "Verified in this session" notes
