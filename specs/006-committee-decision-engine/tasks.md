---

description: "Task list template for feature implementation"
---

# Tasks: Investment Committee Decision Engine

**Input**: Design documents from `/specs/006-committee-decision-engine/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/committee-interface.md, quickstart.md

**Tests**: Not explicitly requested as TDD, but the spec requires zero real OpenAI calls in
this feature's own test suite and explicit rejection behavior for every validation rule —
these are included as normal implementation deliverables per story, not write-first TDD
tasks.

**Organization**: Tasks are grouped by user story (spec.md) to enable independent
implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

Single project, `src`-layout (per plan.md): `src/aic/committee/`, `tests/unit/committee/`.
Depends on the existing `src/aic/domain/` (002), `src/aic/dcf/` (003), and
`src/aic/research/` (004) packages, unmodified by this feature. No new dependency is added
and no existing file is touched — this feature imports `LLMProvider`, `LLMCompletion`, and
`OpenAIProvider` from `aic.research` rather than redefining them.

## Phase 1: Setup

**Purpose**: Establish the `aic.committee` package shell.

- [X] T001 Create `src/aic/committee/__init__.py` as an initially empty module, establishing the `aic.committee` package (contents populated incrementally by later tasks)

**Checkpoint**: Package shell exists. All later `src/aic/committee/__init__.py` edits (T004, T007) are sequential against each other from here on, since they share one file.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The shared types every user story depends on.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T002 [P] Create `src/aic/committee/context.py` with `CommitteeAdjudicationContext` (`investment_case: InvestmentCase`, `dcf_result: DCFResult`, `bull_assessment: AnalysisAssessment`, `bear_assessment: AnalysisAssessment`) (data-model.md CommitteeAdjudicationContext)
- [X] T003 [P] Create `src/aic/committee/draft.py` with `CommitteeDecisionDraft` (`central_thesis: str`, `key_disagreements: list[str]`, `valuation_summary: str`, `downside_risks: list[str]`, `invalidation_conditions: list[str]`, `recommendation: Recommendation`, `confidence: float` bounded `0<=x<=1`, `dissent: list[str]`, `supporting_evidence_ids: list[UUID]`) — a separate required field per constitution-listed Committee Chair responsibility, no defaults, extra fields forbidden (matching `aic.research.draft.ThesisDraft`'s strict-mode pattern) (data-model.md CommitteeDecisionDraft; research.md "separate required field per Chair responsibility")
- [X] T004 Add `CommitteeAdjudicationContext`, `CommitteeDecisionDraft` exports to `src/aic/committee/__init__.py` (depends on T001, T002, T003; same file)

**Checkpoint**: Foundation ready — user story implementation can now begin.

---

## Phase 3: User Story 1 - Adjudicate Bull and Bear Cases Into a Structured Committee Decision (Priority: P1) 🎯 MVP

**Goal**: Turn an `InvestmentCase`, a `DCFResult`, a bull `AnalysisAssessment`, and a bear
`AnalysisAssessment` into a validated `CommitteeDecision` via a swappable LLM provider
(reused from 004), with every referenced evidence entry traceable, zero financial
calculation performed by the LLM, and the recommendation restricted to the existing enum.

**Independent Test**: Supply a complete `CommitteeAdjudicationContext` and a test-double
provider; confirm `generate_decision` returns a validated `CommitteeDecision` whose
referenced evidence is traceable to the input, and that an untraceable evidence reference, a
schema-invalid response, or a provider error each fail explicitly.

### Implementation for User Story 1

- [X] T005 [P] [US1] Create `src/aic/committee/prompt.py` with `build_prompt(context: CommitteeAdjudicationContext) -> tuple[str, str]` — deterministic system/user prompt construction from the investment case (company, thesis, evidence), DCF result, and bull/bear assessments in `context`, no I/O (depends on T002; FR-001)
- [X] T006 [US1] Create `src/aic/committee/generator.py` with `generate_decision(context: CommitteeAdjudicationContext, provider: LLMProvider) -> CommitteeDecision` — calls `provider.complete_structured` with `CommitteeDecisionDraft` (importing `LLMProvider`/`LLMCompletion` from `aic.research.provider`), logs token usage/latency, validates the raw response, resolves `supporting_evidence_ids` against `context.investment_case.evidence` (raising explicitly on any unknown ID), deterministically composes the final `rationale` string via a private `_compose_rationale(draft)` helper from `central_thesis`/`key_disagreements`/`valuation_summary`/`downside_risks`/`invalidation_conditions`, and constructs the unmodified `CommitteeDecision` with `valuation_reference=None` (depends on T002, T003, T005; FR-002, FR-004, FR-005, FR-006, FR-007, FR-008, FR-013; data-model.md "Computation / control flow")
- [X] T007 [US1] Add `build_prompt`, `generate_decision` exports to `src/aic/committee/__init__.py` (depends on T004, T005, T006; same file)
- [X] T008 [P] [US1] Create `tests/unit/committee/committee_fakes.py` with a configurable `FakeLLMProvider` implementing `aic.research.provider.LLMProvider` (returns caller-supplied content/usage/latency, or raises a caller-supplied error) — local to this test directory, named `committee_fakes.py` (not `fakes.py`) to avoid a pytest module-name collision with `tests/unit/research/fakes.py` (research.md); reused by US1, US2, and US3's tests (depends on T002 for import context, though structurally independent of production code)
- [X] T009 [US1] Create `tests/unit/committee/test_committee_generator.py` (named to avoid a collision with `tests/unit/research/test_generator.py`) covering: valid adjudication with traceable evidence and a composed `rationale` containing all five draft sections; rejection of an untraceable `evidence_id`; rejection of a `CommitteeDecisionDraft`-schema-invalid response; explicit propagation of a provider error with no fabricated fallback decision; `recommendation` restricted to the `Recommendation` enum (depends on T006, T008; FR-002, FR-004, FR-005, FR-006, FR-007, FR-008, FR-013; spec US1 acceptance scenarios 1-5)
- [X] T010 [P] [US1] Create `tests/unit/committee/test_committee_prompt.py` (named to avoid a collision with `tests/unit/research/test_prompt.py`) covering deterministic prompt construction from a `CommitteeAdjudicationContext` (depends on T005; FR-001)
- [X] T011 [P] [US1] Create `tests/unit/committee/test_committee_context.py` (named to avoid a collision with `tests/unit/research/test_context.py`) covering `CommitteeAdjudicationContext` required-field validation and round-trip serialization (depends on T002)

**Checkpoint**: User Story 1 is fully functional and independently testable — this alone is the MVP.

---

## Phase 4: User Story 2 - Present Dissent When the Chair Overrules a Side (Priority: P2)

**Goal**: When the Chair's decision does not fully adopt the bull or the bear position,
that disagreement is recorded on the resulting `CommitteeDecision` as dissent; when the two
sides are materially aligned, dissent is empty rather than fabricated.

**Independent Test**: Supply a fake-provider response with non-empty dissent and confirm it
is preserved unchanged on the resulting `CommitteeDecision`; supply a fake-provider response
with empty dissent and confirm the decision's dissent is empty.

### Implementation for User Story 2

- [X] T012 [P] [US2] Create `tests/unit/committee/test_dissent.py` covering: a fake-provider response with non-empty `dissent` produces a `CommitteeDecision` whose `dissent` matches unchanged; a fake-provider response with empty `dissent` produces a `CommitteeDecision` with an empty `dissent` list, never fabricated (depends on T006, T008; FR-009; spec US2 acceptance scenarios 1-2)

**Checkpoint**: User Stories 1 AND 2 both work independently.

---

## Phase 5: User Story 3 - Verify the Feature Without Calling the Real OpenAI API (Priority: P3)

**Goal**: This feature's test suite is provably runnable with zero real OpenAI credentials
or network access.

**Independent Test**: Run the full `committee` test suite with `AIC_OPENAI_API_KEY` unset
and no network access, and confirm it still passes completely.

### Implementation for User Story 3

- [X] T013 [US3] Create `tests/unit/committee/test_committee_no_network_dependency.py` (named to avoid a collision with `tests/unit/research/test_no_network_dependency.py`) asserting `AppSettings` loads successfully with `AIC_OPENAI_API_KEY` unset (reusing 004's settings field — no field is required) and that no test in `tests/unit/committee/` constructs or exercises the real `OpenAIProvider`/`openai` SDK client (depends on T008; FR-003; SC-003; spec US3 acceptance scenario 1)

**Checkpoint**: All three user stories are independently functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Whole-feature validation against the spec's Success Criteria.

- [X] T014 [P] Run `uv run pytest tests/unit/committee -v` and confirm every test passes — validates SC-001, SC-002, SC-003, SC-004
- [X] T015 [P] Run `uv run ruff check .` and `uv run mypy src` and resolve any reported issues
- [X] T016 [P] Verify no LangGraph/multi-agent orchestration, no report-rendering duplication, and no second `LLMProvider`/`LLMCompletion`/`OpenAIProvider` definition anywhere in `src/aic/committee/` — inspect every file (FR-010; contracts/committee-interface.md non-goals)
- [X] T017 [P] Verify no financial calculation exists anywhere in `src/aic/committee/` and confirm `CommitteeDecisionDraft`'s only numeric field is the bounded `confidence` float (FR-006; SC-005)
- [X] T018 [P] Verify every producible `recommendation` is restricted to the existing `Recommendation` enum — no new enum, string literal, or bypass exists in `src/aic/committee/` (FR-008; SC-006)
- [X] T019 Run the full `quickstart.md` validation sequence end-to-end and confirm every snippet behaves exactly as documented

---

## Phase 7: Convergence

- [X] T020 CRITICAL: Include the confidence/conviction score in `_compose_rationale` in `src/aic/committee/generator.py` (currently `draft.confidence` is validated but never surfaces anywhere in the returned `CommitteeDecision`), and add a test in `tests/unit/committee/test_committee_generator.py` asserting the composed rationale includes it, per US1/AC1, FR-002, and the constitution's "produce a recommendation... with a conviction score" requirement (missing)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: T001 only
- **Foundational (Phase 2)**: T002, T003 are `[P]` (independent files); T004 depends on T001-T003 (same file, `src/aic/committee/__init__.py`) — BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational (Phase 2) completion
- **Polish (Phase 6)**: Depends on all three user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Depends only on Foundational — no dependency on US2/US3
- **User Story 2 (P2)**: Depends on `generate_decision` (T006, from US1) and `FakeLLMProvider` (T008, from US1) — tests an already-implemented behavior from a dedicated file, not new production code
- **User Story 3 (P3)**: Depends on `FakeLLMProvider` (T008, from US1) — verifies a property of the whole test suite, not new production code

### Important: shared-file constraints

- `src/aic/committee/__init__.py`: T001 → T004 → T007 must be applied in that order (same file)

### Parallel Opportunities

- T002, T003 (Foundational) can run in parallel — independent files
- T005 (prompt.py) and T008 (committee_fakes.py) can run in parallel with each other — independent files, both only depend on Foundational
- T010 and T011 (US1 tests) can run in parallel with each other once their respective implementation tasks land
- T012 (US2) and T013 (US3) can run in parallel with each other once T006/T008 land — independent files
- T014, T015, T016, T017, T018 (Polish) can all run in parallel — independent verification passes

---

## Parallel Example: Foundational Phase

```bash
# Launch the independent Foundational file-creation tasks together:
Task: "Create src/aic/committee/context.py with CommitteeAdjudicationContext"
Task: "Create src/aic/committee/draft.py with CommitteeDecisionDraft"
```

## Parallel Example: User Story 2 and User Story 3 together

```bash
# Once T006 (generate_decision) and T008 (FakeLLMProvider) land, these are independent:
Task: "Write tests/unit/committee/test_dissent.py (US2)"
Task: "Write tests/unit/committee/test_committee_no_network_dependency.py (US3)"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: `uv run pytest tests/unit/committee -v` passes for adjudication,
   prompt, and context tests, with zero real OpenAI calls
5. This alone delivers the core product hypothesis — a working, evidence-traceable,
   non-averaging Committee Chair adjudication step

### Incremental Delivery

1. Setup + Foundational → `CommitteeAdjudicationContext`/`CommitteeDecisionDraft` ready
2. Add User Story 1 → validate independently → working decision engine (MVP)
3. Add User Story 2 → validate independently → explicit dissent-present/absent guarantee
4. Add User Story 3 → validate independently → zero-credential test-suite property
   explicitly checked
5. Polish → full quickstart.md pass + scope/dependency verification

---

## Notes

- `[P]` tasks touch different files with no dependency between them
- `[Story]` label maps a task to its user story for traceability; Setup/Foundational/Polish
  tasks carry no story label
- `src/aic/committee/__init__.py` is a shared file edited incrementally — respect the
  sequential order noted above
- This feature adds no new third-party dependency and modifies no existing file — it reuses
  `LLMProvider`/`LLMCompletion`/`OpenAIProvider` from `aic.research` (004) verbatim
- Commit after each task or logical group
- Stop at any checkpoint to validate a story independently
