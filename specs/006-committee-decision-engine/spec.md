# Feature Specification: Investment Committee Decision Engine

**Feature Branch**: `006-committee-decision-engine`

**Created**: 2026-08-13

**Status**: Draft

**Input**: User description: "Investment Committee decision engine. Build the AI Investment Committee layer that takes the existing structured InvestmentCase, DCF/ValuationResult, InvestmentThesis, and supporting Evidence and produces a structured CommitteeDecision and report. Python must prepare and validate all structures. The LLM may [truncated in the original request]." Clarified via follow-up question: the Committee Chair MUST weigh independently-produced Bull and Bear assessments (not just the thesis alone) before deciding, satisfying the constitution's Bull/Bear Symmetry principle; this feature consumes already-produced Bull and Bear assessments — it does not generate them."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Adjudicate Bull and Bear Cases Into a Structured Committee Decision (Priority: P1)

A developer closing out the MVP workflow needs to combine a company's investment case
(thesis and evidence), a deterministic DCF valuation, and independently-produced Bull and
Bear assessments into one adjudicated `CommitteeDecision` — synthesized by an LLM acting as
committee chair, but never performing its own financial math and never simply averaging the
two sides.

**Why this priority**: This is the feature's core value and the piece that turns two
one-sided cases plus a valuation into an actual decision — without it, nothing produced by
the prior features (evidence, thesis, valuation, bull/bear assessments) ever resolves into
a recommendation.

**Independent Test**: Supply a complete set of already-validated inputs (investment case,
DCF result, bull assessment, bear assessment) to the decision-adjudication step (using a
test double standing in for OpenAI) and confirm it returns a validated `CommitteeDecision`
with a recommendation, rationale, and evidence traceable to the supplied input.

**Acceptance Scenarios**:

1. **Given** a complete investment case, DCF result, bull assessment, and bear assessment,
   **When** adjudication is invoked, **Then** it returns a validated `CommitteeDecision`
   with a recommendation, rationale, and confidence populated.
2. **Given** the bull and bear assessments disagree materially, **When** adjudication is
   invoked, **Then** the resulting decision's rationale explicitly addresses the
   disagreement rather than silently splitting the difference.
3. **Given** a DCF result supplied as context, **When** the decision is adjudicated,
   **Then** its valuation figures are used exactly as supplied — no financial
   recalculation is performed by the LLM.
4. **Given** an LLM response that proposes referenced evidence not present in the supplied
   investment case, **When** the decision is validated, **Then** adjudication fails
   explicitly rather than silently including the untraceable entry.
5. **Given** the LLM provider returns an error (timeout, rate limit, network failure) or a
   response that fails schema validation, **When** adjudication is attempted, **Then** the
   failure is surfaced explicitly and no fabricated fallback decision is produced.

---

### User Story 2 - Present Dissent When the Chair Overrules a Side (Priority: P2)

When the Chair's decision does not fully adopt the bull or the bear position, that
disagreement must be recorded on the decision, not silently dropped — a core trust property
for a committee memo.

**Why this priority**: Depends on Story 1's adjudication already existing, but delivers a
second explicitly required property: an honest record of what the Chair overruled, not just
what it concluded.

**Independent Test**: Supply bull and bear assessments where the Chair's decision does not
fully align with one side, and confirm the resulting `CommitteeDecision`'s dissent records
the unadopted position; confirm materially aligned assessments produce no fabricated
dissent.

**Acceptance Scenarios**:

1. **Given** the bull and bear assessments disagree and the Chair's decision favors one
   side, **When** adjudication completes, **Then** the decision's dissent reflects the
   position that was not adopted.
2. **Given** the bull and bear assessments are materially aligned, **When** adjudication
   completes, **Then** dissent is empty rather than fabricated.

---

### User Story 3 - Verify the Feature Without Calling the Real OpenAI API (Priority: P3)

A developer needs to run this feature's full test suite in CI without real network calls,
real API costs, or nondeterministic LLM output — the OpenAI dependency must be a swappable
boundary.

**Why this priority**: Depends conceptually on Stories 1–2 already existing, but is what
makes the whole feature verifiable and trustworthy on an ongoing basis.

**Independent Test**: Run the feature's test suite with a fake LLM provider standing in for
OpenAI and confirm it completes with zero real network calls.

**Acceptance Scenarios**:

1. **Given** a test double standing in for the OpenAI provider, **When** the full
   adjudication flow is exercised in a test, **Then** it completes with zero network calls
   to the real OpenAI API.
2. **Given** the test double returns a well-formed decision payload, **When** the flow
   runs, **Then** the resulting `CommitteeDecision` validates successfully.
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
- What happens when the LLM proposes referenced evidence not present in the supplied
  investment case? Adjudication fails explicitly (see User Story 1, acceptance scenario 4).
- What happens when OpenAI is unreachable or times out? An explicit provider error is
  surfaced; no decision is produced, fabricated, or partially returned.
- What happens when the OpenAI API key is not configured and a real (non-test-double) call
  is attempted? The feature fails explicitly with a clear configuration error before any
  network call is attempted.
- What happens when the bull assessment, bear assessment, and DCF result don't obviously
  correspond to the same underlying investment case? This feature does not cross-validate
  that relationship, consistent with 004/005's precedent — ensuring a caller supplies a
  coherent, matching set of inputs is the caller's responsibility.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The feature SHALL accept an investment case (with its thesis and evidence), a
  DCF valuation result, a bull assessment, and a bear assessment as input, and assemble them
  into a single structured (typed, not a raw dictionary) adjudication context.
- **FR-002**: The feature SHALL use OpenAI as the LLM provider to synthesize the investment
  case, valuation, and both assessments into a committee decision (recommendation,
  rationale, confidence, dissent), reusing the existing `CommitteeDecision` domain contract
  unchanged.
- **FR-003**: The LLM call SHALL be made through a provider abstraction (protocol/interface)
  that can be substituted with a test double; this feature's own test suite SHALL require
  zero real network calls to OpenAI.
- **FR-004**: The LLM's raw response SHALL be validated against a structured schema before
  being trusted as application data; a response that fails validation SHALL be rejected with
  an explicit error, never partially accepted or silently coerced.
- **FR-005**: Every entry the LLM proposes as referenced evidence SHALL be checked against
  the evidence supplied in the investment case; any entry not traceable to supplied evidence
  SHALL cause adjudication to fail explicitly, never be silently included or fabricated.
- **FR-006**: The feature SHALL NOT perform, request, or accept from the LLM any financial
  calculation — DCF figures SHALL only be passed through as already-computed, read-only
  context from the existing DCF engine.
- **FR-007**: The committee decision SHALL NOT be produced by simply averaging the bull and
  bear assessments' confidence or conclusions — the rationale SHALL explicitly engage with
  the points of disagreement between the two.
- **FR-008**: The recommendation SHALL be restricted to the existing BUY/WATCH/AVOID
  values — no other recommendation value may be produced.
- **FR-009**: When the bull and bear assessments disagree and the Chair's decision does not
  fully adopt one side, that unadopted position SHALL be recorded as dissent on the
  decision; when the assessments are materially aligned, dissent SHALL be empty rather than
  fabricated.
- **FR-010**: The feature SHALL NOT introduce LangGraph or any multi-agent orchestration —
  adjudication is a single, direct synthesis step.
- **FR-011**: OpenAI API credentials SHALL be sourced only from the existing application
  settings/configuration mechanism — never hardcoded in source, never logged, never included
  in any generated output.
- **FR-012**: If OpenAI API credentials are not configured when a real (non-test-double)
  call is attempted, the feature SHALL fail explicitly with a clear configuration error
  before attempting any network call.
- **FR-013**: The feature SHALL surface OpenAI provider errors (timeouts, rate limits,
  network failures) explicitly to the caller — never substituting a fabricated or default
  decision when the provider call fails.
- **FR-014**: The feature SHALL perform no persistence (no database, no file writes) of the
  generated decision — it returns the structured `CommitteeDecision` to its caller.
- **FR-015**: The feature SHALL NOT modify the supplied bull or bear assessments, the
  investment case, or the DCF engine — it composes them read-only.

### Key Entities

- **CommitteeAdjudicationContext**: The structured, typed bundle of an investment case, a
  DCF valuation result, a bull assessment, and a bear assessment assembled as input to
  adjudication.
- **CommitteeDecision**: The existing domain entity (recommendation, rationale, referenced
  evidence, referenced thesis, dissent) — reused unchanged as this feature's structured
  output.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of successfully adjudicated decisions have every referenced evidence
  entry traceable to the supplied investment case — zero fabricated evidence ever appears.
- **SC-002**: 100% of adjudication attempts where the LLM response fails schema validation
  are rejected explicitly, with zero partially-formed decisions ever returned.
- **SC-003**: 100% of this feature's own automated tests run successfully with zero calls to
  the real OpenAI API.
- **SC-004**: 100% of decisions built from materially disagreeing bull/bear assessments
  produce non-empty dissent when the Chair does not fully adopt one side; 100% of decisions
  built from materially aligned assessments produce empty dissent.
- **SC-005**: Zero financial calculations are performed by the LLM — every valuation figure
  used in a decision's context originates solely from the supplied DCF result.
- **SC-006**: 100% of produced recommendations fall within the existing BUY/WATCH/AVOID set.
- **SC-007**: 100% of provider-error scenarios (timeout, rate limit, network failure) result
  in an explicit failure being surfaced, never a fabricated fallback decision.

## Assumptions

- **`CommitteeDecision` is reused unchanged**: Consistent with 004-investment-research-thesis's
  treatment of `InvestmentThesis`, this feature produces the existing `CommitteeDecision`
  domain model from 002-domain-model exactly as-is — no new or modified output schema.
- **Bull/Bear generation is out of scope**: Per the clarified scope, this feature consumes
  already-produced bull and bear assessments; generating them (an adversarial Bull/Bear
  agent pair) is a separate, not-yet-built feature in this project's MVP sequence. This
  feature's own tests construct bull/bear assessments directly as fixtures, the same way
  004's tests construct an `InvestmentCase` directly rather than depending on a live
  research step.
- **Report rendering is out of scope**: 005-investment-committee-report already composes a
  `CommitteeDecision` (however produced) into a structured `CommitteeReport` and a rendered
  document. This feature's sole output is the `CommitteeDecision` itself; no new rendering
  is introduced, avoiding duplication of 005's already-built composition/rendering step.
- **Provider abstraction reuses the established pattern**: Consistent with
  004-investment-research-thesis, the LLM call goes through a swappable provider protocol,
  is mockable in tests, and OpenAI credentials come from the existing settings mechanism.
  This feature does not require a second, independent provider abstraction design.
- **No retry/self-correction loop**: If the LLM's response fails schema or
  evidence-traceability validation, this feature fails fast with an explicit error rather
  than automatically retrying with a corrective prompt — consistent with 004's precedent and
  the constitution's minimal-architecture principle.
- **No persistence in this feature**: Consistent with the constitution's "no premature
  infrastructure" guidance — the generated decision is returned to the caller, not written
  to any store.
- **Confidence/conviction is LLM-proposed, Python-validated**: The decision's confidence (or
  conviction) is proposed by the LLM and validated by Python against the same bounded-range
  pattern already used for `AnalysisAssessment.confidence` (002-domain-model) — Python never
  computes it from the bull/bear inputs.
- **No cross-validation between composed inputs**: Consistent with 004/005's own precedent,
  the caller is responsible for supplying a coherent, matching set of inputs (investment
  case, DCF result, bull assessment, and bear assessment that all pertain to the same
  underlying analysis); this feature does not verify that relationship.
