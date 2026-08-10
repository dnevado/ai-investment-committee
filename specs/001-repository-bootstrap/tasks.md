---

description: "Task list template for feature implementation"
---

# Tasks: Repository Bootstrap

**Input**: Design documents from `/specs/001-repository-bootstrap/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/package-interface.md, quickstart.md

**Tests**: Not explicitly requested as TDD in the spec. The one test required by the spec (FR-008 smoke test) is included as a normal implementation deliverable, not a write-first TDD task.

**Organization**: Tasks are grouped by user story (spec.md) to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

Single project, `src`-layout (per plan.md): `src/aic/`, `tests/unit/`, config and docs at repository root.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Repository scaffolding — directories and root config files that every later task builds on.

- [X] T001 [P] Create `data/.gitkeep` to establish the (otherwise empty) `data/` directory (FR-011)
- [X] T002 [P] Create `outputs/.gitkeep` to establish the (otherwise empty) `outputs/` directory (FR-011)
- [X] T003 [P] Create `.gitignore` at repository root excluding `.venv/`, `__pycache__/`, `*.pyc`, `.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/`, `.env`, `dist/`, `build/`, `*.egg-info/`, and the generated contents of `data/` and `outputs/` (tracking `.gitkeep` via an explicit exception) (FR-012; research.md "`.gitignore` scope")
- [X] T004 [P] Create `pyproject.toml` at repository root with `[project]` metadata (`name = "aic"`, `version`, `requires-python = ">=3.12"`), `[build-system]` using `hatchling`, and `[tool.hatch.build.targets.wheel] packages = ["src/aic"]` for the src-layout (FR-001, FR-002, FR-013; research.md "Build backend / project metadata")

**Checkpoint**: Root scaffolding exists. All later `pyproject.toml` edits (T006, T012, T013, T017) are sequential against each other from here on, since they share one file.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The package shell and dev-tooling declaration every user story needs before its own work can start.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 [P] Create `src/aic/__init__.py` exposing `__version__` as a non-empty string (the base `import aic` contract; FR-002, contracts/package-interface.md)
- [X] T006 Add a `[dependency-groups]` `dev = [...]` entry (pytest, ruff, mypy) to `pyproject.toml` (depends on T004; FR-003, FR-004, FR-005; research.md "Dependency grouping")

**Checkpoint**: Foundation ready — user story implementation can now begin.

---

## Phase 3: User Story 1 - Set Up a Working Local Environment (Priority: P1) 🎯 MVP

**Goal**: A developer can go from a clean checkout to installed dependencies, a working `import aic`, and a passing test suite, using only the README.

**Independent Test**: On a clean checkout, run `uv venv`, `uv sync`, `uv run pytest` — the smoke test passes.

### Implementation for User Story 1

- [X] T007 [P] [US1] Create `tests/unit/test_smoke.py` asserting `import aic` succeeds and `aic.__version__` is a non-empty string (FR-008, contracts/package-interface.md)
- [X] T008 [US1] Run `uv venv` then `uv sync` to create the local virtual environment and install dependencies declared in `pyproject.toml` (depends on T004, T006)
- [X] T009 [US1] Run `uv run pytest` and confirm the smoke test passes (depends on T005, T007, T008) — validates SC-002, SC-005
- [X] T010 [P] [US1] Write the README.md "Prerequisites" and "Setup" sections documenting Python 3.12+, `uv`, and the `uv venv` / `uv sync` workflow for Windows PowerShell (FR-009, FR-015)
- [X] T011 [US1] Add the README.md "Running Tests" section documenting `uv run pytest` (depends on T010, same file) (FR-009)

**Checkpoint**: User Story 1 is fully functional and independently testable — clean checkout → `uv venv` → `uv sync` → `uv run pytest` passes.

---

## Phase 4: User Story 2 - Run Quality Checks Before Committing (Priority: P2)

**Goal**: A developer can run the documented lint and type-check commands locally and get a clean, zero-issue result.

**Independent Test**: On a configured environment, run `uv run ruff check .` and `uv run mypy src` — both report zero issues.

### Implementation for User Story 2

- [X] T012 [US2] Add `[tool.ruff]` configuration to `pyproject.toml` (target Python 3.12, `src = ["src", "tests"]`) (depends on T006, same file) (FR-004)
- [X] T013 [US2] Add `[tool.mypy]` configuration to `pyproject.toml` (`python_version = "3.12"`, targeting the `src` package) (depends on T012, same file) (FR-005)
- [X] T014 [US2] Run `uv run ruff check .` against the repository and resolve any reported issues (depends on T007, T009, T012) — validates SC-003
- [X] T015 [US2] Run `uv run mypy src` against the repository and resolve any reported issues (depends on T005, T013) — validates SC-004
- [X] T016 [US2] Add the README.md "Quality Checks" section documenting `uv run ruff check .` and `uv run mypy src` (depends on T011, same file) (FR-009)

**Checkpoint**: User Stories 1 AND 2 both work independently.

---

## Phase 5: User Story 3 - Configure the Application via Environment Variables (Priority: P3)

**Goal**: A developer can see every supported environment variable in `.env.example` and load a typed, validated settings object with no real secrets involved.

**Independent Test**: Copy `.env.example` to `.env`, then load `AppSettings` via `get_settings()` — it succeeds and reflects the (non-secret) values.

### Implementation for User Story 3

- [X] T017 [US3] Add `pydantic` and `pydantic-settings` to `[project.dependencies]` in `pyproject.toml` (depends on T013, same file) (FR-006)
- [X] T018 [P] [US3] Create `src/aic/settings.py` with an `AppSettings(BaseSettings)` class (`environment: str = "local"`, `model_config` set to read `env_file=".env"` with `env_prefix="AIC_"`) and a cached `get_settings()` accessor (depends on T005, T017; data-model.md "AppSettings", contracts/package-interface.md "Settings contract") (FR-006)
- [X] T019 [P] [US3] Create `.env.example` at repository root documenting `AIC_ENV` with a placeholder (non-real) value and an explanatory comment (FR-007)
- [X] T020 [US3] Run `uv sync` to install the newly added runtime dependencies (depends on T017)
- [X] T021 [US3] Run `uv run python -c "from aic.settings import get_settings; print(get_settings())"` and confirm it succeeds with no `.env` file present, then repeat after copying `.env.example` to `.env` (depends on T018, T019, T020) — validates User Story 3 acceptance scenarios
- [X] T022 [US3] Add the README.md "Configuration" section documenting `.env.example`, copying it to `.env`, and how `AppSettings` / `get_settings()` load configuration (depends on T016, same file) (FR-007, FR-009)

**Checkpoint**: All three user stories are independently functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Whole-feature validation against the spec's Success Criteria.

- [X] T023 [P] Run the full `quickstart.md` validation sequence end-to-end on a clean checkout (`uv venv`, `uv sync`, `uv run pytest`, `uv run ruff check .`, `uv run mypy src`) and confirm every command exits `0` — validates SC-001, SC-002, SC-003, SC-004, SC-005, SC-008
- [X] T024 [P] Verify no real secrets or credentials exist anywhere in the repository (inspect `.env.example`, `pyproject.toml`, `README.md`; confirm `.env` is git-ignored and untracked) — validates SC-006, FR-010
- [X] T025 [P] Verify no investment-domain, LLM, agent, RAG, AWS, cloud-deployment, or other out-of-scope implementation was introduced by this feature — validates SC-007
- [X] T026 Final README.md consistency pass: confirm Prerequisites → Setup → Running Tests → Quality Checks → Configuration read as one coherent local-dev guide (depends on T022, same file) (FR-009)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — T001–T004 can start immediately (all `[P]`, different files)
- **Foundational (Phase 2)**: T005 depends on nothing (new file); T006 depends on T004 (same file, `pyproject.toml`) — BLOCKS all user stories
- **User Stories (Phase 3–5)**: All depend on Foundational (Phase 2) completion
- **Polish (Phase 6)**: Depends on all three user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Depends only on Foundational — no dependency on US2/US3
- **User Story 2 (P2)**: Depends only on Foundational — no dependency on US1/US3 in principle, but T012/T013 share `pyproject.toml` with T006 (Foundational) and must come after it
- **User Story 3 (P3)**: Depends only on Foundational — no dependency on US1/US2 in principle, but T017 shares `pyproject.toml` with T012/T013 (US2) and must come after them

### Important: shared-file constraint on `pyproject.toml`

Although the three user stories are logically independent, tasks T004 → T006 → T012 → T013 → T017 all edit the **same file** (`pyproject.toml`) and therefore MUST be applied in that sequential order regardless of which story "owns" them — none of these five are `[P]` with each other, even though their stories are otherwise parallelizable. The same applies to `README.md`: T010 → T011 → T016 → T022 → T026 are sequential edits to one file.

### Parallel Opportunities

- T001, T002, T003, T004 (Setup) can all run in parallel — four independent files
- T005 (Foundational) can run in parallel with T001–T004 — independent of the root config files
- T007 and T010 (US1) can run in parallel with each other — different files (test file vs. README)
- T018 and T019 (US3) can run in parallel with each other — different files (`settings.py` vs. `.env.example`)
- T023, T024, T025 (Polish) can all run in parallel — read-only verification passes over different concerns

---

## Parallel Example: Setup Phase

```bash
# Launch all Setup tasks together:
Task: "Create data/.gitkeep"
Task: "Create outputs/.gitkeep"
Task: "Create .gitignore at repository root"
Task: "Create pyproject.toml with project metadata and hatchling build-system"
```

## Parallel Example: User Story 3

```bash
# Launch the independent US3 file-creation tasks together:
Task: "Create src/aic/settings.py with AppSettings and get_settings()"
Task: "Create .env.example documenting AIC_ENV"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: `uv venv`, `uv sync`, `uv run pytest` all succeed on a clean checkout
5. This alone satisfies the feature's foundational purpose — every later AIC iteration can build on it

### Incremental Delivery

1. Setup + Foundational → package shell and dev-tooling declaration ready
2. Add User Story 1 → validate independently → working local dev environment (MVP)
3. Add User Story 2 → validate independently → lint/type-check baseline enforced
4. Add User Story 3 → validate independently → typed, env-var-driven configuration in place
5. Polish → full quickstart.md pass + scope/secrets verification

---

## Notes

- `[P]` tasks touch different files with no dependency between them
- `[Story]` label maps a task to its user story for traceability; Setup/Foundational/Polish tasks carry no story label
- `pyproject.toml` and `README.md` are shared files edited incrementally across phases — respect the sequential order noted above even when working stories in parallel
- This feature introduces no domain, agent, or LLM code — per plan.md, the only `src/` files produced are `src/aic/__init__.py` and `src/aic/settings.py`
- Commit after each task or logical group
- Stop at any checkpoint to validate a story independently

---

## Phase 7: Convergence

- [X] T027 Add `[tool.pytest.ini_options]` configuration to `pyproject.toml` (e.g. `testpaths = ["tests"]`) per research.md "Test, lint, and type-check configuration location" (partial)
