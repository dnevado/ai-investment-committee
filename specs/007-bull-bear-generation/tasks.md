---

description: "Task list template for feature implementation"
---

# Tasks: Bull/Bear Analysis Generation

**Input**: Design documents from `/specs/007-bull-bear-generation/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/bullbear-interface.md, quickstart.md

**Tests**: Not explicitly requested as TDD, but the spec requires zero real OpenAI calls in
this feature's own test suite, explicit rejection behavior for every validation rule, and an
explicit independence guarantee between the Bull and Bear calls — these are included as
normal implementation deliverables per story, not write-first TDD tasks.

**Organization**: Tasks are grouped by user story (spec.md) to enable independent
implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

Single project, `src`-layout (per plan.md): `src/aic/bullbear/`, `tests/unit/bullbear/`.
Depends on the existing `src/aic/domain/` (002) and `src/aic/research/` (004) packages,
unmodified by this feature. No new dependency is added and no existing file is touched —
this feature imports `LLMProvider`, `LLMCompletion`, and `OpenAIProvider` from
`aic.research` rather than redefining them. Every test file in `tests/unit/bullbear/` uses a
`bullbear`-qualified basename from the start to avoid the module-name collisions 006 hit
with `tests/unit/research/` (research.md).

## Phase 1: Setup

**Purpose**: Establish the `aic.bullbear` package shell.

- [X] T001 Create `src/aic/bullbear/__init__.py` as an initially empty module, establishing the `aic.bullbear` package (contents populated incrementally by later tasks)

**Checkpoint**: Package shell exists. All later `src/aic/bullbear/__init__.py` edits (T004, T007, T014) are sequential against each other from here on, since they share one file.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The shared types every user story depends on.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T002 [P] Create `src/aic/bullbear/context.py` with `BullBearContext` (`investment_case: InvestmentCase`, `valuation_result: ValuationResult`) (data-model.md BullBearContext)
- [X] T003 [P] Create `src/aic/bullbear/draft.py` with `AssessmentDraft` (`conclusion: str`, `confidence: float` bounded `0<=x<=1`, `arguments: list[str]`, `assumptions: list[str]`, `risks: list[str]`, `supporting_evidence_ids: list[UUID]`) — no defaults, extra fields forbidden (matching `aic.research.draft.ThesisDraft`/`aic.committee.draft.CommitteeDecisionDraft`'s strict-mode pattern); one schema shared by both roles (data-model.md AssessmentDraft; research.md "one shared AssessmentDraft schema")
- [X] T004 Add `BullBearContext`, `AssessmentDraft` exports to `src/aic/bullbear/__init__.py` (depends on T001, T002, T003; same file)

**Checkpoint**: Foundation ready — user story implementation can now begin.

---

## Phase 3: User Story 1 - Generate an Evidence-Traceable Bull Case (Priority: P1) 🎯 MVP

**Goal**: Turn an `InvestmentCase` and a `ValuationResult` into a validated `AnalysisAssessment` framed as the strongest credible upside case, via a swappable LLM provider (reused from 004), with every supporting-evidence entry traceable, zero financial calculation performed by the LLM, and confidence bounded.

**Independent Test**: Supply a complete `BullBearContext` and a test-double provider; confirm `generate_bull_assessment` returns a validated `AnalysisAssessment` whose evidence is traceable to the input, and that an untraceable evidence reference, a schema-invalid response, an out-of-bounds confidence, or a provider error each fail explicitly.

### Implementation for User Story 1

- [X] T005 [US1] Create `src/aic/bullbear/prompt.py` with `build_bull_prompt(context: BullBearContext) -> tuple[str, str]` — deterministic system/user prompt construction (company, thesis, evidence, valuation result) framing the strongest credible upside case (catalysts and outperformance conditions folded into the arguments the prompt asks for), no I/O; also define the shared private rendering helpers (`_render_evidence`, `_render_thesis`, `_render_valuation`) that `build_bear_prompt` (T012) will reuse (depends on T002; FR-001, FR-002)
- [X] T006 [US1] Create `src/aic/bullbear/generator.py` with a shared private `_generate(context, provider, role, build_prompt) -> AnalysisAssessment` helper (calls `provider.complete_structured` with `AssessmentDraft`, logs token usage/latency tagged with `role`, validates the raw response, resolves `supporting_evidence_ids` against `context.investment_case.evidence` raising explicitly on any unknown ID, constructs the unmodified `AnalysisAssessment`) and the public `generate_bull_assessment(context: BullBearContext, provider: LLMProvider) -> AnalysisAssessment` calling `_generate(..., role="bull", build_prompt=build_bull_prompt)` (depends on T002, T003, T005; FR-002, FR-004, FR-006, FR-007, FR-008, FR-009, FR-016; data-model.md "Computation / control flow")
- [X] T007 [US1] Add `build_bull_prompt`, `generate_bull_assessment` exports to `src/aic/bullbear/__init__.py` (depends on T004, T005, T006; same file)
- [X] T008 [P] [US1] Create `tests/unit/bullbear/bullbear_fakes.py` with a configurable `FakeLLMProvider` implementing `aic.research.provider.LLMProvider` (returns caller-supplied content/usage/latency, or raises a caller-supplied error) — local to this test directory, named `bullbear_fakes.py` (not `fakes.py`) to avoid a collision with `tests/unit/research/fakes.py`/`tests/unit/committee/committee_fakes.py` (research.md); reused by US1, US2, and US3's tests (depends on T002 for import context, though structurally independent of production code)
- [X] T009 [US1] Create `tests/unit/bullbear/test_bullbear_generator.py` covering the Bull role: valid generation with traceable evidence populating conclusion/confidence/arguments/assumptions/risks; rejection of an untraceable `evidence_id`; rejection of an `AssessmentDraft`-schema-invalid response; rejection of an out-of-bounds `confidence`; explicit propagation of a provider error with no fabricated fallback assessment (depends on T006, T008; FR-002, FR-006, FR-007, FR-008, FR-009, FR-016; spec US1 acceptance scenarios 1-4)
- [X] T010 [P] [US1] Create `tests/unit/bullbear/test_bullbear_prompt.py` covering deterministic `build_bull_prompt` construction from a `BullBearContext` (depends on T005; FR-001)
- [X] T011 [P] [US1] Create `tests/unit/bullbear/test_bullbear_context.py` covering `BullBearContext` required-field validation and round-trip serialization (depends on T002)

**Checkpoint**: User Story 1 is fully functional and independently testable — this alone is the MVP.

---

## Phase 4: User Story 2 - Generate an Evidence-Traceable Bear Case, Independently of the Bull Case (Priority: P2)

**Goal**: Turn the same `BullBearContext` into a validated `AnalysisAssessment` framed as an independent challenge to the thesis, via its own separate LLM call that never includes the Bull assessment's content (and vice versa).

**Independent Test**: Generate a Bull case and a Bear case for the same context and confirm the Bear generation call's prompt contains no content from the Bull assessment (and vice versa); confirm the Bear case identifies downside risks, weak assumptions, adverse scenarios, and invalidation conditions, with evidence traceable to the supplied input.

### Implementation for User Story 2

- [X] T012 [US2] Extend `src/aic/bullbear/prompt.py` to add `build_bear_prompt(context: BullBearContext) -> tuple[str, str]` — deterministic system/user prompt construction framing an independent challenge to the thesis (downside risks, weak assumptions, adverse scenarios, and invalidation conditions folded into the arguments/risks the prompt asks for), reusing the shared private rendering helpers from T005, no I/O (depends on T005; same file; FR-001, FR-003)
- [X] T013 [US2] Extend `src/aic/bullbear/generator.py` to add the public `generate_bear_assessment(context: BullBearContext, provider: LLMProvider) -> AnalysisAssessment` calling the shared `_generate(..., role="bear", build_prompt=build_bear_prompt)` from T006 — MUST NOT read, receive, or otherwise depend on any Bull-role output (depends on T006, T012; same file; FR-003, FR-004, FR-006, FR-007, FR-008, FR-009, FR-016)
- [X] T014 [US2] Add `build_bear_prompt`, `generate_bear_assessment` exports to `src/aic/bullbear/__init__.py` (depends on T007, T012, T013; same file)
- [X] T015 [US2] Extend `tests/unit/bullbear/test_bullbear_generator.py` with the Bear role: valid generation with traceable evidence; rejection of an untraceable `evidence_id`; rejection of a schema-invalid response; rejection of an out-of-bounds `confidence`; explicit propagation of a provider error; and an **independence test** asserting that generating a Bull case then a Bear case (or vice versa) for the same context never places one's conclusion/arguments into the other's prompt (depends on T013, T008; FR-004, FR-006, FR-007, FR-008, FR-009, FR-016; spec US2 acceptance scenarios 1-4)
- [X] T016 [P] [US2] Extend `tests/unit/bullbear/test_bullbear_prompt.py` with deterministic `build_bear_prompt` construction and content tests (depends on T012; FR-001)

**Checkpoint**: User Stories 1 AND 2 both work independently, and their independence from each other is explicitly verified.

---

## Phase 5: User Story 3 - Verify Bull and Bear Generation Without Calling the Real OpenAI API (Priority: P3)

**Goal**: This feature's test suite is provably runnable with zero real OpenAI credentials or network access, for both the Bull and the Bear generation paths.

**Independent Test**: Run the full `bullbear` test suite with `AIC_OPENAI_API_KEY` unset and no network access, and confirm it still passes completely.

### Implementation for User Story 3

- [X] T017 [US3] Create `tests/unit/bullbear/test_bullbear_no_network_dependency.py` asserting `AppSettings` loads successfully with `AIC_OPENAI_API_KEY` unset (reusing 004's settings field — no field is required) and that no test in `tests/unit/bullbear/` constructs or exercises the real `OpenAIProvider`/`openai` SDK client (depends on T008; FR-005; SC-003; spec US3 acceptance scenario 1)

**Checkpoint**: All three user stories are independently functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Whole-feature validation against the spec's Success Criteria.

- [X] T018 [P] Run `uv run pytest tests/unit/bullbear -v` and confirm every test passes — validates SC-001, SC-002, SC-003, SC-004
- [X] T019 [P] Run `uv run ruff check .` and `uv run mypy src` and resolve any reported issues
- [X] T020 [P] Verify no new provider abstraction, no `CommitteeDecision` generation, no report rendering, and no duplicated DCF/valuation logic anywhere in `src/aic/bullbear/` — inspect every file (FR-005, FR-010, FR-011, FR-012; contracts/bullbear-interface.md non-goals)
- [X] T021 [P] Verify no financial calculation exists anywhere in `src/aic/bullbear/` and confirm `AssessmentDraft`'s only numeric field is the bounded `confidence` float (FR-009; SC-005)
- [X] T022 [P] Verify `AnalysisAssessment` is reused unchanged — no `BullAssessment`/`BearAssessment` type or subclass exists anywhere in `src/aic/bullbear/` (FR-002, FR-003, FR-018)
- [X] T023 Run the full `quickstart.md` validation sequence end-to-end and confirm every snippet behaves exactly as documented

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: T001 only
- **Foundational (Phase 2)**: T002, T003 are `[P]` (independent files); T004 depends on T001-T003 (same file, `src/aic/bullbear/__init__.py`) — BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational (Phase 2) completion
- **Polish (Phase 6)**: Depends on all three user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Depends only on Foundational — no dependency on US2/US3
- **User Story 2 (P2)**: Depends on US1's `prompt.py`/`generator.py`/`__init__.py` (T005-T007) since it extends the same files, and on `bullbear_fakes.py` (T008, from US1) for its own tests
- **User Story 3 (P3)**: Depends on `bullbear_fakes.py` (T008, from US1) — verifies a property of the whole test suite, not new production code

### Important: shared-file constraints

- `src/aic/bullbear/__init__.py`: T001 → T004 → T007 → T014 must be applied in that order (same file)
- `src/aic/bullbear/prompt.py`: T005 → T012 must be applied in that order (same file — US2 extends US1's file)
- `src/aic/bullbear/generator.py`: T006 → T013 must be applied in that order (same file — US2 extends US1's file)
- `tests/unit/bullbear/test_bullbear_generator.py`: T009 → T015 must be applied in that order (same file)
- `tests/unit/bullbear/test_bullbear_prompt.py`: T010 → T016 must be applied in that order (same file)

### Parallel Opportunities

- T002, T003 (Foundational) can run in parallel — independent files
- T008 (bullbear_fakes.py) can run in parallel with T005 (prompt.py) and T006 (generator.py) — independent files, all only depend on Foundational
- T010 and T011 (US1 tests) can run in parallel with each other once their respective implementation tasks land
- T016 (US2 prompt test) can run in parallel with T015 (US2 generator test) once T012/T013 land — independent files
- T017 (US3) can run in parallel with US2's tasks once T008 lands — independent file
- T018, T019, T020, T021, T022 (Polish) can all run in parallel — independent verification passes

---

## Parallel Example: Foundational Phase

```bash
# Launch the independent Foundational file-creation tasks together:
Task: "Create src/aic/bullbear/context.py with BullBearContext"
Task: "Create src/aic/bullbear/draft.py with AssessmentDraft"
```

## Parallel Example: User Story 1 implementation and test-fixture creation

```bash
# Once Foundational is done, these proceed in parallel — different files:
Task: "Implement src/aic/bullbear/prompt.py (build_bull_prompt) (US1)"
Task: "Create tests/unit/bullbear/bullbear_fakes.py (US1)"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: `uv run pytest tests/unit/bullbear -v` passes for Bull-role
   generation, prompt, and context tests, with zero real OpenAI calls
5. This alone delivers half the product hypothesis — a working, evidence-traceable Bull
   case generator; the Bear case (US2) is the adversarial complement

### Incremental Delivery

1. Setup + Foundational → `BullBearContext`/`AssessmentDraft` ready
2. Add User Story 1 → validate independently → working Bull generator (MVP)
3. Add User Story 2 → validate independently → working, independently-verified Bear
   generator
4. Add User Story 3 → validate independently → zero-credential test-suite property
   explicitly checked
5. Polish → full quickstart.md pass + scope/dependency verification

---

## Notes

- `[P]` tasks touch different files with no dependency between them
- `[Story]` label maps a task to its user story for traceability; Setup/Foundational/Polish
  tasks carry no story label
- `src/aic/bullbear/__init__.py`, `prompt.py`, `generator.py`,
  `test_bullbear_generator.py`, and `test_bullbear_prompt.py` are shared files edited
  incrementally across US1 and US2 — respect the sequential order noted above
- This feature adds no new third-party dependency and modifies no existing file — it reuses
  `LLMProvider`/`LLMCompletion`/`OpenAIProvider` from `aic.research` (004) verbatim
- Commit after each task or logical group
- Stop at any checkpoint to validate a story independently
