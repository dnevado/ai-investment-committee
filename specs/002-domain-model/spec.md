# Feature Specification: Investment Committee Domain Model

**Feature Branch**: `002-domain-model`

**Created**: 2026-08-10

**Status**: Draft

**Input**: User description: "Define the minimal, provider-independent domain model for AIC. Establishes the typed contracts that future research, Bull/Bear, valuation and committee components will exchange. Deterministic, explicit, and independent of OpenAI, LangChain, LangGraph, AWS and any external data provider. Core concepts: Company, Evidence, FinancialSnapshot, InvestmentThesis, InvestmentCase, AnalysisAssessment (reusable, not hard-coded to Bull/Bear), ValuationResult (shape only, no DCF), CommitteeDecision (shape only, no orchestration). No untyped dicts for core objects, no fabricated defaults, explicit currency on monetary values, deterministic serialization, small composable models."

## Clarifications

### Session 2026-08-10

- Q: Should currency values be restricted to real ISO 4217 currency codes, or just required to be present as a string? → A: Validate against the real ISO 4217 currency code list (e.g., USD, EUR, JPY) — invalid/unknown codes rejected.
- Q: What format should the stable identifier fields (company_id, evidence_id, InvestmentCase id, etc.) use? → A: UUID — a generated UUID string for every identifier, guaranteeing global uniqueness with no caller coordination required.
- Q: When these domain models are serialized and deserialized, what should the canonical exchange format be? → A: Plain Python dict is the canonical form; a JSON string is just that dict encoded, not a separate contract.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Represent a Company's Sourced Financial Data Without Ambiguity (Priority: P1)

A developer building any later AIC feature (research, valuation, agents) needs to represent a
company and a point-in-time snapshot of its financial metrics as typed data, where every monetary
value carries explicit currency, missing metrics are represented explicitly rather than fabricated,
and nothing is stored as an untyped dictionary or ambiguous string.

**Why this priority**: Company and financial data are inputs to every other domain concept in this
feature. Getting this foundation wrong (ambiguous currency, fabricated values, untyped blobs)
propagates incorrect or untrustworthy data through the entire system.

**Independent Test**: Construct a `Company` and a `FinancialSnapshot` with valid data — both
validate and can be serialized and deserialized without loss. Attempt to construct a
`FinancialSnapshot` with a monetary value but no currency, or with a required field missing —
construction fails with an explicit validation error.

**Acceptance Scenarios**:

1. **Given** valid identity fields (company_id, ticker, name, exchange, country, sector,
   industry), **When** a `Company` is constructed, **Then** it validates successfully and every
   field is available in typed form (no untyped dictionary).
2. **Given** an `as_of` date and only some of the optional financial metrics, each present metric
   expressed as a `Money` value (amount plus currency) (e.g. revenue known, free cash flow
   unknown), **When** a `FinancialSnapshot` is constructed, **Then** it validates successfully,
   the known metric is present as a `Money` value, and the unknown metric is explicitly absent
   (not zero, not fabricated).
3. **Given** a monetary financial metric provided without a valid accompanying currency (an
   invalid or missing `Money.currency`), **When** a `FinancialSnapshot` is constructed, **Then**
   construction fails with an explicit validation error.
4. **Given** a validly constructed `Company` and `FinancialSnapshot`, **When** each is serialized
   and then deserialized, **Then** the result is identical to the original with no domain
   information lost.

---

### User Story 2 - Assemble Sourced Evidence Into an Investment Thesis and Case (Priority: P2)

A developer needs to represent supporting evidence (facts, calculations, assumptions,
interpretations, or opinions) and combine it with a company's financial data into an investment
thesis and a complete, identifiable investment case — the initial research object that later
features (Bull/Bear, valuation, committee) will build on.

**Why this priority**: Evidence and the thesis are what later analysis argues about and what the
committee ultimately judges; they depend on Company/FinancialSnapshot (Story 1) already existing
as a stable foundation.

**Independent Test**: Construct several `Evidence` records covering each evidence type, an
`InvestmentThesis` referencing some of them, and an `InvestmentCase` connecting a `Company`, one or
more `FinancialSnapshot` records, the thesis, and the evidence — the case exposes a stable
identifier, an analysis timestamp, and every connected part.

**Acceptance Scenarios**:

1. **Given** a source, title, retrieved date, excerpt, and an evidence type of FACT, CALCULATION,
   ASSUMPTION, INTERPRETATION, or OPINION, **When** an `Evidence` record is constructed without a
   URL, **Then** construction succeeds — a URL or other source reference is never a hard
   requirement, since some sources are internal/structured rather than web-linked.
2. **Given** an evidence-type value outside the five defined types, **When** an `Evidence` record
   is constructed, **Then** construction fails with an explicit validation error.
3. **Given** a summary, supporting evidence references, key assumptions, key risks, and
   invalidation conditions, **When** an `InvestmentThesis` is constructed, **Then** it validates
   successfully and exposes each part distinctly.
4. **Given** a `Company`, one or more `FinancialSnapshot` records, an `InvestmentThesis`, and a set
   of `Evidence`, **When** an `InvestmentCase` is assembled, **Then** it exposes a stable
   identifier, an analysis timestamp, and all connected parts, and it can be serialized and
   deserialized without loss.

---

### User Story 3 - Define Reusable Contracts for Future Assessment, Valuation, and Decision (Priority: P3)

A developer needs stable, typed contracts for a future analysis assessment (without hard-coding a
"Bull" or "Bear" role into the domain type), a future valuation result (shape only, no
calculation), and a future committee decision (shape only, no orchestration) — so later features
have something concrete to produce and consume without redesigning the domain layer.

**Why this priority**: These contracts close the loop from evidence and thesis (Story 2) to an
eventual assessment, valuation, and decision, but they are placeholders for future logic and
depend conceptually on the entities already defined in Stories 1–2, so they come last.

**Independent Test**: Construct an `AnalysisAssessment` (with a conclusion, arguments, evidence,
assumptions, risks, and confidence) without any Bull/Bear label anywhere in its type or fields;
construct a `ValuationResult` with a method, date, and a `Money` estimated value; construct a
`CommitteeDecision` with a recommendation, rationale, and referenced evidence/thesis — all three
validate independently and serialize without loss.

**Acceptance Scenarios**:

1. **Given** a conclusion, arguments, supporting evidence, assumptions, risks, and a confidence
   value, **When** an `AnalysisAssessment` is constructed, **Then** it validates successfully, and
   neither the model's type name nor its fields encode "Bull" or "Bear" — that distinction belongs
   to a future application-level orchestration, not this domain type.
2. **Given** a method, valuation date, and an estimated value expressed as a `Money` value (amount
   plus currency), **When** a `ValuationResult` is constructed, **Then** it validates successfully
   without performing or requiring any valuation calculation.
3. **Given** a recommendation, rationale, referenced evidence, and referenced thesis, but no
   valuation performed yet, **When** a `CommitteeDecision` is constructed without a valuation
   reference, **Then** construction still succeeds, since a valuation reference is only required
   "when available."
4. **Given** a recommendation value outside the defined set, **When** a `CommitteeDecision` is
   constructed, **Then** construction fails with an explicit validation error.
5. **Given** validly constructed `AnalysisAssessment`, `ValuationResult`, and `CommitteeDecision`
   objects, **When** each is serialized and then deserialized, **Then** the result is identical to
   the original with no domain information lost.

---

### Edge Cases

- What happens when `Evidence` has no known publication date (e.g., an undated internal memo)?
  Publication date is explicitly optional — construction succeeds without it.
- What happens when a `FinancialSnapshot` has no monetary metrics known at all, only `as_of`?
  Construction succeeds — every metric field is independently optional, and no `Money` value is
  required unless a metric is actually being reported.
- What happens when the same company is analyzed twice at different times? Each resulting
  `InvestmentCase` has its own independently stable identifier and analysis timestamp — no
  collision or overwrite between them.
- What happens when a `CommitteeDecision` needs to record disagreement among reviewers? Dissent /
  disagreement information is an explicit part of the model, not something bolted on or omitted.
- What happens when a currency value is supplied that is not a real ISO 4217 code (e.g., "USDD" or
  "Dollars")? Construction fails with an explicit validation error, the same as any other invalid
  field.
- What happens when code outside the domain layer tries to pass a plain dictionary instead of one
  of these typed models for a core object? That is out of scope for this feature to prevent at
  runtime beyond what type-checking and the models' own validation already provide — this feature
  only guarantees that the domain layer itself never represents core objects as untyped
  dictionaries.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The domain layer SHALL provide a `Company` model with at least: `company_id`,
  `ticker`, `name`, `exchange`, `country`, `sector`, and `industry`.
- **FR-002**: The domain layer SHALL provide an `Evidence` model with at least: `evidence_id`,
  `source`, `title`, an optional URL or other source reference, an optional publication date,
  a retrieved date, an excerpt or factual content, and an evidence type. A URL SHALL NOT be
  required, since some sources are structured or internal rather than web-linked.
- **FR-003**: `Evidence` type SHALL be an explicit, closed classification distinguishing at least:
  FACT, CALCULATION, ASSUMPTION, INTERPRETATION, and OPINION. A value outside this set SHALL be
  rejected.
- **FR-004**: The domain layer SHALL provide a `FinancialSnapshot` model representing a
  point-in-time set of financial metrics: `as_of` date, and independently optional `revenue`,
  `operating_income`, `net_income`, `free_cash_flow`, `cash`, `debt`, and `shares_outstanding`.
  Every metric that is a monetary amount (all of the above except `shares_outstanding`, which is
  a share count) SHALL be represented as a `Money` value (FR-020) when present, not a bare
  number. No ratio or valuation-metric calculation SHALL be performed on these values.
- **FR-005**: The domain layer SHALL provide an `InvestmentThesis` model with: `summary`,
  `supporting_evidence` (references to `Evidence`), `key_assumptions`, `key_risks`, and
  `invalidation_conditions`.
- **FR-006**: The domain layer SHALL provide an `InvestmentCase` model that connects a `Company`,
  one or more `FinancialSnapshot` records, an `InvestmentThesis`, and `Evidence`, and that carries
  a stable identifier and an analysis timestamp.
- **FR-007**: The domain layer SHALL provide a reusable `AnalysisAssessment` model (assessment
  identifier, conclusion, arguments, supporting evidence, assumptions, risks, and confidence) that
  does not encode a "Bull" or "Bear" role in its type or fields — future agent roles are an
  application-level orchestration concern, not a domain-model concern.
- **FR-008**: The domain layer SHALL provide a `ValuationResult` model (valuation identifier,
  method, valuation date, an `estimated_value` represented as a `Money` value (FR-020),
  assumption/evidence references, and uncertainty or confidence information) without
  implementing any valuation calculation.
- **FR-009**: The domain layer SHALL provide a `CommitteeDecision` model (decision identifier,
  recommendation, rationale, referenced evidence, referenced thesis, an optional valuation
  reference, dissent/disagreement information, and a decision timestamp) without implementing
  committee orchestration.
- **FR-010**: Every identifier field (on `Company`, `Evidence`, `InvestmentCase`,
  `AnalysisAssessment`, `ValuationResult`, `CommitteeDecision`) SHALL be a generated UUID, explicit
  and stable within an analysis — never implicitly derived, regenerated, or reused across
  unrelated objects.
- **FR-011**: All date and timestamp fields SHALL use unambiguous date/time values, never
  free-form strings.
- **FR-012**: Every monetary value SHALL carry explicit, unambiguous currency context wherever it
  occurs; monetary amounts SHALL NOT be represented as bare or free-form strings. Currency values
  SHALL be validated against the real ISO 4217 currency code list — an unrecognized code SHALL be
  rejected with an explicit validation error. The `Money` value object (FR-020) is the structural
  mechanism that enforces this: an amount can never exist in the domain layer without its
  currency attached.
- **FR-013**: Optional or not-yet-available information SHALL be represented with explicit
  optional fields; it SHALL NOT be fabricated or silently defaulted, particularly for material
  financial information.
- **FR-014**: Construction with invalid or missing required data SHALL raise an explicit
  validation error.
- **FR-015**: Domain models SHALL be small and composable — connected by reference/composition —
  rather than expressed as one large, all-in-one investment-case model.
- **FR-016**: Domain models SHALL be deterministically serializable and deserializable with no
  loss of domain information on round-trip. A plain dict (produced/consumed via the model's own
  dict-conversion methods) SHALL be the canonical serialized form; a JSON string, where needed, is
  that same dict encoded, not a separate contract.
- **FR-017**: The domain layer SHALL implement no financial calculations, ratio derivations, DCF
  logic, or other valuation computation.
- **FR-018**: The domain layer SHALL have no dependency on OpenAI, LangChain, LangGraph, AWS/boto3
  SDKs, or any external market-data provider SDK; it SHALL perform no network or file I/O and
  SHALL NOT read environment variables.
- **FR-019**: All core domain models SHALL be importable from one `aic.domain` location and usable
  independently of any application, orchestration, agent, or persistence layer — no repositories,
  services, agents, API endpoints, or persistence are introduced by this feature.
- **FR-020**: The domain layer SHALL provide a `Money` value object with exactly two fields: an
  `amount` represented as a precise decimal number (never a binary floating-point number, to
  avoid representation error in monetary values) and a `currency` validated per FR-012. `Money`
  SHALL carry no arithmetic, conversion, or other calculation behavior — it is a typed container
  only (consistent with FR-017). It SHALL be the representation used for every monetary field on
  `FinancialSnapshot` and for `ValuationResult.estimated_value`, rather than a bare amount beside
  a separately-declared currency field.

### Key Entities

- **Company**: Identity of the analyzed business (company_id, ticker, name, exchange, country,
  sector, industry).
- **Evidence**: A classified, traceable piece of supporting material (source, title, optional
  reference/URL, optional publication date, retrieved date, excerpt, evidence type).
- **Money**: A value object bundling a precise decimal `amount` with its validated ISO 4217
  `currency`, so an amount and its currency are always one inseparable piece of information
  rather than two independently-optional fields. Used for every monetary field in
  `FinancialSnapshot` and for `ValuationResult.estimated_value`.
- **FinancialSnapshot**: A point-in-time set of financial metrics; every metric beyond `as_of`
  is independently optional, and every monetary metric present is a `Money` value.
- **InvestmentThesis**: The narrative and its explicit assumptions, risks, and invalidation
  conditions, linked to supporting evidence.
- **InvestmentCase**: The aggregate initial research object connecting Company, one or more
  FinancialSnapshot records, the Thesis, and Evidence, with a stable identifier and timestamp.
- **AnalysisAssessment**: A reusable, role-agnostic structure for a future analysis conclusion
  (used by, but not naming, future Bull/Bear-style agents).
- **ValuationResult**: The shape of a future valuation output — no calculation logic;
  `estimated_value` is a `Money` value.
- **CommitteeDecision**: The shape of a future committee decision — no orchestration logic.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of valid construction attempts for each of the eight core models succeed, and
  100% of construction attempts with missing required or invalid data fail with an explicit,
  specific validation error.
- **SC-002**: 100% of monetary fields across all models are accompanied by explicit, ISO
  4217-valid currency information — none can be constructed with a monetary value but no currency,
  and none can be constructed with a currency code that is not a real ISO 4217 code.
- **SC-003**: 100% of optional financial-metric fields can be omitted from a `FinancialSnapshot`
  without producing a fabricated or defaulted value, verified by tests covering partial data.
- **SC-004**: 100% of serialize-then-deserialize round trips (via the canonical dict form) across
  all eight core models reproduce the original object with no domain information lost.
- **SC-005**: 100% of `Evidence` records are classified into one of the five defined evidence
  types; a value outside that set is rejected 100% of the time.
- **SC-006**: The domain package can be imported and every model constructed, validated, and
  serialized with zero network calls, zero environment-variable reads, and zero dependency on
  LLM, orchestration, or cloud packages.
- **SC-007**: Zero DCF, valuation-calculation, agent-role, or external-integration logic exists
  anywhere in the code delivered by this feature.

## Assumptions

- **Recommendation values for `CommitteeDecision`**: not restated in this description, but the
  constitution already defines the MVP recommendation set as BUY, WATCH, or AVOID (Investment
  Decision Principles). This feature reuses that closed set rather than inventing a new one.
- **Confidence / uncertainty representation**: no scale was specified for `AnalysisAssessment`'s
  confidence or `ValuationResult`'s uncertainty/confidence information. This feature assumes a
  bounded numeric value (0.0–1.0) as the minimal, revisable convention.
- **Multiple financial snapshots per case**: "financial snapshot(s)" is read as `InvestmentCase`
  holding one or more `FinancialSnapshot` references (e.g., successive quarters), not exactly one.
- **Module location**: the description explicitly requires domain models to live under
  `src/aic/domain/` and to be importable from `aic.domain` — this is normally an implementation
  detail left to the plan, but is preserved here as an explicit requirement (FR-019) because the
  user stated it as a hard constraint, not an incidental choice.
- **Pydantic as the modeling technology**: explicitly permitted by the description ("Pydantic is
  allowed because it is part of the project's domain contract technology"); this feature does not
  treat that as an implementation detail to abstract away, consistent with the constitution's
  Structured Outputs principle.
