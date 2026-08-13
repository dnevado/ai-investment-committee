# Phase 0 Research: Investment Committee Decision Engine

Every Technical Context item was resolvable from the spec (including its Assumptions
section), the constitution, and the existing 002/003/004/005 baselines. No open
`NEEDS CLARIFICATION` markers remain.

## Decision: A new `aic.committee` sub-package, reusing 004's provider abstraction verbatim

- **Decision**: Place `CommitteeAdjudicationContext`, `CommitteeDecisionDraft`,
  `build_prompt`, and `generate_decision` in a new sibling sub-package
  `src/aic/committee/`. Import `LLMProvider`, `LLMCompletion`, and `OpenAIProvider` directly
  from `aic.research` rather than redefining them.
- **Rationale**: The provider protocol 004 built (`complete_structured(*, system_prompt,
  user_prompt, schema) -> LLMCompletion`) is already fully generic — it is not coupled to
  `ThesisDraft` or any other schema. Redefining an equivalent protocol/adapter in
  `aic.committee` would be pure duplication, violating Principle VIII (no premature
  infrastructure / avoid unnecessary complexity) for zero behavioral gain. A new
  sub-package is still warranted for what genuinely differs: the adjudication context, the
  LLM-facing draft schema, prompt construction, and the orchestration logic that resolves
  evidence and composes the final decision.
- **Alternatives considered**: Duplicating a second `LLMProvider`/`OpenAIProvider` local to
  `aic.committee` — rejected as unjustified duplication. Placing this feature's code inside
  `aic.research` itself — rejected; `aic.research` is scoped to thesis generation per
  004's own design, and mixing a second, differently-shaped agent's orchestration into the
  same package would blur its single responsibility.

## Decision: `CommitteeDecisionDraft` gets a separate required field per constitution-listed Chair responsibility

- **Decision**: Rather than one free-text `rationale` field, `CommitteeDecisionDraft`
  requires: `central_thesis: str`, `key_disagreements: list[str]`,
  `valuation_summary: str`, `downside_risks: list[str]`, `invalidation_conditions: list[str]`,
  `recommendation: Recommendation`, `confidence: float` (0–1), `dissent: list[str]`, and
  `supporting_evidence_ids: list[UUID]`. `generate_decision` deterministically composes the
  final `CommitteeDecision.rationale` string from `central_thesis`, `key_disagreements`,
  `valuation_summary`, `downside_risks`, and `invalidation_conditions` — Python, not the
  LLM, guarantees every constitution-listed element is present in the output.
- **Rationale**: The constitution requires the Committee Chair to "identify the central
  investment thesis, supporting evidence, assumptions, disagreements, valuation, downside
  risks, and invalidation conditions" before deciding — a MUST that a single opaque
  `rationale` string cannot make code-verifiable (nothing stops an LLM from writing a
  rationale that skips one of these elements while still "sounding" complete). Structured,
  required, separately-validated fields make omission a schema-validation failure (FR-004)
  instead of an unenforceable prompting convention, directly satisfying the constitution's
  "Structured Outputs Only" principle (III) applied to this specific MUST.
- **Alternatives considered**: A single free-text `rationale` field with prompt instructions
  to cover all elements — rejected; matches the constitution's letter loosely but not its
  verifiability spirit, and is exactly the failure mode Principle III exists to prevent.
  Adding these fields directly to the domain `CommitteeDecision` model — rejected; the
  spec's own Assumptions (and 004/005's precedent) require reusing `CommitteeDecision`
  unchanged, and `rationale`/`dissent` are already sufficient output surface for a domain
  consumer — the richer structure is only needed transiently, at the LLM-facing boundary.

## Decision: Evidence references resolve to UUIDs, not full objects

- **Decision**: `CommitteeDecisionDraft.supporting_evidence_ids: list[UUID]` resolves
  against `context.investment_case.evidence`; the resolved, *validated* UUIDs (not full
  `Evidence` objects) populate `CommitteeDecision.referenced_evidence: list[UUID]`.
- **Rationale**: Unlike `InvestmentThesis.supporting_evidence: list[Evidence]` (004's
  target field, which forced ID→object resolution), `CommitteeDecision.referenced_evidence`
  is already typed as `list[UUID]` in the existing domain model (002). No resolution beyond
  "is this ID present in the supplied investment case's evidence" is needed — a simpler,
  smaller version of 004's same traceability mechanism (research.md "Evidence-by-reference"
  decision), reused here because the target schema is already a plain ID list.
- **Alternatives considered**: Resolving to full `Evidence` objects and discarding them —
  rejected as pointless extra work; `CommitteeDecision`'s own field shape doesn't need it.

## Decision: `valuation_reference` is left unset

- **Decision**: `CommitteeDecision.valuation_reference` (an optional `UUID` pointing at a
  domain `ValuationResult`) is left `None` by this feature.
- **Rationale**: This feature's valuation input is a `DCFResult` (003), which has no
  identity of its own. Minting a `ValuationResult` (via the existing
  `aic.dcf.to_valuation_result` helper) purely to generate a UUID for a reference nothing
  else stores or looks up would be reference-to-nowhere complexity with no corresponding
  spec requirement — a violation of Principle VIII, not a fulfillment of it. If a future
  feature introduces `ValuationResult` persistence/lookup, wiring this reference through
  becomes straightforward without changing `CommitteeDecision` itself.
- **Alternatives considered**: Calling `to_valuation_result` and assigning a fresh UUID
  regardless — rejected as premature, purposeless infrastructure.

## Decision: Cost/latency measurement reuses 004's logging pattern

- **Decision**: `generate_decision` logs one structured log line per adjudication (token
  usage, latency) via Python's standard `logging` module at `INFO` level — identical
  mechanism to 004's `generate_thesis`.
- **Rationale**: This is the second agent-facing (LLM-calling) feature in the codebase; the
  constitution's cost/latency-measurement MUST already has a proven, minimal resolution from
  004. Reusing it verbatim avoids inventing a second logging convention for the same
  constitutional requirement.
- **Alternatives considered**: None seriously considered — 004's resolution generalizes
  directly with no adaptation needed.

## Decision: `FakeLLMProvider` is duplicated locally, not imported across test directories

- **Decision**: `tests/unit/committee/committee_fakes.py` defines its own `FakeLLMProvider`,
  structurally identical to `tests/unit/research/fakes.py`'s. Every test module in
  `tests/unit/committee/` whose basename would otherwise collide with an identically-named
  module in `tests/unit/research/` (`fakes.py`, `test_context.py`, `test_prompt.py`,
  `test_generator.py`, `test_no_network_dependency.py`) was given a `committee`-qualified
  name instead (`committee_fakes.py`, `test_committee_context.py`,
  `test_committee_prompt.py`, `test_committee_generator.py`,
  `test_committee_no_network_dependency.py`) during implementation, once `pytest`'s
  collection actually surfaced every collision — not just the `fakes.py` one anticipated
  here at planning time.
- **Rationale**: Neither `tests/unit/research/` nor `tests/unit/committee/` is a Python
  package (no `__init__.py`, consistent with this project's established pytest
  "prepend"-import-mode convention — see 004/005's own precedent and the
  `test_document.py`/`test_report_document.py` naming-collision fix in 005). Cross-directory
  imports between non-package test directories are fragile; small, duplicated, distinctly-named
  fixtures/tests are simpler and more robust than introducing `__init__.py` files
  project-wide just to share ~20 lines of test-only code.
- **Alternatives considered**: Adding `__init__.py` to `tests/unit/` subdirectories to make
  `fakes.py` importable across them — rejected as a project-wide test-infrastructure change
  out of scope for this feature, with its own risk of subtly changing pytest's collection
  behavior for every existing test module.
