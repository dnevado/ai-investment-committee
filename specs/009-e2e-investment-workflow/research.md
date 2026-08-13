# Phase 0 Research: End-to-End Investment Committee Workflow & MVP Completion

Every Technical Context item was resolvable from the spec (including its Assumptions
section), the constitution, and the existing 002–008 baselines. No open
`NEEDS CLARIFICATION` markers remain.

## Decision: Orchestration is a plain function, not LangGraph

- **Decision**: `run_investment_workflow` is an ordinary Python function that calls each
  existing stage's own function in sequence. No LangGraph node, graph, or state machine is
  introduced.
- **Rationale**: The constitution's baseline technology list names LangGraph for
  orchestration, but CLAUDE.md's own staged MVP sequence places "LangGraph" (Iteration 8)
  and "First vertical slice" (Iteration 9, this feature) as distinct steps — this feature is
  explicitly the vertical slice, not the graph-orchestration step. The spec's own exclusion
  of "multi-agent orchestration beyond the existing sequential workflow" and "autonomous
  agents" reinforces that a single deterministic call sequence is exactly what's being
  asked for here, not a graph runtime.
- **Alternatives considered**: Introducing a minimal LangGraph graph now — rejected as
  premature infrastructure (Principle VIII) for a sequence with no branching, no
  human-in-the-loop step, and no need for graph-level state persistence; a graph would add a
  new dependency and a new execution model for no behavioral gain over five sequential
  function calls.

## Decision: The spec's illustrative pipeline order is corrected to match already-built dependencies

- **Decision**: The actual stage order is: DCF (003) → research/thesis generation (004) →
  Bull/Bear generation (007) → committee adjudication (006) → report composition (005) — DCF
  first, not third as the spec's own arrow-diagram lists it.
- **Rationale**: `aic.research.ResearchContext` (004) requires an already-computed
  `DCFResult` as its own required field, and `aic.bullbear.BullBearContext` (007) requires an
  already-computed `ValuationResult` (derived from that same `DCFResult`) as its own required
  field. Neither can be constructed before a DCF computation exists. This is not a design
  choice this feature is free to make differently — it is dictated by contracts already
  shipped and, per the spec's own instruction not to introduce new investment-analysis
  logic, not something this feature will change.
- **Alternatives considered**: None — there is no version of this workflow that respects
  every already-shipped stage's own required-input contract other than valuation-first.

## Decision: A transient placeholder thesis, replaced immediately after research runs

- **Decision**: Before research/thesis generation runs, the orchestrator constructs an
  initial `InvestmentCase` with a fixed placeholder `InvestmentThesis(summary="Pending
  research")` — the only value `InvestmentCase.thesis` (a required field) can hold before a
  real thesis exists. Immediately after `generate_thesis` returns, the orchestrator produces
  an updated `InvestmentCase` (via `model_copy(update={"thesis": ...})`) carrying the real,
  generated thesis, and every later stage (Bull/Bear, committee, report) receives only this
  updated case.
- **Rationale**: `InvestmentCase.thesis` has no default and no `| None` — some value must
  exist to construct the case at all before research has produced the real one. Pydantic
  models in this codebase are treated as immutable value objects (no in-place mutation
  pattern exists anywhere in `aic.domain`), so `model_copy(update=...)` — not attribute
  assignment — is the established way to produce an updated instance.
- **Alternatives considered**: Making `InvestmentCase.thesis` optional so no placeholder is
  needed — rejected; that would be a real, behavior-changing modification to an
  already-shipped 002-domain-model contract, for the sake of a purely internal
  implementation detail of this one new orchestrator function. Passing the thesis
  separately from the case into every downstream stage instead of updating the case —
  rejected; every downstream context type (`BullBearContext`, `CommitteeAdjudicationContext`,
  `CommitteeReport`) already expects a complete `InvestmentCase` (or the specific fields it
  carries) exactly as those features shipped it, not a case-plus-separate-thesis pair.

## Decision: The valuation-summary confidence value is a fixed constant; the valuation date is the latest financial snapshot's date

- **Decision**: `to_valuation_result(dcf_result, valuation_id=uuid4(), valuation_date=<latest
  financial_snapshot.as_of>, confidence=1.0, ...)` is called once per workflow run to derive
  the `ValuationResult` that Bull/Bear generation (007) requires. `confidence=1.0` is a fixed
  constant; `valuation_date` is the most recent of the supplied financial snapshots' `as_of`
  dates (or, with exactly one snapshot, that snapshot's own date).
- **Rationale**: `to_valuation_result`'s `confidence` parameter describes confidence in the
  *valuation calculation*, which is deterministic and therefore carries no computational
  uncertainty of its own — `1.0` is the honest value for "this number is exactly what the
  formula produces given the supplied assumptions," distinct from the qualitative investment
  confidence Bull/Bear/committee narratives separately express. `valuation_date` should
  represent what date the valuation reflects, not when the calculation happened to run — the
  latest supplied financial snapshot's date is the closest available proxy already present
  in the input, avoiding a dependency on wall-clock time (which would make otherwise-identical
  workflow runs produce different `ValuationResult`s on different days, undermining
  reproducibility in tests).
- **Alternatives considered**: Using `datetime.now()`/`date.today()` for `valuation_date` —
  rejected; it would make the workflow's output nondeterministic across otherwise-identical
  runs, and this project has already fixed exactly this class of bug once (the
  `scripts/mvp_validation.py` `date.today()` → `datetime.now(UTC).date()` question raised
  during earlier `ruff` fixes was a different DTZ concern, but the underlying "avoid
  wall-clock nondeterminism" principle is the same one applied here). Accepting `confidence`
  as a required `WorkflowInput` field instead of a fixed constant — rejected as unnecessary
  API surface for a value that has exactly one correct, deterministic answer given how it is
  actually used ("how exact is this arithmetic," not "how confident is the analyst").

## Decision: `CommitteeReport` gains two additive, optional fields — `bull_assessment` and `bear_assessment`

- **Decision**: `CommitteeReport` (005) gains `bull_assessment: AnalysisAssessment | None =
  None` and `bear_assessment: AnalysisAssessment | None = None`. The existing `assessment:
  AnalysisAssessment` field is left required and unchanged; the workflow populates it with
  the Bull assessment (a fixed, documented choice — see below) in addition to populating the
  two new fields with the full Bull/Bear pair. `render_report_document` (005) renders two
  distinct labeled sections ("Bull Case Assessment" / "Bear Case Assessment") when both new
  fields are present; when they are absent (every pre-existing caller and test), it renders
  its exact pre-existing single "Committee Assessment" section from `assessment`, unchanged.
- **Rationale**: This is the Constitution Check's "Gap found" row. `CommitteeReport` (005)
  predates Bull/Bear (007) as a concept in this codebase and was designed around one generic
  assessment; this workflow is the first caller that actually has two independent
  assessments to report. Passing only one into the existing field would silently discard the
  other from the final artifact — a real information-loss bug in a report whose whole point
  is showing both sides of the investment case. An additive change satisfies FR-016 (no
  existing test's assertions change, since `render_report_document`'s behavior is identical
  whenever the two new fields are absent) while still fully representing the workflow's own
  output (SC-001).
- **Alternatives considered**: Renaming/replacing `assessment` with `bull_assessment`/
  `bear_assessment` — rejected; breaks every existing 005 test and caller that constructs
  `CommitteeReport(assessment=...)`, directly violating FR-016. Passing only the Bull
  assessment and dropping the Bear assessment from the report entirely — rejected as a real
  functional regression relative to what the assembled MVP should deliver, not a
  defensible simplification. Introducing a wholly new `CommitteeReport`-like type specific
  to this workflow instead of extending the existing one — rejected; would duplicate
  005's already-correct company/financial-snapshot/thesis/DCF/decision handling for no
  benefit, and 005's `render_report_document` would need a sibling duplicate too.
- **Why the Bull assessment specifically fills the legacy `assessment` field**: An arbitrary
  but fixed, documented choice was needed since the field is singular and required;
  Bull is chosen only for consistency (it is generated first in the workflow's own sequence)
  — no significance should be read into which side "wins" the legacy field, since both are
  always fully present via the two new fields whenever this workflow is the caller.

## Decision: Each stage's own exception propagates unchanged; the orchestrator introduces no new error type

- **Decision**: `run_investment_workflow` does not catch, wrap, or translate any exception
  raised by `compute_dcf`, `generate_thesis`, `generate_bull_assessment`,
  `generate_bear_assessment`, or `generate_decision`. Whatever each already raises today
  (`pydantic.ValidationError`, `ValueError` for untraceable evidence, a provider's own
  error type for network/timeout failures) propagates to the orchestrator's caller
  unmodified.
- **Rationale**: Every existing stage already raises clear, well-typed, well-tested errors
  on failure (FR-011's "halt immediately with an explicit error" is already satisfied by
  each stage's own existing behavior). Introducing a new `WorkflowError` wrapper would add
  an abstraction with no behavioral benefit — Principle VIII — and would obscure exactly
  which underlying stage and failure mode a caller is looking at, the opposite of what
  Traceability (Principle VII) asks for.
- **Alternatives considered**: A unifying `WorkflowError` exception wrapping the original
  cause — rejected as unnecessary indirection for a codebase where every stage's own error
  types are already specific and already tested.

## Decision: `src/aic/agents/prompts/*.md` is removed, not reconciled in place

- **Decision**: The entire `src/aic/agents/` directory (five prompt scaffold files:
  `bear.md`, `bull.md`, `committee.md`, `research.md`, `valuation.md`) is deleted.
- **Rationale**: A repository-wide search confirms zero imports or references to
  `aic.agents` or `agents/prompts` anywhere in `src/` or `tests/` — this scaffolding predates
  004/006/007's actual, independently-designed prompt-construction logic (each of which
  defines its own prompt strings inline in its own `prompt.py`, with materially different
  output schemas than what these files describe) and was never wired to any of it. Leaving
  it in place is exactly the "parallel unused architecture" the spec explicitly asks this
  feature to avoid; deleting it is lower-risk than trying to reconcile content that no code
  path ever reads.
- **Alternatives considered**: Rewriting these files to match the actually-implemented
  prompts and wiring `aic.research`/`aic.bullbear`/`aic.committee` to read from them instead
  of their own inline strings — rejected as a large, risky refactor of three already-shipped,
  already-tested features for a purely cosmetic consistency benefit, and explicitly outside
  this feature's own scope ("must not introduce new investment-analysis logic," "avoid...
  duplicating business logic"). Leaving the files in place with a comment marking them
  historical — rejected; still satisfies "unused" but not "not a parallel architecture," and
  a comment is easy to miss relative to the file's own absence.
