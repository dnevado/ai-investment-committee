# Phase 0 Research: Investment Committee Report

Every Technical Context item was resolvable from the spec (including its Assumptions
section), the constitution, and the existing 002/003/004 baselines. No open
`NEEDS CLARIFICATION` markers remain.

## Decision: A new `aic.report` sub-package

- **Decision**: Place `CommitteeReport` and `render_report_document` in a new sibling
  sub-package `src/aic/report/`, not inside `aic.domain`, `aic.dcf`, or `aic.research`.
- **Rationale**: `aic.domain` is pure, computation-free data; `aic.dcf` is pure,
  deterministic calculation; `aic.research` orchestrates an external LLM call. This
  feature is a fourth, distinct concern — read-only composition and deterministic
  rendering of already-produced entities from all three prior packages — and keeping it
  separate preserves each existing package's own invariant untouched.
- **Alternatives considered**: Adding `CommitteeReport` inside `aic.domain` — rejected;
  `aic.domain` models are simple data holders defined once in 002-domain-model, and this
  feature's composition is a distinct, later-arriving concern that spans `domain`, `dcf`,
  and (indirectly) `research` outputs, not a new primitive domain entity of its own. Adding
  it inside `aic.research` — rejected; this feature makes no LLM call and has nothing to do
  with provider orchestration.

## Decision: `CommitteeReport` is a direct, validated Pydantic bundle — no separate "assemble" function

- **Decision**: `CommitteeReport` is constructed directly from its required fields; there is
  no separate `assemble_report(...)` service function.
- **Rationale**: Mirrors 004-investment-research-thesis's own `ResearchContext` precedent —
  a required-fields-only Pydantic model whose own construction *is* the composition step.
  Pydantic's required-field validation is exactly the "fail explicitly on a missing input"
  mechanism FR-007/FR-014 call for; a wrapper function would add no behavior beyond what the
  model's own `__init__` already provides, which the constitution's minimal-architecture
  principle (VIII) counsels against.
- **Alternatives considered**: A dedicated `assemble_report(...)` function — rejected as an
  unnecessary indirection layer for what is, structurally, just model construction; nothing
  in the spec requires assembly-time logic beyond "all required fields present and valid."

## Decision: `DCFResult` (003) is the sole valuation figure source

- **Decision**: `CommitteeReport` composes the `DCFResult` produced by
  `aic.dcf.compute_dcf`, not the domain-level `ValuationResult` summary type.
- **Rationale**: FR-010 explicitly names "the existing deterministic DCF engine
  (003-dcf-valuation-engine)" as the sole origin of every valuation figure in the report.
  `DCFResult` carries the full detail (per-year FCFF, terminal value, enterprise value,
  equity value, implied value per share) the spec's "present the DCF valuation" requirement
  calls for. Including both `DCFResult` and the domain `ValuationResult` risked two
  possibly-divergent valuation representations in one report — a traceability hazard the
  constitution's Principle VII explicitly warns against ("must avoid presenting generated
  information as sourced information" / no silent mixing).
- **Alternatives considered**: Composing the domain `ValuationResult` instead (or in
  addition) — rejected; `ValuationResult` is a single-figure summary designed for
  `CommitteeDecision.valuation_reference` cross-referencing, not for presenting full DCF
  detail, and adding both types risked inconsistency with no corresponding spec requirement
  asking for it.

## Decision: No new LLM call — rendering is pure Python

- **Decision**: `render_report_document` is a pure, deterministic Python function. Any
  narrative text it displays (thesis summary, assessment conclusion, decision rationale)
  is whatever was already produced by the entities supplied to `CommitteeReport` — this
  feature does not call an LLM itself.
- **Rationale**: The spec's own Assumptions section resolves "the LLM may generate
  human-readable narrative where appropriate" as permissive, not mandatory, favoring the
  constitution's minimal-architecture principle and the request's own instruction to keep
  the MVP free of unnecessary infrastructure. Reusing 004's already-built
  `generate_thesis`/`OpenAIProvider` machinery for a *second*, report-level LLM call would
  duplicate orchestration this feature has no independent need for.
- **Alternatives considered**: Introducing a report-level LLM narrative pass on top of the
  composed content — rejected as premature infrastructure for the MVP; nothing in the
  spec's Functional Requirements or Success Criteria demands narrative synthesis beyond
  presenting what was already produced.

## Decision: Document format and dissent rendering

- **Decision**: The rendered document is Markdown, following 004's established convention.
  `CommitteeDecision.dissent` is reused unchanged (`list[str]`); the renderer prints each
  entry when present, or an explicit "No dissent recorded." line when the list is empty.
- **Rationale**: FR-006/SC-004 require the report to explicitly indicate the *absence* of
  dissent, not merely omit the section. An empty list is the correct structural
  representation (consistent with how `InvestmentThesis.supporting_evidence` already
  represents "no evidence" elsewhere in this codebase); the explicit "no dissent" signal
  belongs in the rendered document, the same way 004's `render_thesis_document` renders
  `"(none)"` for empty assumption/risk/invalidation lists.
- **Alternatives considered**: A dedicated sentinel type (e.g., `dissent: str | None`) on
  `CommitteeReport` distinct from `CommitteeDecision.dissent` — rejected; it would duplicate
  data already present on the composed `CommitteeDecision` for no behavioral gain, and this
  feature does not modify `CommitteeDecision` (FR-013).
