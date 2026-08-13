# Feature Specification: End-to-End Investment Committee Workflow & MVP Completion

**Feature Branch**: `009-e2e-investment-workflow`

**Created**: 2026-08-13

**Status**: Draft

**Input**: User description: "Complete the end-to-end investment analysis workflow by integrating the existing research, investment thesis, bull/bear assessment, DCF valuation, committee adjudication, and report capabilities into one coherent MVP flow. The implementation must reuse the existing domain models, services, generators, LLM provider abstraction, DCF engine, committee decision logic, and report renderer. It must not introduce new investment-analysis logic where equivalent functionality already exists. Scope includes: defining the end-to-end orchestration; ensuring stage outputs pass correctly to the next stage; ensuring the final CommitteeDecision is represented in the CommitteeReport; preserving DCF/valuation information through committee and report layers; resolving inconsistencies between existing models and integration points without duplicating business logic; preserving evidence traceability throughout; failing explicitly on provider failures or invalid intermediate results; keeping the no-network unit-test architecture; adding end-to-end tests with fake providers; preserving all existing unit-test coverage and domain invariants; and reconciling existing agent/prompt definitions with the implemented architecture, avoiding a parallel unused architecture. Out of scope: new research/data providers, web scraping, new DCF/valuation methodology, portfolio management, backtesting, UI, persistence, autonomous agents, multi-agent orchestration beyond the existing sequential workflow, and new LLM provider implementations. Definition of Done: a complete investment case can be passed through the MVP workflow and produce a validated, evidence-backed CommitteeDecision and final CommitteeReport using only existing application components and fake providers in tests, testable end-to-end without network access."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Run the Complete Investment Workflow End-to-End (Priority: P1)

A developer closing out the MVP needs to take a company's raw inputs (profile, financial
snapshot(s), evidence, and DCF assumptions) and get back a validated, evidence-backed
committee report and its rendered document — without manually constructing and wiring
together the intermediate context objects each existing stage (research, DCF, Bull/Bear,
committee, report) already requires.

**Why this priority**: This is the MVP's defining deliverable — the single reason every
prior feature (002 through 008) exists is to eventually compose into exactly this. Without
it, the MVP is a set of working parts that nothing has ever actually assembled.

**Independent Test**: Supply a company, financial snapshot(s), evidence, and DCF
assumptions, plus a test-double LLM provider, to the workflow, and confirm it returns a
validated `CommitteeReport` and rendered document whose thesis, evidence, valuation
figures, Bull/Bear content, and committee decision are all mutually consistent — with the
single underlying DCF computation used everywhere it appears.

**Acceptance Scenarios**:

1. **Given** a complete company, financial snapshot(s), evidence, and DCF assumptions, plus
   a test-double provider, **When** the workflow is run, **Then** it returns a validated
   `CommitteeReport` and a rendered document, with no manual assembly step required by the
   caller.
2. **Given** the workflow has run, **When** the resulting report is inspected, **Then**
   every valuation figure it displays (enterprise value, equity value, implied value per
   share) traces to the single DCF computation the workflow performed — none is
   recomputed or introduced by any later stage.
3. **Given** the workflow has run, **When** the resulting report is inspected, **Then**
   every supporting-evidence reference anywhere in it (thesis, Bull/Bear content,
   committee decision) traces back to the evidence originally supplied — none is
   fabricated or lost between stages.
4. **Given** the workflow has run, **When** the resulting committee decision is inspected,
   **Then** its valuation reference identifies the same underlying valuation used
   throughout the rest of the report, and the report itself correctly represents that
   decision (recommendation, rationale, dissent).

---

### User Story 2 - Fail Explicitly and Stop the Pipeline When Any Stage Fails (Priority: P2)

The same developer needs to trust that if research, Bull, Bear, or committee adjudication
fails partway through — a provider error or an invalid intermediate result — the workflow
stops there and never produces a report built on a fabricated or missing piece.

**Why this priority**: Depends on Story 1's happy path already existing, but is what makes
the assembled workflow trustworthy rather than merely functional — a silently-degraded
report would be worse than no report at all.

**Independent Test**: Configure a test-double provider to fail (or return an
invalid/unvalidatable response) at each stage in turn, and confirm the workflow halts
immediately with an explicit error and produces no report in every case.

**Acceptance Scenarios**:

1. **Given** the DCF assumptions themselves are invalid, **When** the workflow is run,
   **Then** it fails explicitly at the DCF stage, before any LLM call is ever made.
2. **Given** the research/thesis stage's provider call fails or returns an invalid
   response, **When** the workflow is run, **Then** it halts immediately — no Bull, Bear,
   committee, or report stage is ever attempted.
3. **Given** the research and Bull stages succeed but the Bear stage fails, **When** the
   workflow is run, **Then** it halts immediately — no committee or report stage is ever
   attempted, and no partial report is produced.
4. **Given** research, Bull, and Bear all succeed but the committee adjudication stage
   fails, **When** the workflow is run, **Then** it halts immediately — no report is ever
   produced from the otherwise-complete upstream results.

---

### User Story 3 - Verify the Complete Workflow Without Calling Real External Providers (Priority: P3)

A developer needs to run this feature's end-to-end tests, and the entire pre-existing test
suite, in CI without real network calls, real API costs, or nondeterministic LLM output —
and needs confidence that assembling the workflow did not silently change or break any
already-shipped stage's own behavior.

**Why this priority**: Depends conceptually on Stories 1–2 already existing, but is what
makes the assembled MVP verifiable and safe to keep building on.

**Independent Test**: Run this feature's end-to-end test suite with a fake LLM provider
standing in for every stage that would otherwise call OpenAI, and confirm it completes
with zero real network calls; run the complete pre-existing test suite and confirm every
test that passed before this feature still passes, unmodified in behavior.

**Acceptance Scenarios**:

1. **Given** a test double standing in for the LLM provider, **When** the complete
   workflow is exercised in a test, **Then** it completes with zero network calls to any
   real external provider.
2. **Given** the complete pre-existing test suite (every test that existed before this
   feature), **When** it is run after this feature is implemented, **Then** every test
   still passes with no change to its own assertions.

---

### Edge Cases

- What happens when the DCF assumptions alone are invalid (e.g., WACC not exceeding the
  terminal growth rate)? The workflow fails at the DCF stage itself, before any LLM call is
  made (see User Story 2, acceptance scenario 1).
- What happens when the Bull and Bear assessments succeed but disagree materially? The
  workflow proceeds normally — that disagreement is exactly what the committee adjudication
  stage is designed to weigh; the workflow does not intervene in or pre-resolve it.
  Bull and Bear generation remain two independent calls, as already established by
  007-bull-bear-generation.
- What happens when the caller supplies zero evidence? The workflow still proceeds; every
  stage that already accepts empty evidence continues to do so, and the report's evidence
  sections are legitimately empty.
- What happens to the transient placeholder thesis needed to construct the initial
  investment case before research has run? It exists only inside the workflow's own
  execution and is never exposed in the final report — every stage after research receives
  the investment case populated with the actually-generated thesis, not the placeholder.
- What happens to the existing, currently-unused prompt scaffolding under
  `aic/agents/prompts/`? This feature reviews it against the prompt-construction logic each
  already-implemented stage actually uses, and resolves the inconsistency rather than
  leaving two divergent, parallel prompt-definition mechanisms in the repository (FR-017).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The feature SHALL provide a single orchestration entry point that accepts a
  company, its financial snapshot(s), its evidence, DCF assumptions, and an LLM provider,
  and runs the complete workflow (valuation → research → Bull/Bear → committee → report)
  without requiring the caller to manually construct or wire any intermediate stage's
  context object.
- **FR-002**: The workflow SHALL compute the deterministic DCF valuation before invoking
  any stage that depends on it — both research/thesis generation and Bull/Bear generation
  require an already-computed valuation as their own input.
- **FR-003**: The workflow SHALL generate the investment thesis via the existing
  research/thesis-generation capability, using the computed DCF result as its valuation
  context, and SHALL use the generated thesis — not a placeholder — for every subsequent
  stage that needs one.
- **FR-004**: The workflow SHALL derive the valuation summary the Bull/Bear stage requires
  from the same DCF result, using the existing conversion capability between the DCF
  engine's result type and the domain-level valuation summary type, rather than
  introducing a new conversion.
- **FR-005**: The workflow SHALL generate the Bull and Bear assessments via the existing
  Bull/Bear-generation capability, using the generated thesis and the derived valuation
  summary as context, as two independent calls (unchanged from the existing guarantee).
- **FR-006**: The workflow SHALL adjudicate a final committee decision via the existing
  committee-decision capability, using the generated thesis, the computed DCF result, and
  both the Bull and Bear assessments as context.
- **FR-007**: The workflow SHALL compose the final structured report and its rendered
  document via the existing report-composition capability, using the company, financial
  snapshot(s), generated thesis, computed DCF result, a committee assessment, and the
  adjudicated decision.
- **FR-008**: Every supporting-evidence reference produced by any stage (thesis, Bull,
  Bear, committee decision) SHALL remain traceable to the evidence originally supplied to
  the workflow — the workflow SHALL NOT introduce, substitute, or lose evidence between
  stages.
- **FR-009**: Every valuation figure shown anywhere in the final report SHALL trace to the
  single DCF computation performed by the workflow — no stage SHALL recompute, override,
  or introduce a second, independent valuation.
- **FR-010**: The workflow SHALL set the final committee decision's valuation reference to
  the identifier of the valuation summary it derived from the DCF result, closing the
  previously-unfilled link between the committee decision and the underlying valuation.
- **FR-011**: If any stage's provider call fails (timeout, rate limit, network failure) or
  produces a response that fails validation, the workflow SHALL halt immediately with an
  explicit error — it SHALL NOT continue to any subsequent stage, and SHALL NOT produce a
  partial or fabricated report.
- **FR-012**: The workflow SHALL NOT introduce any new financial calculation, valuation
  methodology, or investment-analysis logic beyond what the existing DCF engine, research,
  Bull/Bear, and committee capabilities already provide.
- **FR-013**: The workflow SHALL NOT introduce a new LLM provider abstraction — it SHALL
  reuse the existing provider protocol and pass a single provider instance to every stage
  that needs one.
- **FR-014**: The workflow SHALL NOT introduce persistence, a UI, an API, autonomous
  agents, or multi-agent orchestration beyond the existing sequential stage sequence.
- **FR-015**: This feature's own test suite SHALL exercise the complete pipeline using
  test-double providers, with zero real network calls, consistent with the existing
  no-network unit-test architecture.
- **FR-016**: Every test that existed before this feature SHALL continue to pass with no
  change to its own assertions, demonstrating this feature introduces no regression to any
  existing stage's own contract.
- **FR-017**: The feature SHALL review the existing, currently-unused prompt scaffolding
  (standalone prompt text predating the implemented research/Bull-Bear/committee prompt
  logic) against the prompt-construction logic each stage actually uses, and SHALL resolve
  the inconsistency (for example, by removing the superseded scaffolding) rather than
  leaving two divergent, parallel prompt-definition mechanisms in the repository.

### Key Entities

- **WorkflowInput**: The bundle of raw starting inputs a caller supplies to begin the
  workflow — a company, its financial snapshot(s), its evidence, and DCF assumptions.
- **WorkflowResult**: The bundle of everything the workflow produces — the computed
  valuation, the generated thesis, the Bull and Bear assessments, the committee decision,
  the final structured report, and its rendered document — exposed together so that a
  caller (or a test) can inspect any stage's output, not only the final report.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of successfully completed workflow runs produce a `CommitteeReport`
  whose evidence, thesis, valuation figures, Bull/Bear content, and committee decision are
  all internally consistent with the single DCF computation and the originally-supplied
  evidence — zero manual reassembly required by the caller.
- **SC-002**: 100% of workflow runs where any stage's provider fails or returns an invalid
  response halt explicitly before producing any report — zero fabricated or partial
  reports are ever returned.
- **SC-003**: 100% of this feature's own end-to-end tests run successfully with zero calls
  to any real external provider.
- **SC-004**: 100% of the test suite that existed before this feature continues to pass,
  unmodified in behavior.
- **SC-005**: 100% of completed workflow runs produce a committee decision whose valuation
  reference correctly identifies the valuation summary derived from the same DCF
  computation used throughout the rest of the report.
- **SC-006**: Zero new financial calculations, valuation methodologies, or provider
  abstractions are introduced by this feature.

## Assumptions

- **Orchestration is a plain, deterministic function pipeline, not a new agent framework**:
  Consistent with this project's own staged roadmap (multi-agent orchestration is a later,
  not-yet-reached iteration) and the explicit instruction to introduce no autonomous agents
  or multi-agent orchestration beyond the existing sequential sequence, "orchestration" here
  means a single Python entry point that calls each existing stage's own function in the
  correct order — not a new framework, graph, or agent runtime.
- **The request's illustrative pipeline order is corrected to match already-built
  dependencies**: The source description's arrow-diagram lists Bull/Bear before DCF and
  research immediately after the investment case (before any valuation exists). The
  already-implemented stages require the opposite order — both research/thesis generation
  (004) and Bull/Bear generation (007) require an already-computed valuation as their own
  input. This is exactly the kind of "inconsistency between existing models and integration
  points" the request asks this feature to resolve; the corrected order (valuation first) is
  the only one consistent with contracts already shipped in 003, 004, 006, and 007, so it is
  adopted without treating it as an open question.
- **A single LLM provider instance is reused across every stage that calls one**: Research
  (thesis), Bull generation, Bear generation, and committee adjudication all already depend
  on the identical existing provider protocol; the workflow passes one instance to all four
  rather than accepting one per stage, consistent with "no new provider abstraction."
- **The transient placeholder thesis is an internal implementation detail, not a new
  requirement on the caller**: Constructing the initial investment case (before research has
  run) needs some thesis value, since the domain model requires one; the caller does not
  supply this placeholder, and it never appears in the final report.
- **The valuation summary's confidence value, needed only to satisfy the existing
  DCF-result-to-valuation-summary conversion's own required parameter, is a fixed,
  documented value** (reflecting that the deterministic calculation itself carries no
  uncertainty) unless a caller explicitly wants to override it — this is a narrow
  technical-bridging detail, not a new judgment the workflow introduces.
