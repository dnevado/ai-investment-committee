# Feature Specification: Bull/Bear Analysis Generation

**Feature Branch**: `007-bull-bear-generation`

**Created**: 2026-08-13

**Status**: Draft

**Input**: User description: "Build the adversarial analysis layer of the AI Investment Committee. The feature takes the existing structured InvestmentCase, InvestmentThesis, ValuationResult, and supporting Evidence and generates two independent, structured AnalysisAssessments: one Bull case and one Bear case. The Bull assessment must identify the strongest credible upside case, including supporting evidence, assumptions, catalysts, and conditions required for the investment to outperform. The Bear assessment must independently challenge the investment thesis, identifying downside risks, weak assumptions, adverse scenarios, invalidation conditions, and supporting evidence for the downside case. Bull and Bear generation must use separate LLM calls so that neither assessment is conditioned on the arguments produced by the other. Both outputs must use the existing AnalysisAssessment domain model rather than introducing separate BullAssessment or BearAssessment entities. Python must prepare the analysis context, enforce the Bull/Bear role, validate all inputs and structured LLM outputs, validate evidence references and confidence bounds, and ensure no unsupported evidence is introduced. The LLM may reason over the supplied structured context and produce the assessment content, but must not perform or replace deterministic valuation calculations. The feature must provide an injectable LLM provider and deterministic offline tests using a fake provider. It must not introduce a new provider abstraction, duplicate the DCF/valuation logic, generate the final CommitteeDecision, render reports, ingest external data, or implement UI/API/persistence. The resulting Bull and Bear AnalysisAssessments will be consumed by Feature 006, the Investment Committee Decision Engine, which is responsible for adjudicating between the two cases and producing the final CommitteeDecision."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Generate an Evidence-Traceable Bull Case (Priority: P1)

A developer preparing an investment case for committee review needs the strongest credible
upside argument generated from the existing investment case, thesis, evidence, and
valuation — synthesized by an LLM, but never fabricating evidence or performing its own
valuation math.

**Why this priority**: This establishes the feature's core generation mechanism — context
assembly, role-specific prompting, structured-output validation, and evidence
traceability — that both the Bull and Bear cases depend on. Without it, nothing downstream
(including 006's adjudication) has an upside case to weigh.

**Independent Test**: Supply a complete investment case and valuation result to the Bull
generation step (using a test double standing in for OpenAI) and confirm it returns a
validated `AnalysisAssessment` identifying the strongest upside case, with supporting
evidence traceable to the supplied input.

**Acceptance Scenarios**:

1. **Given** a complete investment case (thesis, evidence) and a valuation result, **When**
   Bull generation is invoked, **Then** it returns a validated `AnalysisAssessment` with a
   conclusion, confidence, arguments, assumptions, and supporting evidence populated,
   framed as the strongest credible upside case.
2. **Given** an LLM response that proposes supporting evidence not present in the supplied
   investment case, **When** the assessment is validated, **Then** generation fails
   explicitly rather than silently including the untraceable entry.
3. **Given** a valuation result supplied as context, **When** the Bull case is generated,
   **Then** its figures are used exactly as supplied — no financial recalculation is
   performed by the LLM.
4. **Given** the LLM provider returns an error (timeout, rate limit, network failure) or a
   response that fails schema validation, **When** Bull generation is attempted, **Then**
   the failure is surfaced explicitly and no fabricated fallback assessment is produced.

---

### User Story 2 - Generate an Evidence-Traceable Bear Case, Independently of the Bull Case (Priority: P2)

The same developer needs an equally rigorous downside case — generated through its own,
separate LLM call that never sees the Bull case's arguments, so the downside case is not
softened or anchored by the upside case (or vice versa).

**Why this priority**: Depends on Story 1's generation mechanism already existing, but
delivers the feature's second, adversarially-independent output — without it, the
committee only ever sees one side of the argument.

**Independent Test**: Generate a Bull case and a Bear case for the same investment case and
valuation result, and confirm the Bear generation call's prompt/context contains no content
from the Bull assessment (and vice versa); confirm the Bear case identifies downside risks,
weak assumptions, adverse scenarios, and invalidation conditions, with evidence traceable to
the supplied input.

**Acceptance Scenarios**:

1. **Given** the same complete investment case and valuation result used for a Bull case,
   **When** Bear generation is invoked, **Then** it returns a validated `AnalysisAssessment`
   with a conclusion, confidence, arguments, assumptions, and supporting evidence populated,
   framed as an independent challenge to the investment thesis (downside risks, weak
   assumptions, adverse scenarios, invalidation conditions).
2. **Given** a Bull assessment has already been generated for a context, **When** the Bear
   assessment is generated for the same context, **Then** the Bear generation call does not
   include the Bull assessment's content — the two calls are independent.
3. **Given** an LLM response that proposes supporting evidence not present in the supplied
   investment case, **When** the Bear assessment is validated, **Then** generation fails
   explicitly rather than silently including the untraceable entry.
4. **Given** the LLM provider returns an error or a response that fails schema validation,
   **When** Bear generation is attempted, **Then** the failure is surfaced explicitly and no
   fabricated fallback assessment is produced.

---

### User Story 3 - Verify Bull and Bear Generation Without Calling the Real OpenAI API (Priority: P3)

A developer needs to run this feature's full test suite in CI without real network calls,
real API costs, or nondeterministic LLM output — the OpenAI dependency must be a swappable
boundary for both the Bull and the Bear generation paths.

**Why this priority**: Depends conceptually on Stories 1–2 already existing, but is what
makes the whole feature verifiable and trustworthy on an ongoing basis.

**Independent Test**: Run the feature's test suite with a fake LLM provider standing in for
OpenAI for both Bull and Bear generation, and confirm it completes with zero real network
calls.

**Acceptance Scenarios**:

1. **Given** a test double standing in for the OpenAI provider, **When** Bull and Bear
   generation are each exercised in a test, **Then** both complete with zero network calls
   to the real OpenAI API.
2. **Given** the test double returns a well-formed assessment payload, **When** either
   generation path runs, **Then** the resulting `AnalysisAssessment` validates successfully.
3. **Given** the test double returns a malformed payload, **When** either generation path
   runs, **Then** it fails explicitly with a clear validation error.

---

### Edge Cases

- What happens when the investment case has zero evidence entries? Generation still
  proceeds for either role — `supporting_evidence` is legitimately empty.
- What happens when the Bull call succeeds but the Bear call fails, or vice versa? Each
  call is independent; this feature exposes two separate generation operations, not one
  atomic dual-call operation — a caller invoking both is responsible for handling partial
  success.
- What happens when the LLM proposes evidence not present in the supplied investment case?
  Generation fails explicitly (see User Story 1, acceptance scenario 2; User Story 2,
  acceptance scenario 3).
- What happens when OpenAI is unreachable or times out for either call? An explicit
  provider error is surfaced; no assessment is produced, fabricated, or partially returned.
- What happens when the OpenAI API key is not configured and a real (non-test-double) call
  is attempted? The feature fails explicitly with a clear configuration error before any
  network call is attempted.
- What happens when the supplied valuation result doesn't obviously correspond to the
  supplied investment case (e.g., a mismatched company)? This feature does not
  cross-validate that relationship — ensuring a caller supplies a matching pair is the
  caller's responsibility.
- What happens if a caller generates the Bull and Bear cases in parallel or in either
  order? No ordering dependency is required or assumed between the two calls.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The feature SHALL accept an investment case (with its thesis and evidence)
  and a valuation result as input, and assemble them into a single structured (typed, not a
  raw dictionary) context usable for either Bull or Bear generation.
- **FR-002**: The feature SHALL use OpenAI to generate a Bull assessment identifying the
  strongest credible upside case — including supporting evidence, assumptions, catalysts,
  and the conditions required for the investment to outperform — reusing the existing
  `AnalysisAssessment` domain contract unchanged.
- **FR-003**: The feature SHALL use OpenAI to generate a Bear assessment that independently
  challenges the investment thesis — including downside risks, weak assumptions, adverse
  scenarios, invalidation conditions, and supporting evidence for the downside case —
  reusing the existing `AnalysisAssessment` domain contract unchanged.
- **FR-004**: Bull and Bear generation SHALL each be performed via a separate, independent
  LLM call; the content or arguments of one SHALL NOT be included in, or otherwise
  influence, the generation call for the other.
- **FR-005**: Each LLM call SHALL be made through a provider abstraction (protocol/interface)
  that can be substituted with a test double; this feature's own test suite SHALL require
  zero real network calls to OpenAI. This feature SHALL reuse the existing provider
  abstraction rather than introducing a new one.
- **FR-006**: Each LLM's raw response SHALL be validated against a structured schema before
  being trusted as application data; a response that fails validation SHALL be rejected
  with an explicit error, never partially accepted or silently coerced.
- **FR-007**: Every entry an LLM proposes for supporting evidence (for either role) SHALL be
  checked against the evidence supplied in the investment case; any entry not traceable to
  supplied evidence SHALL cause generation to fail explicitly, never be silently included or
  fabricated.
- **FR-008**: Every confidence value produced SHALL be validated within the existing bounded
  range already used by `AnalysisAssessment.confidence` — a value outside that range SHALL
  be rejected explicitly.
- **FR-009**: The feature SHALL NOT perform, request, or accept from the LLM any financial
  or valuation calculation — the supplied valuation result SHALL only be passed through as
  already-computed, read-only context.
- **FR-010**: The feature SHALL NOT duplicate the deterministic DCF/valuation engine's
  logic.
- **FR-011**: The feature SHALL NOT produce a `CommitteeDecision` or an investment
  recommendation (BUY/WATCH/AVOID) — adjudication between the Bull and Bear cases remains
  the responsibility of 006-committee-decision-engine.
- **FR-012**: The feature SHALL NOT render a human-readable report or document.
- **FR-013**: The feature SHALL NOT ingest external data, and SHALL NOT introduce a UI, an
  API, or persistence.
- **FR-014**: OpenAI API credentials SHALL be sourced only from the existing application
  settings/configuration mechanism — never hardcoded in source, never logged, never included
  in any generated output.
- **FR-015**: If OpenAI API credentials are not configured when a real (non-test-double)
  call is attempted, the feature SHALL fail explicitly with a clear configuration error
  before attempting any network call.
- **FR-016**: The feature SHALL surface OpenAI provider errors (timeouts, rate limits,
  network failures) explicitly to the caller, for either the Bull or the Bear call — never
  substituting a fabricated or default assessment when a provider call fails.
- **FR-017**: The feature SHALL perform no persistence (no database, no file writes) of
  either generated assessment — it returns the structured `AnalysisAssessment`s to its
  caller.
- **FR-018**: The feature SHALL NOT modify the supplied investment case, valuation result,
  or the existing `AnalysisAssessment` domain model — it composes and generates read-only.

### Key Entities

- **BullBearContext**: The structured, typed bundle of an investment case (thesis and
  evidence) and a valuation result, assembled as input to either Bull or Bear generation.
- **AnalysisAssessment**: The existing domain entity (conclusion, confidence, arguments,
  supporting evidence, assumptions, risks) — reused unchanged as the structured output of
  both roles. Nothing on the entity itself distinguishes a Bull assessment from a Bear
  assessment; the role is a property of how and when it was generated, not of the stored
  object.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of successfully generated Bull and Bear assessments have every
  `supporting_evidence` entry traceable to the supplied investment case — zero fabricated
  evidence ever appears.
- **SC-002**: 100% of generated confidence values fall within the existing bounded range —
  zero out-of-range values are ever returned.
- **SC-003**: 100% of this feature's own automated tests run successfully with zero calls to
  the real OpenAI API, for both the Bull and the Bear generation paths.
- **SC-004**: 100% of Bear generation calls can be independently verified as not having
  received the Bull assessment's content, and vice versa.
- **SC-005**: Zero financial or valuation calculations are performed by the LLM in either
  generation path — every valuation figure used originates solely from the supplied
  valuation result.
- **SC-006**: 100% of generation attempts where the LLM response fails schema validation are
  rejected explicitly, with zero partially-formed assessments ever returned.
- **SC-007**: 100% of provider-error scenarios (timeout, rate limit, network failure), for
  either role, result in an explicit failure being surfaced, never a fabricated fallback
  assessment.

## Assumptions

- **Two separate generation operations, not one combined call**: Consistent with FR-004,
  Bull and Bear generation are exposed as two independent operations (however a caller
  chooses to sequence or parallelize them) rather than a single function that returns both —
  a single combined call could too easily tempt an implementation into conditioning one
  role's prompt on the other's output.
- **`AnalysisAssessment` is reused unchanged, for both roles**: Per the explicit instruction
  not to introduce `BullAssessment`/`BearAssessment` entities, both generation paths produce
  the exact same existing domain type from 002-domain-model. A caller must track which
  assessment is the Bull case and which is the Bear case by how it obtained them, not by any
  field on the object itself.
- **Valuation input is a `ValuationResult`, not the richer `DCFResult`**: Per the explicit
  request, this feature accepts the domain-level `ValuationResult` summary
  (002-domain-model) as its valuation context, not the full `DCFResult` from
  003-dcf-valuation-engine. It is assumed to already exist (typically produced from a
  `DCFResult` via the existing `to_valuation_result` conversion) before this feature is
  invoked; how it was produced is out of this feature's concern.
- **Provider abstraction reuses the established pattern**: Consistent with
  004-investment-research-thesis and 006-committee-decision-engine, both generation calls go
  through the same existing, swappable provider protocol — this feature does not define a
  second, independent provider abstraction.
- **No retry/self-correction loop**: If an LLM's response fails schema or
  evidence-traceability validation, generation fails fast with an explicit error rather than
  automatically retrying with a corrective prompt — consistent with 004/006's precedent.
- **No persistence in this feature**: Consistent with the constitution's "no premature
  infrastructure" guidance — both generated assessments are returned to the caller, not
  written to any store.
- **No cross-validation between the investment case and the valuation result**: Consistent
  with 004/005/006's own precedent, the caller is responsible for supplying a coherent,
  matching pair; this feature does not verify that relationship.
- **Consumed by 006, not integrated with it**: This feature produces standalone Bull and
  Bear `AnalysisAssessment`s; wiring them into 006-committee-decision-engine's
  `CommitteeAdjudicationContext` is the caller's responsibility, not something this feature
  performs itself.
