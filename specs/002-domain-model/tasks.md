---

description: "Task list template for feature implementation"
---

# Tasks: Investment Committee Domain Model

**Input**: Design documents from `/specs/002-domain-model/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/domain-package-interface.md, quickstart.md

**Tests**: Not explicitly requested as TDD, but the spec explicitly lists required test categories per model (valid construction, required-field validation, optional fields, currency handling, evidence classification, serialization round-trip, invalid values) — these are included as normal implementation deliverables alongside each model, not as write-first TDD tasks.

**Organization**: Tasks are grouped by user story (spec.md) to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

Single project, `src`-layout (per plan.md, unchanged from 001-repository-bootstrap):
`src/aic/domain/`, `tests/unit/domain/`.

## Phase 1: Setup

**Purpose**: Establish the `aic.domain` package shell.

- [X] T001 Create `src/aic/domain/__init__.py` as an initially empty module, establishing the `aic.domain` package (contents populated incrementally by later tasks; FR-019)

**Checkpoint**: Package shell exists. All later `src/aic/domain/__init__.py` edits (T005, T008, T016, T023) are sequential against each other from here on, since they share one file.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared building blocks every user story depends on — the closed enumerations, ISO 4217 currency validation, and the `Money` value object.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T002 [P] Create `src/aic/domain/enums.py` with `EvidenceType` (`StrEnum`: FACT, CALCULATION, ASSUMPTION, INTERPRETATION, OPINION) and `Recommendation` (`StrEnum`: BUY, WATCH, AVOID) (FR-003; spec Assumptions; data-model.md Enumerations; research.md "Enum representation")
- [X] T003 [P] Create `src/aic/domain/currency.py` with the complete ISO 4217 alphabetic currency code set as a `frozenset[str]` constant (sourced from the official ISO 4217 list, with a comment on how to regenerate it) and a `CurrencyCode` validated type/validator that rejects any value outside that set (research.md "ISO 4217 currency validation against the real, complete code set")
- [X] T004 Create `src/aic/domain/money.py` with the `Money` value object (`amount: Decimal`, `currency: CurrencyCode`), no arithmetic or conversion methods (depends on T003; FR-017; data-model.md Money; research.md "`Money` value object for monetary fields")
- [X] T005 Add `EvidenceType`, `Recommendation`, `CurrencyCode`, and `Money` exports to `src/aic/domain/__init__.py` (depends on T001, T002, T003, T004; same file)

**Checkpoint**: Foundation ready — user story implementation can now begin.

---

## Phase 3: User Story 1 - Represent a Company's Sourced Financial Data Without Ambiguity (Priority: P1) 🎯 MVP

**Goal**: A developer can construct a `Company` and a `FinancialSnapshot` with valid data (round-tripping losslessly), and invalid/ambiguous data (missing currency, mixed currencies, missing required fields) is rejected explicitly.

**Independent Test**: Construct a `Company` and a `FinancialSnapshot` with valid data — both validate and round-trip via `model_dump()`/`model_validate()`. Construct a `FinancialSnapshot` with a monetary metric but no valid currency — construction fails explicitly.

### Implementation for User Story 1

- [X] T006 [P] [US1] Create `src/aic/domain/company.py` with the `Company` model — `company_id: UUID` (required, caller-supplied), `ticker`, `name`, `exchange`, `country`, `sector`, `industry` all required `str` (FR-001, FR-010; data-model.md Company)
- [X] T007 [US1] Create `src/aic/domain/financial_snapshot.py` with the `FinancialSnapshot` model — `as_of: date`; `revenue`, `operating_income`, `net_income`, `free_cash_flow`, `cash`, `debt` each `Money | None`; `shares_outstanding: Decimal | None`; a model-level validator rejecting a mix of currencies across populated `Money` metrics (depends on T004; FR-004, FR-013; data-model.md FinancialSnapshot)
- [X] T008 [US1] Add `Company` and `FinancialSnapshot` exports to `src/aic/domain/__init__.py` (depends on T005, T006, T007; same file)
- [X] T009 [P] [US1] Create `tests/unit/domain/test_company.py` covering valid construction and required-field validation (FR-001; spec US1 acceptance scenario 1)
- [X] T010 [P] [US1] Create `tests/unit/domain/test_financial_snapshot.py` covering valid construction with partial optional metrics (absent metric is `None`, not `0`), rejection of a monetary value with an invalid/missing currency, rejection of mixed currencies across metrics, and lossless `model_dump()`/`model_validate()` round-trip (FR-004, FR-013, FR-016; spec US1 acceptance scenarios 2-4)
- [X] T011 [P] [US1] Create `tests/unit/domain/test_currency.py` covering acceptance of real ISO 4217 codes and rejection of an invalid code (SC-002; spec Edge Cases)
- [X] T012 [P] [US1] Create `tests/unit/domain/test_money.py` covering valid `Money` construction, rejection without a valid currency, and round-trip serialization (research.md "`Money` value object")

**Checkpoint**: User Story 1 is fully functional and independently testable.

---

## Phase 4: User Story 2 - Assemble Sourced Evidence Into an Investment Thesis and Case (Priority: P2)

**Goal**: A developer can construct classified `Evidence`, an `InvestmentThesis` referencing it, and an `InvestmentCase` connecting a `Company`, one or more `FinancialSnapshot` records, the thesis, and evidence — all with a stable identifier and analysis timestamp.

**Independent Test**: Construct `Evidence` records covering each evidence type (without a URL), an `InvestmentThesis`, and an `InvestmentCase` — the case exposes a stable identifier, an analysis timestamp, and every connected part, and round-trips losslessly.

### Implementation for User Story 2

- [X] T013 [P] [US2] Create `src/aic/domain/evidence.py` with the `Evidence` model — `evidence_id: UUID` (required, caller-supplied), `source`, `title`, `excerpt`, `retrieved_date` required; `reference`, `publication_date` optional; `evidence_type: EvidenceType` (depends on T002, T005; FR-002, FR-003, FR-010; data-model.md Evidence)
- [X] T014 [US2] Create `src/aic/domain/thesis.py` with the `InvestmentThesis` model — `summary`, `supporting_evidence: list[Evidence]`, `key_assumptions`, `key_risks`, `invalidation_conditions` (depends on T013; FR-005; data-model.md InvestmentThesis)
- [X] T015 [US2] Create `src/aic/domain/investment_case.py` with the `InvestmentCase` model — `case_id: UUID` (required, caller-supplied), `analysis_timestamp: datetime` (UTC, auto via `default_factory`), `company: Company`, `financial_snapshots: list[FinancialSnapshot]` (min length 1), `thesis: InvestmentThesis`, `evidence: list[Evidence]` (depends on T006, T007, T014; FR-006, FR-010; data-model.md InvestmentCase)
- [X] T016 [US2] Add `Evidence`, `InvestmentThesis`, `InvestmentCase` exports to `src/aic/domain/__init__.py` (depends on T008, T013, T014, T015; same file)
- [X] T017 [P] [US2] Create `tests/unit/domain/test_evidence.py` covering valid construction without a URL, correct evidence-type classification, rejection of an out-of-set evidence type, and round-trip serialization (FR-002, FR-003; spec US2 acceptance scenarios 1-2)
- [X] T018 [P] [US2] Create `tests/unit/domain/test_thesis.py` covering valid construction and round-trip serialization (FR-005; spec US2 acceptance scenario 3)
- [X] T019 [P] [US2] Create `tests/unit/domain/test_investment_case.py` covering assembly from `Company`/`FinancialSnapshot`(s)/`InvestmentThesis`/`Evidence`, the minimum-one-snapshot rule, stable identifier/timestamp exposure, and round-trip serialization (FR-006; spec US2 acceptance scenario 4)

**Checkpoint**: User Stories 1 AND 2 both work independently.

---

## Phase 5: User Story 3 - Define Reusable Contracts for Future Assessment, Valuation, and Decision (Priority: P3)

**Goal**: A developer can construct a role-agnostic `AnalysisAssessment`, a shape-only `ValuationResult`, and a shape-only `CommitteeDecision` (optionally without a valuation yet), all independently valid and round-trip-safe.

**Independent Test**: Construct an `AnalysisAssessment` with no Bull/Bear label anywhere in its type or fields, a `ValuationResult` with a `Money` estimated value, and a `CommitteeDecision` without a `valuation_reference` — all three validate and round-trip losslessly.

### Implementation for User Story 3

- [ ] T020 [P] [US3] Create `src/aic/domain/assessment.py` with the `AnalysisAssessment` model — `assessment_id: UUID` (required, caller-supplied), `conclusion`, `arguments`, `supporting_evidence: list[UUID]`, `assumptions`, `risks`, `confidence: float` (0.0-1.0 bounded); no field or the type name encodes "Bull"/"Bear" (FR-007, FR-010; data-model.md AnalysisAssessment)
- [ ] T021 [P] [US3] Create `src/aic/domain/valuation.py` with the `ValuationResult` model — `valuation_id: UUID` (required, caller-supplied), `method`, `valuation_date`, `estimated_value: Money`, `assumption_evidence_refs: list[UUID]`, `confidence: float` (0.0-1.0 bounded) (depends on T004; FR-008, FR-010; data-model.md ValuationResult)
- [ ] T022 [US3] Create `src/aic/domain/decision.py` with the `CommitteeDecision` model — `decision_id: UUID` (required, caller-supplied), `decision_timestamp: datetime` (UTC, auto via `default_factory`), `recommendation: Recommendation`, `rationale`, `referenced_evidence: list[UUID]`, `referenced_thesis: InvestmentThesis | None`, `valuation_reference: UUID | None`, `dissent: list[str]` (depends on T002, T005, T014; FR-009, FR-010; data-model.md CommitteeDecision)
- [ ] T023 [US3] Add `AnalysisAssessment`, `ValuationResult`, `CommitteeDecision` exports to `src/aic/domain/__init__.py` (depends on T016, T020, T021, T022; same file)
- [ ] T024 [P] [US3] Create `tests/unit/domain/test_assessment.py` covering valid construction, absence of any Bull/Bear naming in the type or fields, and round-trip serialization (FR-007; spec US3 acceptance scenario 1)
- [ ] T025 [P] [US3] Create `tests/unit/domain/test_valuation.py` covering valid construction using `Money`, absence of any calculation behavior, and round-trip serialization (FR-008; spec US3 acceptance scenario 2)
- [ ] T026 [P] [US3] Create `tests/unit/domain/test_decision.py` covering valid construction with and without a `valuation_reference`, rejection of an invalid `recommendation` value, and round-trip serialization (FR-009; spec US3 acceptance scenarios 3-4)

**Checkpoint**: All three user stories are independently functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Whole-feature validation against the spec's Success Criteria.

- [ ] T027 [P] Run `uv run pytest tests/unit/domain -v` and confirm every test passes — validates SC-001, SC-003, SC-004, SC-005
- [ ] T028 [P] Run `uv run ruff check .` and `uv run mypy src` and resolve any reported issues
- [ ] T029 [P] Verify `aic.domain` can be imported and every model constructed/validated/serialized with zero network calls, zero environment-variable reads, and zero dependency on OpenAI/LangChain/LangGraph/AWS/boto3/market-data packages — inspect every `src/aic/domain/*.py` import (FR-018, SC-006)
- [ ] T030 [P] Verify no DCF, valuation-calculation, agent-role, committee-orchestration, or persistence logic exists anywhere in `src/aic/domain/` (FR-017, SC-007)
- [ ] T031 Run the full `quickstart.md` validation sequence end-to-end and confirm every snippet behaves exactly as documented

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — T001 can start immediately
- **Foundational (Phase 2)**: T002 and T003 are `[P]` (independent new files); T004 depends on T003 (imports `CurrencyCode`); T005 depends on T001-T004 (same file, `src/aic/domain/__init__.py`) — BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational (Phase 2) completion
- **Polish (Phase 6)**: Depends on all three user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Depends only on Foundational (`Money`/`CurrencyCode` from T003-T004) — no dependency on US2/US3
- **User Story 2 (P2)**: Depends on Foundational (`EvidenceType` from T002) and on US1's `Company`/`FinancialSnapshot` (T006-T007), since `InvestmentCase` connects them — not independent of US1's models, but independently testable once they exist
- **User Story 3 (P3)**: Depends on Foundational (`Recommendation` from T002, `Money` from T004) and on US2's `InvestmentThesis` (T014), since `CommitteeDecision.referenced_thesis` references it — not independent of US2's models, but independently testable once they exist

### Important: shared-file constraint on `src/aic/domain/__init__.py`

Tasks T001 → T005 → T008 → T016 → T023 all edit the **same file**
(`src/aic/domain/__init__.py`) and therefore MUST be applied in that sequential order
regardless of which phase "owns" them — none of these five are `[P]` with each other.

### Parallel Opportunities

- T002 and T003 (Foundational) can run in parallel — independent new files
- T006 (US1) can run in parallel with Foundational-phase file creation once T001-T005 land, and independently of T007
- T009, T010, T011, T012 (US1 tests) can all run in parallel — different files
- T013 (US2) can run in parallel with other US2 setup once its dependencies (T002, T005) land
- T017, T018, T019 (US2 tests) can all run in parallel — different files
- T020 and T021 (US3) can run in parallel with each other — different files, independent of one another
- T024, T025, T026 (US3 tests) can all run in parallel — different files
- T027, T028, T029, T030 (Polish) can all run in parallel — independent verification passes

---

## Parallel Example: Foundational Phase

```bash
# Launch the independent Foundational file-creation tasks together:
Task: "Create src/aic/domain/enums.py with EvidenceType and Recommendation"
Task: "Create src/aic/domain/currency.py with the complete ISO 4217 code set"
```

## Parallel Example: User Story 1 tests

```bash
# Launch all US1 test files together:
Task: "Create tests/unit/domain/test_company.py"
Task: "Create tests/unit/domain/test_financial_snapshot.py"
Task: "Create tests/unit/domain/test_currency.py"
Task: "Create tests/unit/domain/test_money.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: `uv run pytest tests/unit/domain -v` passes for `Company`, `FinancialSnapshot`, `Money`, and currency tests
5. This alone gives every later feature a validated `Company`/`FinancialSnapshot`/`Money` contract to build on

### Incremental Delivery

1. Setup + Foundational → enums, currency validation, and `Money` ready
2. Add User Story 1 → validate independently → `Company`/`FinancialSnapshot` contract ready (MVP)
3. Add User Story 2 → validate independently → `Evidence`/`InvestmentThesis`/`InvestmentCase` contract ready
4. Add User Story 3 → validate independently → `AnalysisAssessment`/`ValuationResult`/`CommitteeDecision` contracts ready
5. Polish → full quickstart.md pass + scope/dependency verification

---

## Notes

- `[P]` tasks touch different files with no dependency between them
- `[Story]` label maps a task to its user story for traceability; Setup/Foundational/Polish tasks carry no story label
- `src/aic/domain/__init__.py` is a shared file edited incrementally across phases — respect the sequential order noted above even when working stories in parallel
- Every identifier field (`company_id`, `evidence_id`, `case_id`, `assessment_id`, `valuation_id`, `decision_id`) is a **required, caller-supplied** `UUID` — no model auto-generates one (research.md "Identifier type — caller-supplied, not auto-generated")
- Every monetary field uses the shared `Money` value object, never a bare `Decimal` beside a separate currency field (research.md "`Money` value object for monetary fields")
- This feature introduces no domain logic beyond typed data and validation — per plan.md, `src/aic/domain/` contains no calculation, agent, orchestration, or persistence code
- Commit after each task or logical group
- Stop at any checkpoint to validate a story independently

---

## Phase 7: Convergence

- [X] T032 [P] [US1] Add a `model_dump()`/`model_validate()` round-trip serialization test for `Company` in `tests/unit/domain/test_company.py` per SC-004 (partial)

---

## Phase 8: Convergence

- [X] T033 [P] [US2] Add a parametrized required-field-validation test to `tests/unit/domain/test_evidence.py` (missing `evidence_id`, `source`, `title`, `excerpt`, or `retrieved_date` each raise `ValidationError`) per SC-001 (partial)

---

## Phase 9: Convergence

- [X] T034 [P] [US2] Add a parametrized required-field-validation test to `tests/unit/domain/test_investment_case.py` (missing `case_id`, `company`, or `thesis` each raise `ValidationError`) per SC-001 (partial)
- [X] T035 [P] [US2] Add a required-field-validation test to `tests/unit/domain/test_thesis.py` (missing `summary` raises `ValidationError`) per SC-001 (partial)
