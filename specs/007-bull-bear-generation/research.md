# Phase 0 Research: Bull/Bear Analysis Generation

Every Technical Context item was resolvable from the spec (including its Assumptions
section), the constitution, and the existing 002/004/006 baselines. No open
`NEEDS CLARIFICATION` markers remain.

## Decision: A new `aic.bullbear` sub-package, reusing 004's provider abstraction verbatim

- **Decision**: Place `BullBearContext`, `AssessmentDraft`, `build_bull_prompt`,
  `build_bear_prompt`, `generate_bull_assessment`, and `generate_bear_assessment` in a new
  sibling sub-package `src/aic/bullbear/`. Import `LLMProvider`, `LLMCompletion`, and
  `OpenAIProvider` directly from `aic.research` rather than redefining them.
- **Rationale**: Identical rationale to 006's own decision — the provider protocol is
  already fully generic and schema-agnostic. Redefining it here would be pure duplication
  (Principle VIII). A new sub-package is still warranted because Bull/Bear generation is a
  distinct concern from thesis generation (004), report composition (005), and committee
  adjudication (006).
- **Alternatives considered**: Duplicating a second provider abstraction — rejected as
  unjustified duplication. Placing this inside `aic.committee` since 006 consumes this
  feature's output — rejected; 006 does not (and per its own spec, should not) depend on
  how its `bull_assessment`/`bear_assessment` inputs were produced, and this feature does
  not depend on `aic.committee` either. Keeping them as separate, independent packages
  preserves that decoupling.

## Decision: One shared `AssessmentDraft` schema for both roles — no richer per-role schema

- **Decision**: `AssessmentDraft` mirrors `AnalysisAssessment`'s own shape almost exactly
  (`conclusion`, `confidence`, `arguments`, `assumptions`, `risks`,
  `supporting_evidence_ids`). The same schema is used for both the Bull and the Bear call;
  role is enforced entirely by which prompt (`build_bull_prompt` vs. `build_bear_prompt`) is
  used, not by a schema difference.
- **Rationale**: Unlike 006's `CommitteeDecisionDraft` (which needed a separate required
  field per constitution-listed Committee Chair responsibility because the constitution
  enumerates that responsibility list explicitly), the constitution's Bull/Bear Symmetry
  principle only requires each agent to "argue the strongest credible upside/downside
  case" — it does not enumerate required sub-elements the way the Chair's responsibilities
  are listed. `AnalysisAssessment`'s existing `arguments`/`assumptions`/`risks` fields
  already have room for the spec's richer language (catalysts and outperformance
  conditions fold into `arguments` for Bull; adverse scenarios and invalidation conditions
  fold into `risks` for Bear) via prompt instruction, without needing a synthetic
  composition step the way 006's `_compose_rationale` was needed to guarantee constitution
  coverage.
- **Alternatives considered**: Separate `BullAssessmentDraft`/`BearAssessmentDraft` schemas
  with role-specific extra fields (e.g., `catalysts: list[str]`,
  `invalidation_conditions: list[str]`) — rejected; nothing in the constitution requires
  these as separately-verifiable structural elements the way it did for the Committee
  Chair, and `AnalysisAssessment` has no corresponding fields to receive them even if
  captured, so the added schema complexity would buy no additional code-verified guarantee
  — it would just be prompted-for content moved one layer earlier for no benefit.

## Decision: Two independent top-level functions, sharing only a private mechanics helper

- **Decision**: `generate_bull_assessment(context, provider)` and
  `generate_bear_assessment(context, provider)` are the two public entry points. Both
  internally call a private `_generate(context, provider, build_prompt_fn)` helper that
  performs the mechanical steps common to any role — call the provider, log cost/latency,
  validate the draft, resolve evidence references, construct the `AnalysisAssessment` — but
  neither public function ever calls the other, passes the other's output, or shares any
  in-flight state with the other.
- **Rationale**: FR-004 requires the two calls to be genuinely independent — sharing code
  that describes *how to process one already-role-specific prompt's completion* is not the
  same as sharing *content* between the two roles, and avoids duplicating the same five
  mechanical steps twice. The independence guarantee comes from each public function
  building its own prompt via its own role-specific `build_*_prompt` function and passing
  only that to its own `provider.complete_structured` call — nothing from one call's result
  is ever visible to the other's construction.
- **Alternatives considered**: A single `generate_assessment(context, provider, role)`
  function taking a role parameter — rejected; the spec explicitly asks for "two
  independent, structured AnalysisAssessments" via "separate LLM calls," and a single
  function taking a role enum reads as one operation with a mode switch rather than two
  independent operations, which is a weaker signal of the independence guarantee FR-004
  requires. Two clearly-named, separate public functions make the independence structurally
  obvious at the call site.

## Decision: Evidence references resolve to UUIDs, not full objects

- **Decision**: `AssessmentDraft.supporting_evidence_ids: list[UUID]` resolves against
  `context.investment_case.evidence`; the resolved, validated UUIDs populate
  `AnalysisAssessment.supporting_evidence: list[UUID]` directly.
- **Rationale**: Identical to 006's own decision for the same reason —
  `AnalysisAssessment.supporting_evidence` (002-domain-model) is already typed as
  `list[UUID]`, so no ID→object resolution is needed beyond the traceability check itself.
- **Alternatives considered**: None seriously considered; this is a straightforward reuse
  of an established, working pattern.

## Decision: Cost/latency measurement reuses 004's logging pattern, once per call

- **Decision**: The shared `_generate` helper logs one structured log line per LLM call
  (token usage, latency) via Python's standard `logging` module at `INFO` level — so both
  `generate_bull_assessment` and `generate_bear_assessment` each produce their own log
  entry, distinguishable by including the role in the log message.
- **Rationale**: This is the third agent-facing feature in the codebase (after 004 and
  006); reusing the proven logging pattern avoids inventing a fourth convention for the
  same constitutional requirement. Logging per-call (not once for "both calls together")
  keeps cost/latency attributable to the specific role that incurred it.
- **Alternatives considered**: A single combined log line covering both calls — rejected;
  it would obscure which call's tokens/latency belong to which role, weakening the
  constitution's own stated goal of answering "how much does one completed investment
  analysis cost?" at a useful granularity.

## Decision: Test file basenames are pre-qualified with `bullbear_`/`test_bullbear_` from the start

- **Decision**: Every file in `tests/unit/bullbear/` is named with a `bullbear`-specific
  basename from the first implementation pass (`bullbear_fakes.py`,
  `test_bullbear_context.py`, `test_bullbear_prompt.py`, `test_bullbear_generator.py`,
  `test_bullbear_no_network_dependency.py`) — not `fakes.py`/`test_context.py`/etc.
- **Rationale**: 006 discovered, only during its own Polish phase, that five identically-named
  files collided with `tests/unit/research/`'s files, because neither test directory is a
  Python package (pytest's "prepend" import mode requires globally-unique module basenames
  across non-package directories). That was caught and fixed after the fact in 006; this
  feature applies the lesson proactively instead of repeating the same rediscovery.
- **Alternatives considered**: Adding `__init__.py` to `tests/unit/` subdirectories to make
  cross-directory name reuse safe — rejected again, for the same reason 006 rejected it: a
  project-wide test-infrastructure change out of scope for a single feature.
