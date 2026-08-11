---

description: "Task list template for feature implementation"
---

# Tasks: Investment Research & Thesis Generation

**Input**: Design documents from `/specs/004-investment-research-thesis/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/research-interface.md, quickstart.md

**Tests**: Not explicitly requested as TDD, but the spec requires zero real OpenAI calls in this feature's own test suite and explicit rejection behavior for every validation rule — these are included as normal implementation deliverables per story, not write-first TDD tasks.

**Organization**: Tasks are grouped by user story (spec.md) to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

Single project, `src`-layout (per plan.md): `src/aic/research/`, `tests/unit/research/`.
Depends on the existing `src/aic/domain/` (002) and `src/aic/dcf/` (003) packages,
unmodified by this feature except for one new field on `src/aic/settings.py`.

## Phase 1: Setup

**Purpose**: Add the new `openai` dependency and establish the `aic.research` package shell.

- [X] T001 Add `openai` to `[project] dependencies` in `pyproject.toml` (research.md "`openai` SDK as a new, sanctioned dependency")
- [X] T002 Run `uv sync` to install the new dependency (depends on T001)
- [X] T003 Create `src/aic/research/__init__.py` as an initially empty module, establishing the `aic.research` package (contents populated incrementally by later tasks)

**Checkpoint**: Package shell and dependency exist. All later `src/aic/research/__init__.py` edits (T008, T012, T018) are sequential against each other from here on, since they share one file.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The shared types every user story depends on, plus the settings addition.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Create `src/aic/research/context.py` with `ResearchContext` (`investment_case: InvestmentCase`, `dcf_result: DCFResult`) (data-model.md ResearchContext)
- [X] T005 [P] Create `src/aic/research/draft.py` with `ThesisDraft` (`summary: str`, `supporting_evidence_ids: list[UUID]`, `key_assumptions`, `key_risks`, `invalidation_conditions: list[str]`) — no numeric/financial field, structurally enforcing FR-006 (data-model.md ThesisDraft)
- [X] T006 [P] Create `src/aic/research/provider.py` with `LLMCompletion` (`content: dict`, `prompt_tokens: int`, `completion_tokens: int`, `latency_ms: float`) and the `LLMProvider` `Protocol` (`complete_structured(*, system_prompt, user_prompt, schema) -> LLMCompletion`) (data-model.md LLMCompletion/LLMProvider; contracts/research-interface.md)
- [X] T007 [P] Add `openai_api_key: str | None = Field(default=None, validation_alias="AIC_OPENAI_API_KEY")` to `AppSettings` in `src/aic/settings.py` (research.md "Settings extension"; FR-009, FR-010)
- [X] T008 Add `ResearchContext`, `ThesisDraft`, `LLMCompletion`, `LLMProvider` exports to `src/aic/research/__init__.py` (depends on T003, T004, T005, T006; same file)

**Checkpoint**: Foundation ready — user story implementation can now begin.

---

## Phase 3: User Story 1 - Generate an Evidence-Traceable Investment Thesis (Priority: P1) 🎯 MVP

**Goal**: A developer can turn a `ResearchContext` into a validated `InvestmentThesis` via a swappable LLM provider, with every `supporting_evidence` entry traceable to the supplied input and zero financial calculation performed by the LLM.

**Independent Test**: Supply a complete `ResearchContext` and a test-double provider; confirm `generate_thesis` returns a validated `InvestmentThesis` whose evidence is traceable to the input, and that an untraceable evidence reference, a schema-invalid response, or a provider error each fail explicitly.

### Implementation for User Story 1

- [X] T009 [P] [US1] Create `src/aic/research/prompt.py` with `build_prompt(context: ResearchContext) -> tuple[str, str]` — deterministic system/user prompt construction from the company, financial snapshots, evidence, and DCF result in `context`, no I/O (depends on T004; FR-001)
- [X] T010 [P] [US1] Create `src/aic/research/openai_provider.py` with `OpenAIProvider` implementing `LLMProvider` via the `openai` SDK — reads its API key only from a caller-supplied value (never reads settings/env itself), raises explicitly if used without a usable key (depends on T002, T006; FR-009, FR-010; contracts/research-interface.md "OpenAIProvider contract")
- [X] T011 [US1] Create `src/aic/research/generator.py` with `generate_thesis(context: ResearchContext, provider: LLMProvider) -> InvestmentThesis` — calls `provider.complete_structured` with `ThesisDraft`, logs token usage/latency, validates the raw response against `ThesisDraft`, resolves `supporting_evidence_ids` against `context.investment_case.evidence` (raising explicitly on any unknown ID), and constructs the unmodified `InvestmentThesis` from the resolved evidence (depends on T004, T005, T006, T009; FR-002, FR-004, FR-005, FR-006, FR-013; data-model.md "Computation / control flow")
- [X] T012 [US1] Add `build_prompt`, `OpenAIProvider`, `generate_thesis` exports to `src/aic/research/__init__.py` (depends on T008, T009, T010, T011; same file)
- [X] T013 [P] [US1] Create `tests/unit/research/fakes.py` with a configurable `FakeLLMProvider` implementing `LLMProvider` (returns caller-supplied content/usage/latency, or raises a caller-supplied error) — reused by US1's and US3's tests (depends on T006)
- [X] T014 [US1] Create `tests/unit/research/test_generator.py` covering: valid generation with traceable evidence, rejection of an untraceable `evidence_id`, rejection of a `ThesisDraft`-schema-invalid response, and explicit propagation of a provider error with no fabricated fallback thesis (depends on T011, T013; FR-002, FR-004, FR-005, FR-006, FR-013; spec US1 acceptance scenarios 1-4)
- [X] T015 [P] [US1] Create `tests/unit/research/test_prompt.py` covering deterministic prompt construction from a `ResearchContext` (depends on T009; FR-001)
- [X] T016 [P] [US1] Create `tests/unit/research/test_openai_provider.py` mocking the `openai` SDK client (not the network) and asserting `OpenAIProvider` maps a mocked response into a correct `LLMCompletion`, with zero real network calls (depends on T010; research.md "OpenAI adapter tests mock the SDK client")

**Checkpoint**: User Story 1 is fully functional and independently testable — this alone is the MVP.

---

## Phase 4: User Story 2 - Render the Thesis Into a Human-Readable Document (Priority: P2)

**Goal**: A validated `InvestmentThesis` (from any source, not just this feature's own generator) can be deterministically rendered into a human-readable Markdown document.

**Independent Test**: Render the same `InvestmentThesis` twice and confirm the two documents are identical and contain exactly the thesis's structured content.

### Implementation for User Story 2

- [X] T017 [US2] Create `src/aic/research/document.py` with `render_thesis_document(thesis: InvestmentThesis) -> str` — pure Markdown rendering (no I/O, no randomness), depends only on the existing `aic.domain.InvestmentThesis`, genuinely independent of this feature's Foundational types (FR-011, FR-012)
- [X] T018 [US2] Add `render_thesis_document` export to `src/aic/research/__init__.py` (depends on T008, T012, T017; same file)
- [X] T019 [P] [US2] Create `tests/unit/research/test_document.py` covering: the document contains exactly the thesis's summary/evidence/assumptions/risks/invalidation conditions with no invented content, and two renders of the same thesis are byte-identical (depends on T017; FR-011, FR-012; spec US2 acceptance scenarios 1-2)

**Checkpoint**: User Stories 1 AND 2 both work independently.

---

## Phase 5: User Story 3 - Verify the Feature Without Calling the Real OpenAI API (Priority: P3)

**Goal**: This feature's test suite is provably runnable with zero real OpenAI credentials or network access.

**Independent Test**: Run the full `research` test suite with `AIC_OPENAI_API_KEY` unset and no network access, and confirm it still passes completely.

### Implementation for User Story 3

- [X] T020 [US3] Create `tests/unit/research/test_no_network_dependency.py` asserting `AppSettings` loads successfully with `AIC_OPENAI_API_KEY` unset (no field is required), as an explicit, checked property rather than an assumed byproduct of using fakes elsewhere (depends on T007, T013; FR-003; SC-003; spec US3 acceptance scenario 1)

**Checkpoint**: All three user stories are independently functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Whole-feature validation against the spec's Success Criteria.

- [X] T021 [P] Run `uv run pytest tests/unit/research -v` and confirm every test passes — validates SC-001, SC-002, SC-003, SC-004
- [X] T022 [P] Run `uv run ruff check .` and `uv run mypy src` and resolve any reported issues
- [X] T023 [P] Verify no LangGraph/multi-agent orchestration, no `BUY`/`WATCH`/`AVOID`/`CommitteeDecision`/`AnalysisAssessment` content, and no persistence anywhere in `src/aic/research/` — inspect every file (FR-007, FR-008, FR-014; SC-006; spec out-of-scope list)
- [X] T024 [P] Verify no financial calculation exists anywhere in `src/aic/research/` and confirm `ThesisDraft` has no numeric field (FR-006; SC-005)
- [X] T025 Run the full `quickstart.md` validation sequence end-to-end and confirm every snippet behaves exactly as documented

---

## Phase 7: Convergence

- [X] T026 Add a test asserting `generate_thesis` logs token usage (`prompt_tokens`, `completion_tokens`) and `latency_ms` on a successful call, in `tests/unit/research/test_generator.py` per Constitution: Quality, Observability & Development Workflow (partial)
- [X] T027 Add a test asserting `generate_thesis` succeeds with an `InvestmentCase` that has zero `Evidence` entries, producing an `InvestmentThesis` with an empty `supporting_evidence` list, in `tests/unit/research/test_generator.py` per spec.md Edge Cases (missing)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: T001 → T002 → T003 in order (T002 needs the dependency declared by T001; T003 is independent of T001/T002 but grouped here as Setup)
- **Foundational (Phase 2)**: T004, T005, T006, T007 are `[P]` (independent files); T008 depends on T003-T006 (same file, `src/aic/research/__init__.py`) — BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational (Phase 2) completion
- **Polish (Phase 6)**: Depends on all three user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Depends only on Foundational — no dependency on US2/US3
- **User Story 2 (P2)**: Depends only on Foundational's `InvestmentThesis` reuse (from 002-domain-model, already existing) — genuinely independent of US1's `generator.py`/`openai_provider.py`; could be implemented fully in parallel with User Story 1
- **User Story 3 (P3)**: Depends on US1 (`FakeLLMProvider` from T013) and Foundational (`AppSettings` from T007) — not independent of US1's test fixtures

### Important: shared-file constraints

- `src/aic/research/__init__.py`: T003 → T008 → T012 → T018 must be applied in that order (same file)
- `pyproject.toml`: T001 must precede T002 (same file, sequential dependency)

None of the above pairs are `[P]` with each other, even where their owning stories are
otherwise independent.

### Parallel Opportunities

- T004, T005, T006, T007 (Foundational) can all run in parallel — independent files
- T009 (prompt.py) and T010 (openai_provider.py) can run in parallel with each other, and both in parallel with T013 (fakes.py) — independent files
- T015 and T016 (US1 tests) can run in parallel with each other once their respective implementation tasks (T009, T010) land
- **User Story 2 (T017-T019) can proceed entirely in parallel with User Story 1** once Foundational is done — `document.py` only needs the existing `InvestmentThesis`, not anything US1 builds
- T021, T022, T023, T024 (Polish) can all run in parallel — independent verification passes

---

## Parallel Example: Foundational Phase

```bash
# Launch the independent Foundational file-creation tasks together:
Task: "Create src/aic/research/context.py with ResearchContext"
Task: "Create src/aic/research/draft.py with ThesisDraft"
Task: "Create src/aic/research/provider.py with LLMCompletion and LLMProvider"
Task: "Add openai_api_key field to src/aic/settings.py"
```

## Parallel Example: User Story 1 and User Story 2 together

```bash
# Once Foundational is done, these two stories touch disjoint files:
Task: "Implement generate_thesis in src/aic/research/generator.py (US1)"
Task: "Implement render_thesis_document in src/aic/research/document.py (US2)"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: `uv run pytest tests/unit/research -v` passes for generation, prompt, and adapter tests, with zero real OpenAI calls
5. This alone delivers the core product hypothesis — a working, evidence-traceable, provider-swappable thesis generator

### Incremental Delivery

1. Setup + Foundational → `ResearchContext`/`ThesisDraft`/`LLMProvider`/settings ready
2. Add User Story 1 → validate independently → working thesis generator (MVP)
3. Add User Story 2 → validate independently → deterministic document rendering
4. Add User Story 3 → validate independently → zero-credential test-suite property explicitly checked
5. Polish → full quickstart.md pass + scope/dependency verification

---

## Notes

- `[P]` tasks touch different files with no dependency between them
- `[Story]` label maps a task to its user story for traceability; Setup/Foundational/Polish tasks carry no story label
- `src/aic/research/__init__.py` and `pyproject.toml` are shared files edited incrementally — respect the sequential order noted above
- This feature adds exactly one new third-party dependency (`openai`, explicitly sanctioned by the constitution) and modifies exactly one existing file (`src/aic/settings.py`) — everything else is new, additive code under `src/aic/research/`
- Commit after each task or logical group
- Stop at any checkpoint to validate a story independently
