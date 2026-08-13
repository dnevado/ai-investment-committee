# Quickstart: Validate Committee Adjudication Layer

This feature introduces no new code, so its validation *is*
006-committee-decision-engine's validation. Every scenario below runs against the existing
`aic.committee` package and its existing `tests/unit/committee/` suite — see
`specs/006-committee-decision-engine/quickstart.md` for the full runnable snippet this
reuses verbatim.

## Prerequisites

```powershell
uv sync
```

## User Story 1 — Adjudicate bull/bear cases into a decision (fake provider)

Run the identical snippet documented in
`specs/006-committee-decision-engine/quickstart.md` under "User Story 1 — Adjudicate
bull/bear cases into a decision (fake provider)". It constructs a
`CommitteeAdjudicationContext`, calls `generate_decision` with a fake `LLMProvider`, and
prints `WATCH 1 1` — confirming context assembly, `CommitteeDecisionDraft` validation,
evidence-ID resolution, and non-averaging rationale composition, satisfying this spec's
User Story 1 (acceptance scenarios 1–4) and SC-001, SC-002, SC-005, SC-006.

**Verified in this session**: re-run live on 2026-08-13, output matched `WATCH 1 1` exactly.

## User Story 2 — Dissent present vs. absent

```powershell
uv run pytest tests/unit/committee/test_dissent.py -v
```

**Expected outcome**: both tests pass — a fake-provider response with non-empty dissent
produces a decision whose dissent matches unchanged, and a response with empty dissent
produces a decision with empty dissent, never fabricated — satisfying this spec's User
Story 2 and SC-004.

## User Story 3 — Zero real external LLM calls

```powershell
uv run pytest tests/unit/committee -v
```

**Expected outcome**: all 16 tests in `tests/unit/committee/` pass with zero network access
and no LLM provider credentials configured — satisfying this spec's User Story 3 and SC-003.

**Verified in this session**: re-run live on 2026-08-13, `16 passed`.

## Provider-error propagation (this spec's FR-014 / SC-007)

```powershell
uv run pytest tests/unit/committee/test_committee_generator.py::test_generate_decision_propagates_provider_error_without_fabricating_decision -v
```

**Expected outcome**: passes — a provider error is surfaced to the caller unchanged, and no
fabricated fallback decision is ever returned.

## Consumed by the report layer with no new adapter (this spec's FR-018 / SC-008)

```powershell
uv run pytest tests/unit/report -v
```

**Expected outcome**: all `CommitteeReport` tests pass, confirming `CommitteeReport.decision`
already accepts the exact `CommitteeDecision` type this feature's adjudication step
produces, with no new adapter code anywhere in the repository.

## Full validation in one pass

```powershell
uv run pytest tests/unit/committee tests/unit/report -v
uv run ruff check .
uv run mypy src
```

**Verified in this session**: all three commands exited `0` on the current `main` — the
complete acceptance signal for this feature, with zero files added or modified.
