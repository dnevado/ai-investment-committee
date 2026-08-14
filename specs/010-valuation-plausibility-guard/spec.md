# Feature Specification: Valuation Plausibility Guard

**Feature Branch**: `010-valuation-plausibility-guard`

**Created**: 2026-08-14

**Status**: Draft

**Input**: User description: "Validate the complete investment-committee pipeline against a real public company dataset, using Amazon as the reference case, and ensure that the generated investment decision is financially interpretable, internally consistent, traceable to its inputs and assumptions, and does not silently accept economically implausible valuation outputs."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Reject an economically implausible valuation before it reaches research or committee (Priority: P1)

An analyst supplies DCF assumptions that, once computed, imply the company has no sustainable cash flow left in the terminal year (for example, forecast capital expenditure assumptions that persistently exceed after-tax operating profit). Today the DCF engine will silently compute and return a deeply negative enterprise value, and the pipeline will carry that nonsensical figure all the way through research, bull/bear analysis, committee adjudication, and the final memo as if it were a legitimate bearish valuation. The analyst needs the system to stop immediately and say clearly what is wrong, instead of producing a polished-looking report built on a broken number.

**Why this priority**: This is the core defect this feature exists to close. Without it, the system can produce a fully-formed, confident-sounding `CommitteeDecision` and memo that rests on a valuation that is not economically meaningful — the single most damaging failure mode for an investment research tool, because it looks trustworthy while being wrong.

**Independent Test**: Can be fully tested by computing a DCF with assumptions known to drive terminal-year free cash flow to zero or below (or otherwise drive enterprise value to zero or below), and confirming the system raises a clear, descriptive error before any research, bull/bear, or committee stage runs, rather than returning a `DCFResult`.

**Acceptance Scenarios**:

1. **Given** DCF assumptions whose terminal forecast year produces a non-positive free cash flow to the firm (FCFF), **When** the DCF is computed, **Then** the system raises an explicit error identifying that the terminal-year FCFF is non-positive and reports its value, and no `DCFResult` is returned.
2. **Given** DCF assumptions that produce a non-positive enterprise value even though the terminal-year FCFF is positive, **When** the DCF is computed, **Then** the system raises an explicit error identifying that the computed enterprise value is non-positive and reports its value, and no `DCFResult` is returned.
3. **Given** an end-to-end workflow run (research → thesis → bull/bear → DCF → committee → report) using assumptions that fail either check above, **When** the workflow is run, **Then** it fails at the DCF stage before any LLM provider call is made, and no thesis, assessment, decision, or report is produced.

---

### User Story 2 - Validate the full pipeline end-to-end against a real company's data (Priority: P2)

An analyst wants confidence that the complete pipeline — company and financial data, evidence, research, investment thesis, bull/bear assessments, DCF valuation, committee adjudication, and final memo — works correctly together on a real company, not just on synthetic test fixtures. Amazon is used as the reference case because it is a large, well-documented public company with abundant, easily verifiable public financial disclosures.

**Why this priority**: Synthetic unit-test fixtures can hide integration problems that only appear with real-scale, real-world figures (as happened here: a $150B+ enterprise-value swing was invisible in small round-number test fixtures). A real reference case is the practical way to catch this class of problem before it reaches an analyst relying on the tool for an actual company.

**Independent Test**: Can be fully tested by running the complete pipeline against a reference dataset built from Amazon's own reported financials and assumption set, and confirming it completes successfully end to end, producing a `CommitteeReport` with a strictly positive, internally consistent valuation.

**Acceptance Scenarios**:

1. **Given** a reference dataset of Amazon's actual reported financials (revenue, operating income, net income, free cash flow, cash, debt, shares outstanding) and a documented, internally consistent forecast/assumption set (growth, margin, tax rate, WACC, terminal growth), **When** the complete pipeline is run against it, **Then** it produces a `CommitteeReport` with a strictly positive enterprise value, equity value, and implied value per share.
2. **Given** the same reference dataset, **When** the pipeline completes, **Then** every material input figure (historical actuals and forecast assumptions) is traceable to a piece of supporting evidence that records its source and whether it is a reported fact, a derived calculation, or a forward-looking assumption.

---

### User Story 3 - Understand why a valuation was rejected (Priority: P3)

When the plausibility guard rejects a valuation, the analyst who supplied the assumptions needs enough information in the error itself to know what to change, without having to read the DCF engine's source code.

**Why this priority**: A guard that fails loudly but unhelpfully just trades one confusing failure mode for another. This priority is lower than P1/P2 because the guard already provides value by failing at all; making the failure diagnosable is a refinement of that value.

**Independent Test**: Can be fully tested by triggering each rejection condition from User Story 1 and confirming the resulting error message names the specific figure that failed the check (terminal-year FCFF or enterprise value) and its computed value.

**Acceptance Scenarios**:

1. **Given** a rejected DCF computation, **When** the analyst reads the raised error, **Then** the message states which check failed (terminal-year FCFF or enterprise value) and the offending computed amount, without requiring the analyst to inspect intermediate calculations manually.

---

### Edge Cases

- What happens when an interim (non-terminal) forecast year has a negative FCFF but the terminal year recovers to a positive FCFF? This MUST NOT be rejected — a temporary investment-heavy year followed by recovery is a legitimate, plausible scenario, and the discounted-cash-flow math already accounts for it correctly. Only the terminal year's FCFF (the basis for the perpetuity terminal value) and the final enterprise value are checked.
- What happens when terminal-year FCFF is exactly zero? This MUST be rejected under the same "non-positive" rule as a negative value — a going-concern perpetuity with zero sustaining cash flow forever is not a economically meaningful valuation.
- What happens when the DCF's own existing validation already rejects the assumptions for an unrelated reason (e.g., WACC not greater than terminal growth rate)? That existing, prior validation continues to apply first; this feature adds an additional, separate check on the *computed result*, not a replacement for existing input validation.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The DCF computation MUST reject, with an explicit and descriptive error, any result whose terminal forecast year produces a free cash flow to the firm (FCFF) that is not strictly positive, because the perpetuity-growth terminal value is only economically meaningful when computed from a sustaining, positive cash flow base.
- **FR-002**: The DCF computation MUST reject, with an explicit and descriptive error, any result whose computed enterprise value is not strictly positive, as a second, independent safety check beyond FR-001.
- **FR-003**: Each rejection error MUST identify which specific check failed (terminal-year FCFF or enterprise value) and MUST include the offending computed figure, so the cause is diagnosable from the error alone.
- **FR-004**: The rejection MUST occur at DCF computation time, before any research, thesis-generation, bull/bear, or committee-adjudication stage runs and before any LLM provider call is made, consistent with this project's existing fail-fast behavior for other invalid inputs.
- **FR-005**: The system MUST provide a reusable reference dataset built from Amazon's own reported FY2025 financials (revenue, operating income, net income, free cash flow, cash, debt, shares outstanding) and an internally consistent forecast/assumption set (per-year revenue, D&A, capex, change in net working capital, operating margin, tax rate, WACC, terminal growth) capable of exercising the complete pipeline end to end.
- **FR-006**: Every material figure in the reference dataset MUST carry evidence metadata recording its source and classifying it as a reported fact, a derived calculation, or a forward-looking assumption, consistent with this project's existing evidence-traceability requirements.
- **FR-007**: The reference dataset's assumption set MUST itself pass the checks in FR-001 and FR-002, so the reference case demonstrates a successful, plausible end-to-end run rather than only exercising the rejection path.
- **FR-008**: The pipeline MUST be automatically testable, without network access, for both the acceptance path (an internally consistent assumption set completes successfully) and the rejection path (an assumption set reproducing a persistently negative terminal-year FCFF is rejected), so this guard is protected by regression tests rather than only by manual scripts.
- **FR-009**: A `CommitteeDecision` and `CommitteeReport` MUST NOT be produced from a `DCFResult` that failed FR-001 or FR-002 — i.e., there MUST be no code path by which an implausible valuation reaches the committee or the final memo.

### Key Entities

- **DCFResult**: The existing deterministic output of the DCF engine (enterprise value, equity value, implied value per share, per-year cash flows). Gains a new invariant: it is never returned unless it passes the terminal-year FCFF and enterprise-value plausibility checks.
- **Reference Dataset (Amazon)**: A fixed, documented set of `Company`, `FinancialSnapshot`, `Evidence`, and `DCFAssumptions` values built from Amazon's real reported financials, used as the end-to-end validation case for this feature and as a regression fixture going forward.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of automated test runs using an assumption set with non-positive terminal-year FCFF fail immediately, before any network call, with an error that names the failing check and the offending figure.
- **SC-002**: The Amazon reference dataset run produces a strictly positive enterprise value, equity value, and implied value per share, with zero manual correction needed after the fix is in place.
- **SC-003**: An analyst can determine, from the raised error message text alone, which computed figure caused a rejection, without reading DCF engine source code.
- **SC-004**: All pre-existing DCF, workflow, and committee tests continue to pass, except where a test's own fixture data must be updated because it relied on a previously-unvalidated implausible result.

## Assumptions

- The plausibility guard is a hard failure (raises an explicit error and halts the pipeline), not a soft warning attached to the report, consistent with this project's existing precedent of failing fast and explicitly on invalid DCF assumptions (e.g., WACC not exceeding terminal growth) and on provider/evidence-traceability failures, rather than allowing an analyst-facing artifact to be built on top of a known-bad result.
- "Non-positive" is used as the threshold (rejecting both zero and negative values) for both terminal-year FCFF and enterprise value, since a going-concern valuation requires a strictly positive, sustaining cash flow base and a strictly positive resulting value.
- The Amazon reference dataset uses whole-dollar figures sourced from Amazon's own FY2025 reported results (10-K / earnings release) for historical actuals, and clearly-labeled, evidence-grounded forecast assumptions for forward-looking figures — it is a validation fixture for this project, not a claim of investment advice about Amazon.
- This feature does not change the DCF formula itself (FCFF, terminal value, enterprise value, equity value, implied value per share all remain as currently implemented) — it adds a validation gate on the computed result, per this project's principle that Python (not the LLM) owns all financial arithmetic and its correctness.
- Rebalancing the specific Amazon forecast assumptions (e.g., how capital expenditure intensity is projected across the forecast years) so that the reference case passes FR-007 is in scope as part of building the reference dataset, but is a data/assumption-design detail resolved during planning/implementation, not a new valuation methodology.
