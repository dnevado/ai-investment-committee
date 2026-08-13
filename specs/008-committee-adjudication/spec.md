# Feature Specification: Committee Adjudication Layer

**Feature Branch**: `008-committee-adjudication`

**Created**: 2026-08-13

**Status**: Draft

**Input**: User description: "Implement the investment committee adjudication layer that takes the existing investment case, DCF valuation, bull assessment, and bear assessment, and produces a final structured investment decision. The feature must make the committee's reasoning explicit, evidence-grounded, and auditable, including recommendation, rationale, confidence, key points of agreement/disagreement, and dissenting views. The decision must reference only evidence already present in the investment case and must never fabricate supporting evidence. The implementation should use the existing LLM provider abstraction, structured drafts, validation, prompts, domain models, and no-network unit-test pattern established by previous features. Scope: CommitteeAdjudicationContext, committee adjudication prompt, structured CommitteeDecisionDraft, generation through the existing LLMProvider abstraction, validation of supporting evidence IDs, construction of the final InvestmentDecision, propagation of provider errors without fabricating decisions, handling of disagreement/dissent between bull and bear assessments, unit tests and no-network dependency tests, integration with the existing domain models. Out of scope: new DCF or valuation logic, new research or web/data acquisition, new financial data sources, UI, persistence, changes to the existing provider architecture. The feature is complete when the existing thesis, DCF result, bull assessment, and bear assessment can be synthesized into a validated, evidence-backed final InvestmentDecision that is ready to be consumed by the report layer."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Adjudicate Bull and Bear Cases Into a Structured Committee Decision (Priority: P1)

A developer closing out the MVP workflow needs to combine a company's investment case
(thesis and evidence), a deterministic DCF valuation, and independently-produced Bull and
Bear assessments into one adjudicated final investment decision — synthesized by an LLM
acting as committee chair, but never performing its own financial math and never simply
averaging the two sides.

**Why this priority**: This is the feature's core value — it is the piece that turns two
one-sided cases plus a valuation into an actual decision. Without it, nothing produced by
the prior features (evidence, thesis, valuation, bull/bear assessments) ever resolves into
a recommendation the report layer can present.

**Independent Test**: Supply a complete set of already-validated inputs (investment case,
DCF result, bull assessment, bear assessment) to the adjudication step (using a test double
standing in for the LLM provider) and confirm it returns a validated decision with a
recommendation, rationale, and confidence, whose referenced evidence is traceable to the
supplied input.

**Acceptance Scenarios**:

1. **Given** a complete investment case, DCF result, bull assessment, and bear assessment,
   **When** adjudication is invoked, **Then** it returns a validated decision with a
   recommendation, rationale, and confidence populated.
2. **Given** the bull and bear assessments disagree materially, **When** adjudication is
   invoked, **Then** the resulting decision's rationale explicitly addresses the points of
   agreement and disagreement rather than silently splitting the difference.
3. **Given** a DCF result supplied as context, **When** the decision is adjudicated,
   **Then** its valuation figures are used exactly as supplied — no financial
   recalculation is performed by the LLM.
4. **Given** an LLM response that proposes supporting evidence not present in the supplied
   investment case, **When** the decision is validated, **Then** adjudication fails
   explicitly rather than silently including the untraceable entry.
5. **Given** the LLM provider returns an error (timeout, rate limit, network failure) or a
   response that fails schema validation, **When** adjudication is attempted, **Then** the
   failure is surfaced explicitly and no fabricated fallback decision is produced.

---

### User Story 2 - Present Dissent When the Chair Overrules a Side (Priority: P2)

When the Chair's decision does not fully adopt the bull or the bear position, that
disagreement must be recorded on the decision, not silently dropped — a core trust property
for a committee memo that is later consumed by the report layer.

**Why this priority**: Depends on Story 1's adjudication already existing, but delivers a
second explicitly required property: an honest, auditable record of what the Chair
overruled, not just what it concluded.

**Independent Test**: Supply bull and bear assessments where the Chair's decision does not
fully align with one side, and confirm the resulting decision's dissent records the
unadopted position; confirm materially aligned assessments produce no fabricated dissent.

**Acceptance Scenarios**:

1. **Given** the bull and bear assessments disagree and the Chair's decision favors one
   side, **When** adjudication completes, **Then** the decision's dissenting views reflect
   the position that was not adopted.
2. **Given** the bull and bear assessments are materially aligned, **When** adjudication
   completes, **Then** dissent is empty rather than fabricated.

---

### User Story 3 - Verify Adjudication Without Calling a Real External LLM Service (Priority: P3)

A developer needs to run this feature's full test suite in CI without real network calls,
real API costs, or nondeterministic LLM output — the LLM provider dependency must be a
swappable boundary, consistent with how every prior LLM-calling feature in this project has
been verified.

**Why this priority**: Depends conceptually on Stories 1–2 already existing, but is what
makes the whole feature verifiable and trustworthy on an ongoing basis.

**Independent Test**: Run the feature's test suite with a fake LLM provider standing in for
the real provider and confirm it completes with zero real network calls.

**Acceptance Scenarios**:

1. **Given** a test double standing in for the LLM provider, **When** the full adjudication
   flow is exercised in a test, **Then** it completes with zero network calls to any real
   external LLM service.
2. **Given** the test double returns a well-formed decision payload, **When** the flow
   runs, **Then** the resulting decision validates successfully.
3. **Given** the test double returns a malformed payload, **When** the flow runs, **Then**
   it fails explicitly with a clear validation error.

---

### Edge Cases

- What happens when the bull and bear assessments fully agree? Adjudication still
  proceeds; dissent is empty rather than fabricated (see User Story 2, acceptance
  scenario 2).
- What happens when a required input (investment case, DCF result, bull assessment, or
  bear assessment) is missing? Adjudication fails explicitly rather than partially
  proceeding.
- What happens when the LLM proposes supporting evidence not present in the supplied
  investment case? Adjudication fails explicitly (see User Story 1, acceptance scenario 4).
- What happens when the LLM provider is unreachable or times out? An explicit provider
  error is surfaced; no decision is produced, fabricated, or partially returned.
- What happens when LLM provider credentials are not configured and a real (non-test-double)
  call is attempted? The feature fails explicitly with a clear configuration error before
  any network call is attempted.
- What happens when the bull assessment, bear assessment, and DCF result don't obviously
  correspond to the same underlying investment case? This feature does not cross-validate
  that relationship — ensuring a caller supplies a coherent, matching set of inputs is the
  caller's responsibility.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The feature SHALL accept an investment case (with its thesis and evidence), a
  DCF valuation result, a bull assessment, and a bear assessment as input, and assemble them
  into a single structured (typed, not a raw dictionary) adjudication context
  (`CommitteeAdjudicationContext`).
- **FR-002**: The feature SHALL use an LLM to synthesize the investment case, valuation, and
  both assessments into a final investment decision (recommendation, rationale, confidence,
  key points of agreement/disagreement, dissent), reusing the existing final-decision domain
  contract unchanged rather than introducing a new one.
- **FR-003**: The LLM call SHALL be made through the existing provider abstraction
  (protocol/interface) that can be substituted with a test double; this feature's own test
  suite SHALL require zero real network calls to any external LLM service. This feature
  SHALL NOT introduce a new or modified provider abstraction.
- **FR-004**: The LLM's raw response SHALL be validated against a structured schema
  (`CommitteeDecisionDraft`) before being trusted as application data; a response that fails
  validation SHALL be rejected with an explicit error, never partially accepted or silently
  coerced.
- **FR-005**: Every entry the LLM proposes as supporting evidence SHALL be checked against
  the evidence supplied in the investment case; any entry not traceable to supplied evidence
  SHALL cause adjudication to fail explicitly, never be silently included or fabricated.
- **FR-006**: The feature SHALL NOT perform, request, or accept from the LLM any financial
  or valuation calculation — DCF figures SHALL only be passed through as already-computed,
  read-only context from the existing DCF engine.
- **FR-007**: The committee decision SHALL NOT be produced by simply averaging the bull and
  bear assessments' confidence or conclusions — the rationale SHALL explicitly engage with
  the key points of agreement and disagreement between the two.
- **FR-008**: The recommendation SHALL be restricted to the existing recommendation values —
  no other recommendation value may be produced.
- **FR-009**: When the bull and bear assessments disagree and the Chair's decision does not
  fully adopt one side, that unadopted position SHALL be recorded as a dissenting view on
  the decision; when the assessments are materially aligned, dissent SHALL be empty rather
  than fabricated.
- **FR-010**: The feature SHALL NOT introduce new DCF or valuation logic, and SHALL NOT
  duplicate the deterministic DCF/valuation engine's logic.
- **FR-011**: The feature SHALL NOT ingest new research, external web/data sources, or new
  financial data sources.
- **FR-012**: LLM provider credentials SHALL be sourced only from the existing application
  settings/configuration mechanism — never hardcoded in source, never logged, never included
  in any generated output.
- **FR-013**: If LLM provider credentials are not configured when a real (non-test-double)
  call is attempted, the feature SHALL fail explicitly with a clear configuration error
  before attempting any network call.
- **FR-014**: The feature SHALL surface LLM provider errors (timeouts, rate limits, network
  failures) explicitly to the caller — never substituting a fabricated or default decision
  when the provider call fails.
- **FR-015**: The feature SHALL perform no persistence (no database, no file writes) of the
  generated decision — it returns the structured decision to its caller.
- **FR-016**: The feature SHALL NOT introduce a UI, an API, or a scheduling mechanism.
- **FR-017**: The feature SHALL NOT modify the supplied investment case, DCF result, bull
  assessment, bear assessment, or any existing domain model — it composes them read-only.
- **FR-018**: The resulting decision SHALL be structured so that it is directly consumable
  by the existing report layer without requiring any new adapter or transformation.

### Key Entities

- **CommitteeAdjudicationContext**: The structured, typed bundle of an investment case, a
  DCF valuation result, a bull assessment, and a bear assessment assembled as input to
  adjudication.
- **CommitteeDecisionDraft**: The structured, LLM-facing intermediate representation of the
  Chair's reasoning (central thesis, points of agreement/disagreement, valuation summary,
  downside risks, invalidation conditions, recommendation, confidence, dissent, and
  supporting-evidence references) validated before being trusted.
- **InvestmentDecision**: The final, structured, evidence-backed investment decision this
  feature produces — recommendation, rationale, confidence, and dissent — ready to be
  consumed by the report layer. This reuses the project's existing final-decision domain
  entity; no new or parallel decision type is introduced (see Assumptions).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of successfully adjudicated decisions have every referenced supporting
  evidence entry traceable to the supplied investment case — zero fabricated evidence ever
  appears.
- **SC-002**: 100% of adjudication attempts where the LLM response fails schema validation
  are rejected explicitly, with zero partially-formed decisions ever returned.
- **SC-003**: 100% of this feature's own automated tests run successfully with zero calls to
  any real external LLM service.
- **SC-004**: 100% of decisions built from materially disagreeing bull/bear assessments
  produce non-empty dissent when the Chair does not fully adopt one side; 100% of decisions
  built from materially aligned assessments produce empty dissent.
- **SC-005**: Zero financial calculations are performed by the LLM — every valuation figure
  used in a decision's context originates solely from the supplied DCF result.
- **SC-006**: 100% of produced recommendations fall within the existing recommendation set.
- **SC-007**: 100% of provider-error scenarios (timeout, rate limit, network failure) result
  in an explicit failure being surfaced, never a fabricated fallback decision.
- **SC-008**: 100% of produced decisions are directly consumable by the existing report
  layer with no new adapter code.

## Assumptions

- **"InvestmentDecision" maps to the project's existing final-decision domain entity**: The
  source description asks for a "final structured investment decision" (`InvestmentDecision`)
  that is "ready to be consumed by the report layer." The project's existing domain model and
  report layer already define and consume a `CommitteeDecision` entity (recommendation,
  rationale, referenced evidence, dissent) for exactly this purpose. Per the explicit
  instruction to integrate with existing domain models rather than introduce new ones, this
  feature reuses that existing entity unchanged as its output; "InvestmentDecision" in the
  source description is read as this feature's informal name for that same entity, not a
  request for a new, parallel type.
- **Provider abstraction reuses the established pattern**: Consistent with prior LLM-calling
  features in this project, the LLM call goes through the existing swappable provider
  protocol, is mockable in tests, and provider credentials come from the existing settings
  mechanism. This feature does not require a second, independent provider abstraction
  design, and does not change the existing provider architecture.
- **No retry/self-correction loop**: If the LLM's response fails schema or
  evidence-traceability validation, this feature fails fast with an explicit error rather
  than automatically retrying with a corrective prompt, consistent with this project's
  established precedent and the constitution's minimal-architecture principle.
- **No persistence in this feature**: Consistent with the constitution's "no premature
  infrastructure" guidance — the generated decision is returned to the caller, not written
  to any store.
- **Confidence is LLM-proposed, code-validated**: The decision's confidence is proposed by
  the LLM and validated in code against the same bounded-range pattern already used
  elsewhere in this project's assessment models — it is never computed from the bull/bear
  inputs by this feature.
- **No cross-validation between composed inputs**: Consistent with this project's own
  precedent, the caller is responsible for supplying a coherent, matching set of inputs
  (investment case, DCF result, bull assessment, and bear assessment that all pertain to the
  same underlying analysis); this feature does not verify that relationship.
- **Bull/Bear generation is out of scope**: This feature consumes already-produced bull and
  bear assessments; generating them is a separate, previously-scoped feature. This feature's
  own tests construct bull/bear assessments directly as fixtures.
- **Report rendering is out of scope**: This feature's sole output is the final decision
  itself; rendering it into a human-readable report or document is the existing report
  layer's responsibility, not something this feature performs.
