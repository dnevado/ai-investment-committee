# Phase 0 Research: Investment Committee Domain Model

Every Technical Context item was resolvable from the spec (including its Clarifications
session), the constitution, and the existing 001-repository-bootstrap baseline. No open
`NEEDS CLARIFICATION` markers remain.

## Decision: ISO 4217 currency validation against the real, complete code set

- **Decision**: Vendor the **complete** real ISO 4217 alphabetic currency code list
  (all ~180 active codes, e.g., `USD`, `EUR`, `JPY`, ...) as a single Python
  `frozenset[str]` constant inside `src/aic/domain/currency.py`, sourced verbatim from
  the official ISO 4217 published list, and validate every `currency` field against it
  with a Pydantic field/model validator. No third-party currency package (e.g.,
  `pycountry`) is added. The module carries a comment documenting where the list came
  from and how to regenerate it (re-copy the current active-code list from the ISO 4217
  maintenance agency's published table) so the "maintainable" requirement is satisfied
  without ongoing dependency upkeep.
- **Rationale**: An *arbitrary subset* (as in the earlier draft of this decision) is not
  acceptable — it would silently reject legitimate real-world currencies never
  anticipated at design time, which is worse than not validating at all for a feature
  whose entire purpose is eliminating currency ambiguity. The **complete** code set is
  necessary. It is still simplest and most maintainable to vendor that complete set as a
  static constant rather than add a dependency: it is a small (~180-entry), rarely
  changing (ISO adds/removes a handful of codes roughly once every few years),
  self-contained data set with no behavior attached to it — exactly the case where a
  dependency adds ongoing supply-chain and version-compatibility surface for no
  behavioral benefit over a vendored constant. This keeps the domain layer
  dependency-free (reinforcing FR-018) and trivially testable.
- **Alternatives considered**: `pycountry` — accurate and maintained, and would remove
  the (minor) burden of manually refreshing the vendored list, but is a real runtime
  dependency (with its own transitive dependencies and release cadence) for a static
  data set this project can vendor directly; rejected as disproportionate given the
  constitution's and project's repeated "avoid unnecessary dependencies" guidance. A
  regex/format-only check (3 uppercase letters) — rejected outright, since it is exactly
  the "arbitrary" non-validation this correction rules out. An arbitrary curated subset
  (the original version of this decision) — rejected as insufficiently correct: it must
  be the real, complete set, not a subset chosen for convenience.

## Decision: Identifier type — caller-supplied, not auto-generated

- **Decision**: Every identifier field (`company_id`, `evidence_id`, and the identifiers
  on `InvestmentCase`, `AnalysisAssessment`, `ValuationResult`, `CommitteeDecision`) is a
  standard-library `uuid.UUID`, but it is a **required constructor argument** — the
  domain models do **not** auto-generate it via a `default_factory`. The caller is
  responsible for supplying a stable, unique UUID (typically via `uuid4()` at the call
  site, or a previously-established ID when reconstructing an existing record).
- **Rationale**: FR-010 requires identifiers to be "explicit and stable" — a domain
  model silently minting its own identity on every construction is at odds with
  "explicit" (the caller never chose or saw the value) and is a poor fit for a
  dependency-free domain layer that has no persistence: whatever eventually persists,
  displays, or cross-references these records needs to control identity itself
  (e.g., to reconstruct the *same* `Company` from stored data with its original ID,
  rather than getting a new one every time). Keeping generation as the caller's
  responsibility also keeps the domain layer itself free of even the minimal "hidden
  behavior" of auto-generation, consistent with these models being pure, explicit data
  contracts. `uuid.UUID` remains the field's type — only *who* generates the value
  changes.
- **Alternatives considered**: `default_factory=uuid4` (the original version of this
  decision) — rejected per the correction: auto-generation makes identity an implicit
  side effect of construction rather than an explicit input, and forecloses the caller's
  ability to supply a stable ID when reconstructing a record. Plain `str` — still
  rejected, as before, since an unstructured string offers no uniqueness guarantee or
  validation; UUID remains the right *type*, just not auto-generated.

## Decision: Explicit Pydantic v2 API usage

- **Decision**: This feature targets Pydantic v2 explicitly (the `pydantic>=2.0`
  dependency already pinned in `pyproject.toml` by 001-repository-bootstrap). All
  serialization/deserialization uses Pydantic v2's `model_dump()` and
  `model_validate()` — never the Pydantic v1 API (`.dict()`, `.parse_obj()`,
  `.json()`), which is deprecated in v2 and unavailable in a future v3.
- **Rationale**: Makes explicit what was previously only implied by the pinned
  dependency version, so every model, test, and contract in this feature is written
  against one unambiguous API surface. `model_dump()`/`model_validate()` round-trip
  losslessly for the stdlib types this feature uses (`UUID`, `Decimal`, `date`,
  `datetime`, `StrEnum`) when used in their default (Python-object) mode, which is what
  the dict-canonical serialization decision below requires.
- **Alternatives considered**: None — Pydantic v1 APIs are not a real alternative given
  the already-pinned v2 dependency; this decision exists to make the target explicit and
  traceable, not to choose between real options.

## Decision: `Money` value object for monetary fields

- **Decision**: Introduce a small, reusable `Money` value object in
  `src/aic/domain/money.py`: `amount: Decimal`, `currency: CurrencyCode` (the same
  ISO 4217-validated type used elsewhere). It is used wherever a single monetary value
  needs its own currency context, replacing a repeated "bare `Decimal` amount +
  sibling `currency` field" pattern:
  - `ValuationResult.estimated_value` becomes a single `Money` field (replacing the
    separate `currency` + `estimated_value: Decimal` fields).
  - `FinancialSnapshot`'s monetary metrics (`revenue`, `operating_income`,
    `net_income`, `free_cash_flow`, `cash`, `debt`) each become `Money | None`,
    replacing the snapshot-level `currency` field plus six sibling bare-`Decimal`
    fields. A model-level validator enforces that every *populated* metric on one
    `FinancialSnapshot` shares the same currency (preserving the "one snapshot, one
    currency" semantic from the spec's FR-004 framing, without a redundant top-level
    field). `shares_outstanding` stays a bare `Decimal | None` — it is a share count,
    not a monetary amount, and correctly has no currency.
  `Money` carries no arithmetic or financial-calculation methods (no `__add__`, no
  conversion logic) — it is purely a typed container, consistent with FR-017's
  prohibition on financial calculations anywhere in the domain layer.
- **Rationale**: Directly requested by this correction, and a real improvement over the
  original design: "amount paired with its currency" is one coherent piece of
  information, not two independently-optional pieces of data that happen to be declared
  next to each other. Bundling them into one type means every future consumer of a
  monetary field automatically gets both parts together (no risk of reading an amount
  while accidentally using the wrong sibling currency field), and it removes the need
  for a separate, easily-forgotten top-level `currency` field on models with multiple
  monetary metrics.
- **Alternatives considered**: Keep bare `Decimal` + a single shared `currency` field
  per model (the original design) — workable for `ValuationResult` (one amount, one
  currency) but awkward for `FinancialSnapshot` (up to six monetary fields all
  implicitly sharing one distant top-level field with no per-field type-level
  connection); rejected because it is exactly the "repeating bare Decimal + currency
  fields" pattern this correction asks to remove. Giving `Money` conversion or
  arithmetic behavior — rejected, out of scope per FR-017 and this correction's explicit
  "no calculations or financial logic" constraint.

## Decision: Date and timestamp types

- **Decision**: Use `datetime.date` for point-in-time dates without a time component
  (`FinancialSnapshot.as_of`, `Evidence.publication_date`/`retrieved_date`,
  `ValuationResult.valuation_date`) and `datetime.datetime` (timezone-aware, UTC) for
  true timestamps (`InvestmentCase.analysis_timestamp`,
  `CommitteeDecision.decision_timestamp`).
- **Rationale**: Matches FR-011's requirement for unambiguous date/time values using
  standard types; Pydantic supports both natively with round-trip-safe dict
  serialization. Distinguishing `date` from `datetime` avoids the ambiguity of a
  timestamp that silently carries (or drops) a time-of-day component where none was
  intended.
- **Alternatives considered**: ISO 8601 strings everywhere — rejected because it
  reintroduces the free-form-string ambiguity the spec explicitly warns against for
  other fields; a single `datetime` type for everything — rejected as it would force a
  fabricated time-of-day onto fields that are genuinely date-only (e.g., a fiscal
  as-of date).

## Decision: Enum representation

- **Decision**: `EvidenceType` and `Recommendation` are `enum.StrEnum` (Python 3.11+
  stdlib) with explicit member values matching the spec's vocabulary (`FACT`,
  `CALCULATION`, `ASSUMPTION`, `INTERPRETATION`, `OPINION` for the former; `BUY`,
  `WATCH`, `AVOID` for the latter, per the spec's Assumptions section citing the
  constitution).
- **Rationale**: `StrEnum` values compare and serialize as plain strings, which fits the
  dict-canonical serialization decision cleanly (no custom encoder needed) while still
  giving Pydantic a closed, validated set of allowed values — an out-of-set value is
  rejected automatically.
- **Alternatives considered**: Plain `Literal[...]` string unions — workable, but a named
  `StrEnum` is more discoverable and reusable across the codebase (agents/tests can
  `from aic.domain.enums import EvidenceType` rather than duplicating a literal list).

## Decision: Composition style for `InvestmentCase` and cross-model references

- **Decision**: `InvestmentCase` embeds its `Company`, `FinancialSnapshot` list, and
  `InvestmentThesis` as nested Pydantic models (not just IDs), but `InvestmentThesis`,
  `AnalysisAssessment`, `ValuationResult`, and `CommitteeDecision` reference `Evidence`
  by its `evidence_id` (`UUID`) plus an inline copy of the evidence list is *not*
  duplicated — evidence is owned by whichever object first introduces it
  (`InvestmentThesis.supporting_evidence`, etc.) and referenced by ID elsewhere within
  the same `InvestmentCase`.
- **Rationale**: Matches FR-015 ("small composable models... rather than one large
  model") while still satisfying FR-006's requirement that `InvestmentCase` connects a
  `Company`, `FinancialSnapshot`(s), a `InvestmentThesis`, and `Evidence` — nesting the
  directly-owned parts keeps the object self-contained and losslessly serializable,
  while ID-references between assessments/decisions and evidence avoid duplicating the
  same evidence content in multiple places.
- **Alternatives considered**: Everything by ID with no nesting (would make
  `InvestmentCase` require an external lookup table to be useful — awkward for a
  pure, dependency-free domain layer with no persistence); everything nested/duplicated
  everywhere (would violate "small composable models" and risk divergent copies of the
  same evidence).
