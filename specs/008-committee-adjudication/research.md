# Phase 0 Research: Committee Adjudication Layer

Every Technical Context item was resolvable from the spec, the constitution, and the
existing 006-committee-decision-engine implementation. No open `NEEDS CLARIFICATION`
markers remain.

## Decision: Reuse the existing `aic.committee` package; write no new source code

- **Decision**: This feature's implementation is the already-existing, already-tested
  `src/aic/committee/` package (`CommitteeAdjudicationContext` in `context.py`,
  `CommitteeDecisionDraft` in `draft.py`, `build_prompt` in `prompt.py`, `generate_decision`
  in `generator.py`), produced by 006-committee-decision-engine. No new package, module, or
  function is added.
- **Rationale**: A file-by-file comparison of this spec's Functional Requirements against
  006's implementation (carried out via a live `/speckit-converge` run earlier in this
  session, immediately before this plan) found zero gaps: evidence-ID validation (FR-005),
  provider-error propagation without fabrication (FR-014), dissent recording (FR-009),
  restriction to the existing recommendation set (FR-008), non-averaging rationale
  composition (FR-007), reuse of the existing provider abstraction with no changes (FR-003),
  and read-only DCF consumption (FR-006) are all already implemented and covered by 16
  passing tests in `tests/unit/committee/`. Writing a second, parallel implementation of
  identical logic would violate the constitution's Minimal Architecture principle (VIII) and
  the CLAUDE.md Scope Discipline guidance to "avoid speculative abstractions" and "preserve
  existing behavior" — there is no simpler-alternative test to pass, because reuse *is* the
  simpler alternative.
- **Alternatives considered**: Building a new `aic.adjudication` (or similarly-named)
  package from scratch, matching this spec's scope list literally as new work — rejected.
  It would duplicate deterministic decision logic 1:1 with `aic.committee`, creating two
  code paths that could silently drift apart (a correctness risk the constitution's
  Traceability and Evidence-Before-Opinion principles exist specifically to prevent), for
  zero behavioral difference. Modifying `aic.committee` in place to "belong" to this feature
  — rejected; the code is already correct and tested under 006's ownership, and touching it
  here would violate "modify only necessary files."

## Decision: "InvestmentDecision" in the spec maps to the existing `CommitteeDecision` domain entity

- **Decision**: Wherever this spec's Key Entities or Functional Requirements refer to the
  final "InvestmentDecision," the satisfying artifact is the existing
  `aic.domain.CommitteeDecision` model (`decision_id`, `recommendation`, `rationale`,
  `referenced_evidence`, `referenced_thesis`, `dissent`), returned unchanged by
  `generate_decision`.
- **Rationale**: The domain model (002-domain-model) defines no `InvestmentDecision` type,
  and the spec's own Assumptions section (and its explicit "integration with the existing
  domain models" scope item) direct reuse over introducing a new, parallel type.
  `CommitteeDecision` is also already the exact type 005-investment-committee-report's
  `CommitteeReport.decision` field consumes — satisfying this spec's FR-018/SC-008
  ("consumable by the report layer without a new adapter") by construction, with zero new
  code.
- **Alternatives considered**: Introducing a new `InvestmentDecision` Pydantic model,
  possibly as a thin wrapper or subclass of `CommitteeDecision` — rejected; it would force
  005's report layer to either accept two decision types or gain a new adapter, both
  unjustified by any requirement in this spec (FR-018 explicitly requires *avoiding* new
  adapter code) and prohibited by 005's own contract, which is not modified by this plan.

## Decision: This plan's own artifacts document a mapping, not a new design

- **Decision**: `data-model.md`, `contracts/adjudication-interface.md`, and `quickstart.md`
  for this feature describe how each entity/requirement/scenario in `spec.md` is satisfied
  by 006's existing types and functions, rather than specifying new ones.
- **Rationale**: Spec Kit's Phase 1 outputs exist to give `/speckit-tasks` enough detail to
  generate an accurate task list. For this feature, the accurate task list is verification
  tasks (confirm each requirement against the existing code and its existing tests), not
  implementation tasks — the mapping documents *are* that detail.
- **Alternatives considered**: Leaving Phase 1 artifacts as a literal restatement of 006's
  own `data-model.md`/`contracts/committee-interface.md` — rejected as unnecessary
  duplication of documents that already exist at
  `specs/006-committee-decision-engine/`; this plan's artifacts instead cross-reference them
  directly.
