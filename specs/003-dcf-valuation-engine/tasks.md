---

description: "Task list template for feature implementation"
---

# Tasks: Deterministic DCF Valuation Engine

**Input**: Design documents from `/specs/003-dcf-valuation-engine/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/dcf-engine-interface.md, quickstart.md

**Tests**: Not explicitly requested as TDD, but the spec requires a canonical Reference Case and explicit rejection behavior for every validation rule — these are included as normal implementation deliverables per story, not write-first TDD tasks.

**Organization**: Tasks are grouped by user story (spec.md) to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

Single project, `src`-layout (per plan.md): `src/aic/dcf/`, `tests/unit/dcf/`. Depends on
the existing `src/aic/domain/` package (`Money`, `ValuationResult`) from 002-domain-model,
unmodified by this feature.

## Phase 1: Setup

**Purpose**: Establish the `aic.dcf` package shell.

- [X] T001 Create `src/aic/dcf/__init__.py` as an initially empty module, establishing the `aic.dcf` package (contents populated incrementally by later tasks)

**Checkpoint**: Package shell exists. All later `src/aic/dcf/__init__.py` edits (T004, T007) are sequential against each other from here on, since they share one file.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The input/output data models every user story depends on.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T002 [P] Create `src/aic/dcf/assumptions.py` with `ForecastYear` (`revenue`, `depreciation_and_amortization`, `capital_expenditure`, `change_in_net_working_capital`, all `Money`) and `DCFAssumptions` (`forecast: list[ForecastYear]` with `min_length=1`, `operating_margin`, `tax_rate`, `wacc`, `terminal_growth_rate` as `Decimal`, `cash`/`debt` as `Money`, `shares_outstanding` as `Decimal`) — structural/required-field shape only, no cross-field business-rule validators yet (FR-001–FR-004, FR-016 (via `min_length=1`), FR-018; data-model.md ForecastYear/DCFAssumptions)
- [X] T003 [P] Create `src/aic/dcf/result.py` with `YearResult` (`year: int`, `fcff: Money`, `pv_fcff: Money`) and `DCFResult` (`per_year: list[YearResult]`, `terminal_value`, `pv_terminal_value`, `enterprise_value`, `equity_value`, `implied_value_per_share`, all `Money`) (data-model.md YearResult/DCFResult)
- [X] T004 Add `ForecastYear`, `DCFAssumptions`, `YearResult`, `DCFResult` exports to `src/aic/dcf/__init__.py` (depends on T001, T002, T003; same file)

**Checkpoint**: Foundation ready — user story implementation can now begin.

---

## Phase 3: User Story 1 - Compute Enterprise Value, Equity Value, and Implied Value Per Share (Priority: P1) 🎯 MVP

**Goal**: A developer can turn a complete, valid `DCFAssumptions` into a `DCFResult` (and, via an adapter, a `ValuationResult`) — deterministically, with every output value carrying the correct currency.

**Independent Test**: Supply a complete, valid set of assumptions and confirm `compute_dcf` returns per-year FCFF/PV(FCFF), Terminal Value, PV(Terminal Value), Enterprise Value, Equity Value, and Implied Value Per Share consistent with the stated formulas; confirm two runs on the same input produce identical output.

### Implementation for User Story 1

- [X] T005 [US1] Create `src/aic/dcf/engine.py` with `compute_dcf(assumptions: DCFAssumptions) -> DCFResult` implementing FR-005–FR-013 (EBIT, NOPAT, FCFF, PV(FCFF) per year, Terminal Value, PV(Terminal Value), Enterprise Value, Equity Value, Implied Value Per Share) using exact `Decimal` arithmetic throughout, rounding only the values placed into the returned `DCFResult` to 2 decimal places with round-half-up (FR-021, FR-022), with a final `is_finite()` check on every computed value before returning (FR-019) (depends on T002, T003, T004; data-model.md "Computation"; research.md "`Decimal` arithmetic", "Rounding policy implementation")
- [X] T006 [US1] Add `to_valuation_result(result: DCFResult, *, valuation_id, valuation_date, confidence, method="DCF (FCFF)", assumption_evidence_refs=[]) -> ValuationResult` to `src/aic/dcf/engine.py`, mapping `DCFResult.implied_value_per_share` into `ValuationResult.estimated_value` losslessly (depends on T005, same file; FR-026; research.md "`ValuationResult` compatibility via an explicit adapter function")
- [X] T007 [US1] Add `compute_dcf` and `to_valuation_result` exports to `src/aic/dcf/__init__.py` (depends on T004, T005, T006; same file)
- [X] T008 [US1] Create `tests/unit/dcf/test_engine.py` with a valid-computation test (simple hand-verifiable numbers, asserting each formula step — EBIT/NOPAT/FCFF per year, Enterprise Value = sum(PV(FCFF)) + PV(Terminal Value), Equity Value = Enterprise Value + Cash − Debt, Implied Value Per Share = Equity Value ÷ Shares Outstanding), a determinism test (two `compute_dcf` calls on the same input produce an equal `DCFResult`), and an output-currency-propagation test (every `Money` field in the result carries the input currency) (depends on T005; FR-005–FR-013, FR-021, FR-022, FR-025; spec US1 acceptance scenarios 1-3)
- [X] T009 [US1] Add a `to_valuation_result` test to `tests/unit/dcf/test_engine.py` asserting `ValuationResult.estimated_value` matches `DCFResult.implied_value_per_share` exactly (depends on T006, T008, same file; FR-026)

**Checkpoint**: User Story 1 is fully functional and independently testable — this alone is the MVP.

---

## Phase 4: User Story 2 - Reject Invalid or Economically Incoherent Assumptions Explicitly (Priority: P2)

**Goal**: `DCFAssumptions` construction fails explicitly — before any calculation runs — for every rule in FR-014–FR-020.

**Independent Test**: Supply assumption sets that each violate exactly one validation rule and confirm each is rejected with an explicit error and no numeric result is produced.

### Implementation for User Story 2

- [X] T010 [US2] Add a model validator to `src/aic/dcf/assumptions.py` `DCFAssumptions` rejecting `wacc` not strictly greater than `terminal_growth_rate` (depends on T002, same file; FR-014)
- [X] T011 [US2] Add a validator to `src/aic/dcf/assumptions.py` rejecting `wacc` that is not strictly positive (depends on T010, same file; FR-015)
- [X] T012 [US2] Add a validator to `src/aic/dcf/assumptions.py` rejecting `shares_outstanding` that is not strictly positive (depends on T011, same file; FR-017)
- [X] T013 [US2] Add a validator to `src/aic/dcf/assumptions.py` rejecting `tax_rate` outside `[0, 1]` (depends on T012, same file; spec Assumptions "Tax Rate bounds")
- [X] T014 [US2] Add a cross-field validator to `src/aic/dcf/assumptions.py` rejecting a `DCFAssumptions` whose `forecast` entries, `cash`, and `debt` do not all share one currency (depends on T013, same file; FR-020)
- [X] T015 [US2] Create `tests/unit/dcf/test_assumptions.py` covering: `wacc == terminal_growth_rate` rejected, `wacc <= 0` rejected, empty `forecast` rejected (via `min_length=1` from T002), `shares_outstanding <= 0` rejected, `tax_rate` outside `[0, 1]` rejected, each required field missing rejected (parametrized), and mismatched currency across `forecast`/`cash`/`debt` rejected (depends on T010, T011, T012, T013, T014; FR-014–FR-020; spec US2 acceptance scenarios 1-6)

**Checkpoint**: User Stories 1 AND 2 both work independently.

---

## Phase 5: User Story 3 - Verify Engine Correctness Against a Canonical Reference Case (Priority: P3)

**Goal**: The spec's documented Reference Case, run through the engine, reproduces every documented output value exactly.

**Independent Test**: Feed the Reference Case's documented inputs into `compute_dcf` and confirm every output field matches the documented expected value exactly.

### Implementation for User Story 3

- [X] T016 [US3] Add `test_reference_case` to `tests/unit/dcf/test_engine.py` using spec.md's exact Reference Case inputs, asserting every `DCFResult` field (per-year FCFF/PV(FCFF) for years 1-3, Terminal Value, PV(Terminal Value), Enterprise Value, Equity Value, Implied Value Per Share) matches the documented expected value exactly (depends on T005, T008, same file; FR-005–FR-013; spec US3 acceptance scenario 1; SC-001)

**Checkpoint**: All three user stories are independently functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Whole-feature validation against the spec's Success Criteria.

- [X] T017 [P] Run `uv run pytest tests/unit/dcf -v` and confirm every test passes — validates SC-001, SC-005
- [X] T018 [P] Run `uv run ruff check .` and `uv run mypy src` and resolve any reported issues
- [X] T019 [P] Verify `aic.dcf` performs zero network/file I/O and has zero dependency on OpenAI/LangChain/LangGraph/AWS/boto3/market-data packages — inspect every `src/aic/dcf/*.py` import (FR-023, FR-024, SC-007)
- [X] T020 [P] Verify no NaN/Infinity ever appears in a successful calculation's output, and no Monte Carlo, probabilistic, comparable-company, precedent-transaction, terminal-multiple, or FX-conversion logic exists anywhere in `src/aic/dcf/` (FR-019, FR-025, SC-006; spec out-of-scope list)
- [X] T021 Run the full `quickstart.md` validation sequence end-to-end and confirm every snippet behaves exactly as documented, including the Reference Case output `1906.40 1956.40 19.56`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — T001 can start immediately
- **Foundational (Phase 2)**: T002 and T003 are `[P]` (independent new files); T004 depends on T001-T003 (same file, `src/aic/dcf/__init__.py`) — BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational (Phase 2) completion
- **Polish (Phase 6)**: Depends on all three user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Depends only on Foundational — no dependency on US2/US3
- **User Story 2 (P2)**: Depends only on Foundational (`DCFAssumptions` from T002) — genuinely independent of US1's `engine.py`/`test_engine.py`; could be implemented in parallel with US1 by a different contributor
- **User Story 3 (P3)**: Depends on US1 (`compute_dcf` from T005, and `test_engine.py` from T008) — not independent of US1's concrete implementation, since it verifies that implementation's output

### Important: shared-file constraints

- `src/aic/dcf/__init__.py`: T001 → T004 → T007 must be applied in that order (same file)
- `src/aic/dcf/assumptions.py`: T002 → T010 → T011 → T012 → T013 → T014 must be applied in that order (same file)
- `src/aic/dcf/engine.py`: T005 → T006 must be applied in that order (same file)
- `tests/unit/dcf/test_engine.py`: T008 → T009 → T016 must be applied in that order (same file)

None of the above pairs are `[P]` with each other, even where their owning stories are
otherwise independent.

### Parallel Opportunities

- T002 and T003 (Foundational) can run in parallel — independent new files
- User Story 2 (T010-T015) can proceed in parallel with User Story 1 (T005-T009) once Foundational is done — they touch entirely disjoint files (`assumptions.py`/`test_assumptions.py` vs `engine.py`/`test_engine.py`)
- T017, T018, T019, T020 (Polish) can all run in parallel — independent verification passes

---

## Parallel Example: Foundational Phase

```bash
# Launch the independent Foundational file-creation tasks together:
Task: "Create src/aic/dcf/assumptions.py with ForecastYear and DCFAssumptions"
Task: "Create src/aic/dcf/result.py with YearResult and DCFResult"
```

## Parallel Example: User Story 1 and User Story 2 together

```bash
# Once Foundational is done, these two stories touch disjoint files:
Task: "Implement compute_dcf in src/aic/dcf/engine.py (US1)"
Task: "Add WACC/terminal-growth validator to src/aic/dcf/assumptions.py (US2)"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: `uv run pytest tests/unit/dcf -v` passes for the valid-computation, determinism, and `to_valuation_result` tests
5. This alone delivers the core product hypothesis — a working, deterministic DCF calculation

### Incremental Delivery

1. Setup + Foundational → `DCFAssumptions`/`DCFResult` shapes ready
2. Add User Story 1 → validate independently → working calculation engine (MVP)
3. Add User Story 2 → validate independently → explicit rejection of invalid/incoherent input
4. Add User Story 3 → validate independently → canonical Reference Case verified exactly
5. Polish → full quickstart.md pass + scope/dependency verification

---

## Notes

- `[P]` tasks touch different files with no dependency between them
- `[Story]` label maps a task to its user story for traceability; Setup/Foundational/Polish tasks carry no story label
- `src/aic/dcf/__init__.py`, `src/aic/dcf/assumptions.py`, `src/aic/dcf/engine.py`, and `tests/unit/dcf/test_engine.py` are each shared files edited incrementally — respect the sequential order noted above
- This feature introduces no new dependency, no I/O, no LLM call, and no persistence — per plan.md, `src/aic/dcf/` contains four files (`__init__.py`, `assumptions.py`, `result.py`, `engine.py`) and nothing else
- Commit after each task or logical group
- Stop at any checkpoint to validate a story independently

---

## Phase 7: Convergence

- [X] T022 [P] [US1] Add edge-case tests to `tests/unit/dcf/test_engine.py` for a forecast year with negative FCFF, a Debt large enough to produce a negative Equity Value/Implied Value Per Share, and a negative `terminal_growth_rate`, per spec.md Edge Cases (partial)
- [X] T023 [P] [US1] Add a direct unit test for `_round_money`'s `is_finite()` guard in `src/aic/dcf/engine.py`, asserting it raises for a non-finite `Decimal`, per SC-006 (partial)
