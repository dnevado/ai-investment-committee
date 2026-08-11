# Feature Specification: Investment Research & Thesis Generation

**Feature Branch**: `004-investment-research-thesis`

**Created**: 2026-08-11

**Status**: Draft

**Input**: User description: "Build an investment research and thesis generation layer that prepares structured context from InvestmentCase, Evidence, FinancialSnapshot, and the deterministic DCFResult, then uses OpenAI to generate a structured InvestmentThesis suitable as input to the future AI Investment Committee. The LLM may interpret and synthesize supplied evidence, assumptions, risks, catalysts, invalidation conditions, and DCF results, but must not perform financial calculations — Python remains responsible for deterministic financial data and validation. Output: a validated Pydantic InvestmentThesis, a human-readable thesis document generated from the same structured thesis, and traceable supporting evidence with explicit assumptions, risks, and invalidation conditions. Must not make an investment decision, produce BUY/WATCH/AVOID recommendations, implement Bull/Bear committee assessments, or introduce LangGraph/multi-agent orchestration. OpenAI is the LLM provider; credentials come from the existing settings mechanism, never hardcoded; tests must not require real OpenAI calls, the provider boundary must be mockable. No financial arithmetic belongs in the LLM — the existing deterministic DCF engine remains the sole source of valuation calculations."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Generate an Evidence-Traceable Investment Thesis (Priority: P1)

A developer building the AIC workflow needs to turn an `InvestmentCase`'s research inputs
(company, financial snapshots, evidence) together with an already-computed `DCFResult` into a
validated, structured `InvestmentThesis` — synthesized by an LLM, but never fabricating evidence
or performing its own financial math.

**Why this priority**: This is the core value of the feature — without a working, trustworthy
thesis-generation step, nothing else in this feature matters.

**Independent Test**: Supply a complete `InvestmentCase` and a `DCFResult` to the thesis-generation
service (using a test double standing in for OpenAI) and confirm it returns a validated
`InvestmentThesis` whose supporting evidence is traceable to the supplied input.

**Acceptance Scenarios**:

1. **Given** a complete `InvestmentCase` (company, financial snapshot(s), evidence) and a
   `DCFResult`, **When** thesis generation is invoked, **Then** it returns a validated
   `InvestmentThesis` with a summary, supporting evidence, key assumptions, key risks, and
   invalidation conditions populated.
2. **Given** an LLM response that proposes supporting evidence not present in the supplied input,
   **When** the thesis is validated, **Then** generation fails explicitly rather than silently
   including the untraceable entry.
3. **Given** a `DCFResult` supplied as context, **When** the thesis is generated, **Then** its
   valuation figures are used exactly as supplied — no financial recalculation is performed by the
   LLM.
4. **Given** the LLM provider returns an error (timeout, rate limit, network failure) or a
   response that fails schema validation, **When** thesis generation is attempted, **Then** the
   failure is surfaced explicitly and no fabricated fallback thesis is produced.

---

### User Story 2 - Render the Thesis Into a Human-Readable Document (Priority: P2)

A developer needs a human-readable document generated deterministically from the same validated
`InvestmentThesis` — not a second, independently-generated piece of text that could drift from
the structured data.

**Why this priority**: Depends on Story 1's structured thesis already existing, but delivers the
feature's second explicitly required output.

**Independent Test**: Render the same `InvestmentThesis` twice and confirm the two documents are
identical and contain exactly the thesis's structured content.

**Acceptance Scenarios**:

1. **Given** a validated `InvestmentThesis`, **When** the human-readable document is generated,
   **Then** it contains exactly the thesis's summary, supporting evidence, key assumptions, key
   risks, and invalidation conditions — no additional invented content.
2. **Given** the same `InvestmentThesis`, **When** the document is generated twice, **Then** both
   outputs are byte-identical (deterministic rendering).

---

### User Story 3 - Verify the Feature Without Calling the Real OpenAI API (Priority: P3)

A developer needs to run this feature's full test suite in CI without real network calls, real
API costs, or nondeterministic LLM output — the OpenAI dependency must be a swappable boundary.

**Why this priority**: Depends conceptually on Stories 1–2 already existing (there's nothing to
test in isolation otherwise), but is what makes the whole feature verifiable and trustworthy on
an ongoing basis.

**Independent Test**: Run the feature's test suite with a fake LLM provider standing in for
OpenAI and confirm it completes with zero real network calls.

**Acceptance Scenarios**:

1. **Given** a test double standing in for the OpenAI provider, **When** the full
   thesis-generation flow is exercised in a test, **Then** it completes with zero network calls to
   the real OpenAI API.
2. **Given** the test double returns a well-formed thesis payload, **When** the flow runs,
   **Then** the resulting `InvestmentThesis` validates successfully.
3. **Given** the test double returns a malformed payload, **When** the flow runs, **Then** it
   fails explicitly with a clear validation error.

---

### Edge Cases

- What happens when the `InvestmentCase` has zero `Evidence` entries? Thesis generation still
  proceeds — `supporting_evidence` is legitimately empty; assumptions and risks remain
  interpretive content and are not required to cite evidence.
- What happens when OpenAI is unreachable or times out? An explicit provider error is surfaced;
  no thesis is produced, fabricated, or partially returned.
- What happens when the LLM proposes evidence not present in the supplied input? Generation fails
  explicitly (see User Story 1, acceptance scenario 2).
- What happens when the OpenAI API key is not configured and a real (non-test-double) call is
  attempted? The feature fails explicitly with a clear configuration error before any network call
  is attempted.
- What happens when a supplied `DCFResult` doesn't actually correspond to the supplied
  `InvestmentCase` (e.g., a mismatched company)? This feature does not cross-validate that
  relationship — no linking identifier exists between the two in the current domain model, and
  ensuring the correct pairing is the caller's responsibility.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The feature SHALL accept an `InvestmentCase` and a `DCFResult` as input and
  assemble them into a single structured (typed, not a raw dictionary) research-context object
  for use by the thesis-generation step.
- **FR-002**: The feature SHALL use OpenAI as the LLM provider to synthesize the supplied
  evidence, financial data, and DCF result into an `InvestmentThesis` (summary, supporting
  evidence, key assumptions, key risks, invalidation conditions), reusing the existing
  `InvestmentThesis` domain contract unchanged.
- **FR-003**: The LLM call SHALL be made through a provider abstraction (protocol/interface) that
  can be substituted with a test double; this feature's own test suite SHALL require zero real
  network calls to OpenAI.
- **FR-004**: The LLM's raw response SHALL be validated against the `InvestmentThesis` schema
  before being trusted as application data; a response that fails validation SHALL be rejected
  with an explicit error, never partially accepted or silently coerced.
- **FR-005**: Every entry the LLM proposes for `supporting_evidence` SHALL be checked against the
  `Evidence` objects supplied in the input context; any entry not traceable to supplied evidence
  SHALL cause generation to fail explicitly, never be silently included or fabricated.
- **FR-006**: The feature SHALL NOT perform, request, or accept from the LLM any financial
  calculation (DCF values, ratios, or other valuation math) — DCF figures SHALL only be passed
  through as already-computed, read-only context from the existing DCF engine.
- **FR-007**: The feature SHALL NOT produce an investment recommendation (BUY/WATCH/AVOID), a
  `CommitteeDecision`, or a Bull/Bear `AnalysisAssessment` — those remain out of scope.
- **FR-008**: The feature SHALL NOT introduce LangGraph or any multi-agent orchestration — thesis
  generation is a single, direct research/synthesis step.
- **FR-009**: OpenAI API credentials SHALL be sourced only from the existing application
  settings/configuration mechanism — never hardcoded in source, never logged, never included in
  any generated output.
- **FR-010**: If OpenAI API credentials are not configured when a real (non-test-double) call is
  attempted, the feature SHALL fail explicitly with a clear configuration error before attempting
  any network call.
- **FR-011**: The feature SHALL deterministically render a validated `InvestmentThesis` into a
  human-readable document containing exactly its structured content — produced by Python code
  from the structured data, not by a second, independent LLM call.
- **FR-012**: Rendering the same `InvestmentThesis` into a document multiple times SHALL always
  produce an identical result.
- **FR-013**: The feature SHALL surface OpenAI provider errors (timeouts, rate limits, network
  failures) explicitly to the caller — never substituting a fabricated or default thesis when the
  provider call fails.
- **FR-014**: The feature SHALL perform no persistence (no database, no file writes) of the
  generated thesis or document — it returns the structured `InvestmentThesis` and the rendered
  document to its caller.

### Key Entities

- **ResearchContext**: The structured, typed bundle of an `InvestmentCase` and a `DCFResult`
  assembled as input to thesis generation.
- **InvestmentThesis**: The existing domain entity (summary, supporting evidence, key
  assumptions, key risks, invalidation conditions) — reused unchanged as this feature's structured
  output.
- **ThesisDocument**: The human-readable rendering of a validated `InvestmentThesis`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of successfully generated theses have every `supporting_evidence` entry
  traceable to the supplied input evidence — zero fabricated evidence ever appears.
- **SC-002**: 100% of thesis-generation attempts where the LLM response fails schema validation
  are rejected explicitly, with zero partially-formed thesis ever returned.
- **SC-003**: 100% of this feature's own automated tests run successfully with zero calls to the
  real OpenAI API.
- **SC-004**: Rendering the same structured thesis into a document produces an identical result
  100% of the time.
- **SC-005**: Zero financial calculations are performed by the LLM — every valuation figure used
  in a generated thesis originates solely from the supplied `DCFResult`.
- **SC-006**: Zero investment recommendation, Bull/Bear assessment, or committee-decision content
  is produced by this feature.
- **SC-007**: 100% of provider-error scenarios (timeout, rate limit, network failure) result in an
  explicit failure being surfaced, never a fabricated fallback thesis.

## Assumptions

- **`InvestmentThesis` is reused unchanged**: The source description mentions the LLM may
  synthesize "catalysts" among other inputs, but the explicit output list (evidence, assumptions,
  risks, invalidation conditions) matches the existing `InvestmentThesis` domain model from
  002-domain-model exactly. This feature does not add a new "catalysts" field — catalysts inform
  the narrative summary rather than becoming a new structured field, avoiding an unrequested
  schema change to an already-shipped domain model.
- **Human-readable document format**: Assumed to be Markdown, consistent with this project's
  existing documentation conventions (README, memos). Not stated explicitly; low-impact and
  easily revisable.
- **No retry/self-correction loop**: If the LLM's response fails schema or evidence-traceability
  validation, this feature fails fast with an explicit error rather than automatically retrying
  with a corrective prompt — the simplest correct MVP behavior, consistent with the constitution's
  minimal-architecture principle. A retry strategy can be added later without changing this
  feature's external contract.
- **No persistence in this feature**: Consistent with the constitution's "no premature
  infrastructure" guidance — the generated thesis and document are returned to the caller, not
  written to any store.
- **Settings extension**: The existing `aic.settings` configuration mechanism (from
  001-repository-bootstrap) gains an optional OpenAI API key setting, sourced from an environment
  variable following that feature's established naming convention — this is a natural extension
  of "the existing settings mechanism" the description explicitly requires, not a new pattern.
- **OpenAI/Pydantic named as requirement content, not implementation detail**: The provider
  (OpenAI) and the validation mechanism (Pydantic-based structured output validation) are treated
  as explicit requirements because the source description states them as hard requirements of
  this feature, consistent with how prior features in this project (001, 002, 003) treated
  explicitly-named tools as in-scope requirement content rather than incidental implementation
  choices.
- **No cross-validation between `DCFResult` and `InvestmentCase`**: No identifier links a
  `DCFResult` to the `InvestmentCase` it was computed for in the current domain model; ensuring a
  caller supplies a matching pair is out of scope for this feature.
