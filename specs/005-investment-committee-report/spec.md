# Feature Specification: Investment Committee Report

**Feature Branch**: `005-investment-committee-report`

**Created**: 2026-08-12

**Status**: Draft

**Input**: User description: "Build Feature 005 — Investment Committee Report. Close the MVP end-to-end investment workflow by producing a structured and human-readable investment committee report that composes the existing Company, FinancialSnapshot, Evidence, InvestmentThesis, DCF/ValuationResult, AnalysisAssessment, and CommitteeDecision contracts. The report must present the investment thesis, supporting evidence, DCF valuation, assumptions, risks, invalidation conditions, committee assessment, recommendation, and dissent when present. Python prepares and validates the structured data; the LLM may generate human-readable narrative where appropriate, but financial calculations remain exclusively in the deterministic DCF engine. The feature must reuse existing domain contracts and the 003 DCF engine rather than duplicate financial logic. It must produce both a structured report model and a Markdown/document representation suitable for human review and downstream AI Committee analysis. Keep the MVP free of persistence, API, UI, scheduling, market-data integration, or unnecessary infrastructure. No new financial calculations or valuation logic should be introduced."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Assemble a Complete, Structured Investment Committee Report (Priority: P1)

A developer closing out the MVP workflow needs to take everything already produced for a
company — its profile, financial snapshots, investment thesis with supporting evidence, a
deterministic DCF valuation, a committee assessment, and a committee decision — and compose
them into one validated, structured report, without altering, recomputing, or fabricating
any of the underlying data.

**Why this priority**: This is the feature's core value and the piece that closes the MVP
end-to-end workflow — without a working composition step, nothing produced by the prior
features (evidence, thesis, valuation, assessment, decision) ever comes together into a
single reviewable artifact.

**Independent Test**: Supply a complete set of already-validated inputs (company, financial
snapshot(s), thesis with evidence, DCF valuation, assessment, decision) to the report
assembly step and confirm it returns a validated, structured report containing all of them
unchanged.

**Acceptance Scenarios**:

1. **Given** a complete set of validated inputs, **When** the report is assembled, **Then**
   it returns a structured report containing the company, financial snapshots, thesis with
   its supporting evidence, DCF valuation, committee assessment, and committee decision
   exactly as supplied.
2. **Given** a committee decision that records one or more dissenting positions, **When**
   the report is assembled, **Then** the dissent is included in the structured report.
3. **Given** a committee decision with no recorded dissent, **When** the report is
   assembled, **Then** the structured report explicitly reflects that no dissent was
   recorded, rather than silently omitting the topic.
4. **Given** any required input is missing, **When** assembly is attempted, **Then** it
   fails explicitly and no partial report is produced.

---

### User Story 2 - Render the Report Into a Human-Readable Document (Priority: P2)

A developer (or the future AI Investment Committee workflow) needs a human-readable
document generated deterministically from the same validated structured report — suitable
for human review and for downstream AI Committee analysis.

**Why this priority**: Depends on Story 1's structured report already existing, but
delivers the feature's second explicitly required output — an artifact a person or a
downstream process can actually read.

**Independent Test**: Render the same structured report twice and confirm the two
documents are identical and contain exactly the report's structured content (thesis,
evidence, DCF valuation, assumptions, risks, invalidation conditions, committee assessment,
recommendation, and dissent).

**Acceptance Scenarios**:

1. **Given** a validated structured report, **When** the human-readable document is
   generated, **Then** it contains the investment thesis, supporting evidence, DCF
   valuation, assumptions, risks, invalidation conditions, committee assessment,
   recommendation, and dissent (or its explicit absence) — no additional invented content.
2. **Given** the same structured report, **When** the document is generated twice,
   **Then** both outputs are byte-identical.

---

### User Story 3 - Keep the Report Free of New Valuation Logic or Recommendations (Priority: P3)

A developer relying on this report needs confidence that composing several already-trusted
prior features together did not silently introduce a new valuation shortcut or let the
report override what the committee actually decided.

**Why this priority**: Guards the MVP's core trust properties — deterministic valuation and
evidence traceability — from regressing as this feature brings multiple sensitive features
together. Worth its own explicit, tested guarantee rather than being assumed.

**Independent Test**: Inspect a generated report and confirm every valuation figure traces
exactly to the DCF engine's own output, and confirm the feature never computes, infers, or
overrides the committee decision's recommendation.

**Acceptance Scenarios**:

1. **Given** a DCF valuation result supplied as input, **When** the report is assembled and
   rendered, **Then** every valuation figure in the structured report and the rendered
   document matches the DCF engine's output exactly.
2. **Given** a committee decision with a recommendation, **When** the report is assembled,
   **Then** the report presents that recommendation unchanged — the feature does not
   compute or alter it.

---

### Edge Cases

- What happens when the investment thesis or committee assessment has no supporting
  evidence? The report still assembles; the corresponding section is legitimately empty
  rather than a failure.
- What happens when the committee decision has no dissent recorded? The report explicitly
  states that no dissent was recorded, rather than omitting the section (see FR-006).
- What happens when a required input (thesis, valuation, assessment, or decision) is
  missing? Assembly fails explicitly (see FR-014).
- What happens when the supplied financial snapshots span different fiscal periods or
  currencies? This feature does not reconcile them — it presents each supplied snapshot
  as-is; ensuring supplied data is consistent is the responsibility of the caller, not this
  feature.
- What happens when the DCF valuation, thesis, assessment, and decision don't obviously
  correspond to the same underlying analysis? This feature does not cross-validate that
  relationship — ensuring a caller supplies a coherent, matching set of inputs is the
  caller's responsibility.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The feature SHALL accept a company, one or more financial snapshots, an
  investment thesis (with its supporting evidence), a DCF valuation result, a committee
  assessment, and a committee decision as input, and assemble them into a single structured
  (typed, not a raw dictionary) report object.
- **FR-002**: The report SHALL present the investment thesis summary together with its
  supporting evidence, key assumptions, key risks, and invalidation conditions exactly as
  supplied — no evidence or narrative content may be added, removed, or altered during
  assembly.
- **FR-003**: The report SHALL present the DCF valuation results exactly as produced by the
  existing deterministic DCF engine — the feature SHALL NOT perform, request, or infer any
  new financial calculation.
- **FR-004**: The report SHALL present the committee assessment's conclusion, confidence,
  supporting arguments, assumptions, and risks exactly as supplied.
- **FR-005**: The report SHALL present the committee decision's recommendation and rationale
  exactly as supplied — the feature SHALL NOT compute, infer, or override the
  recommendation.
- **FR-006**: The report SHALL present dissent when the committee decision records one or
  more dissenting positions, and SHALL explicitly indicate when no dissent was recorded.
- **FR-007**: The composed structured report SHALL be validated before it can be rendered
  into a document; a missing or invalid required input SHALL be rejected explicitly.
- **FR-008**: The feature SHALL deterministically render a validated report into a
  human-readable document containing exactly its structured content — no financial figure
  in the rendered document may differ from the structured report's own values.
- **FR-009**: Rendering the same structured report into a document multiple times SHALL
  always produce an identical result.
- **FR-010**: The feature SHALL NOT introduce any new financial calculation, valuation
  method, or valuation logic — every valuation figure in the report SHALL originate solely
  from the existing deterministic DCF engine (003-dcf-valuation-engine).
- **FR-011**: The feature SHALL perform no persistence (no database, no file writes) of the
  generated report or document — it returns the structured report and rendered document to
  its caller.
- **FR-012**: The feature SHALL NOT introduce an API, UI, scheduling mechanism, or
  market-data integration.
- **FR-013**: The feature SHALL NOT modify any existing domain entity (company, financial
  snapshot, evidence, investment thesis, valuation result, committee assessment, committee
  decision) or the DCF engine — it composes them read-only.
- **FR-014**: If any required input (thesis, valuation, assessment, or decision) is missing
  when assembling the report, the feature SHALL fail explicitly with a clear error rather
  than producing a partial or fabricated report.

### Key Entities

- **CommitteeReport**: The structured, composed investment committee report — bundles the
  company, financial snapshot(s), investment thesis (with its supporting evidence), DCF
  valuation, committee assessment, and committee decision (recommendation and dissent) into
  one report object, without altering or recomputing any of the composed data.
- **CommitteeReportDocument**: The human-readable (Markdown) rendering of a validated
  `CommitteeReport`, suitable for human review and downstream AI Committee analysis.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of successfully assembled reports present every supplied evidence,
  assumption, risk, and invalidation condition unchanged from the input.
- **SC-002**: 100% of valuation figures shown in a report match the values produced by the
  deterministic DCF engine exactly — zero recalculated or invented figures.
- **SC-003**: Rendering the same structured report into a document produces an identical
  result 100% of the time.
- **SC-004**: 100% of reports whose committee decision records dissent display that
  dissent; 100% of reports with no recorded dissent explicitly indicate its absence rather
  than omitting the section silently.
- **SC-005**: 100% of assembly attempts missing a required input fail explicitly, with zero
  partially-formed reports ever returned.
- **SC-006**: Zero new financial calculations are introduced by this feature — every
  valuation figure originates from the existing deterministic DCF engine.
- **SC-007**: Zero persistence, API, UI, scheduling, or market-data integration is present
  in this feature.

## Assumptions

- **Narrative content stays deterministic in this feature**: The source description's "the
  LLM may generate human-readable narrative where appropriate" is read as permissive, not as
  a mandate for this feature to introduce a new LLM call. Consistent with reusing
  004-investment-research-thesis rather than duplicating its orchestration, and with the
  explicit instruction to keep the MVP free of unnecessary infrastructure, this feature's
  rendered document is produced deterministically by Python from the already-structured
  report content (including the investment thesis's own narrative summary, which may itself
  have been produced separately by 004's thesis-generation step). This feature does not
  introduce a new LLM call. Report-level narrative synthesis beyond the composed structured
  content, if ever needed, would be a separate, explicitly-scoped future feature.
- **Document format**: Markdown, consistent with 004-investment-research-thesis's
  established convention and this project's existing documentation style.
- **No persistence**: Consistent with the constitution's "no premature infrastructure"
  guidance and the explicit instruction to keep the MVP free of persistence — the generated
  report and document are returned to the caller, not written to any store.
- **No cross-validation between composed inputs**: Consistent with 004's own precedent, the
  caller is responsible for supplying a coherent, matching set of inputs (thesis, valuation,
  assessment, and decision that all pertain to the same underlying analysis); this feature
  does not verify that relationship.
- **DCF valuation source**: The "DCF/ValuationResult" this report composes is the result
  produced by the existing 003-dcf-valuation-engine; no new valuation type or calculation is
  introduced by this feature.
- **Dissent representation**: Reused unchanged from the existing committee decision's
  dissent data; an empty/absent dissent is presented as "no dissent recorded" rather than a
  blank or omitted section.
