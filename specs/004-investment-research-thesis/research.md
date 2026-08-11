# Phase 0 Research: Investment Research & Thesis Generation

Every Technical Context item was resolvable from the spec (including its Assumptions
section), the constitution, and the existing 001/002/003 baselines. No open
`NEEDS CLARIFICATION` markers remain.

## Decision: A new `aic.research` sub-package

- **Decision**: Place `ResearchContext`, `ThesisDraft`, `LLMProvider`, `OpenAIProvider`,
  `generate_thesis`, and `render_thesis_document` in a new sibling sub-package
  `src/aic/research/`, not inside `aic.domain` or `aic.dcf`.
- **Rationale**: `aic.domain` is pure, computation-free data; `aic.dcf` is pure,
  deterministic calculation; this feature is neither — it orchestrates an external LLM
  call and business logic around it (evidence resolution, validation). A distinct
  sub-package keeps each existing package's own invariant intact (per its own prior
  FR-017/FR-006-equivalent "no calculation"/"no I/O" guarantees) while giving this
  feature's genuinely different concern (external provider orchestration) its own home,
  matching the constitution's "Research: establish evidence" agent-role framing.
- **Alternatives considered**: Adding this logic inside `aic.domain` — rejected, would
  contradict `aic.domain`'s established "no I/O, no computation" invariant from
  002-domain-model. A single flat `aic.services` package for all future
  application-level logic — rejected as premature; nothing yet justifies a shared
  catch-all package over one clearly-named sub-package per concern.

## Decision: `ThesisDraft` — an LLM-facing schema distinct from `InvestmentThesis`

- **Decision**: The LLM is asked to produce a `ThesisDraft` (summary, `key_assumptions`,
  `key_risks`, `invalidation_conditions` as text, and `supporting_evidence_ids: list[UUID]`
  — *references* to supplied `Evidence`, not reproduced `Evidence` content). The
  `generate_thesis` function then resolves those IDs against the real `Evidence` objects
  from the input `ResearchContext` to build the final `InvestmentThesis.supporting_evidence:
  list[Evidence]` — using the original, untouched `Evidence` objects, never anything the
  LLM generated.
- **Rationale**: `InvestmentThesis.supporting_evidence` (002-domain-model) is
  `list[Evidence]` — full objects, not ID references. Asking the LLM to *reproduce* full
  `Evidence` objects (source, title, excerpt, dates) would (a) risk it subtly altering
  content while reproducing it (a hallucination vector on exactly the field this feature
  most needs to trust) and (b) require fuzzy content-matching to validate traceability
  (FR-005), which is unreliable. Asking for ID references instead makes traceability a
  simple, structural set-membership check — a reference to an ID outside the supplied
  input set is an unambiguous, explicit failure (no ambiguity about "close enough"
  matches). `InvestmentThesis` itself remains completely unmodified, per the spec's own
  Assumption — only a new, LLM-facing intermediate schema is introduced.
- **Alternatives considered**: Asking the LLM to reproduce full `Evidence` objects and
  fuzzy-matching them against the input — rejected for the hallucination and
  reliability reasons above. Changing `InvestmentThesis.supporting_evidence` to
  `list[UUID]` to match this feature's needs — rejected; that would modify an
  already-shipped 002-domain-model contract, which the spec's own Assumptions section
  explicitly rules out ("`InvestmentThesis` is reused unchanged").

## Decision: `openai` SDK as a new, sanctioned dependency

- **Decision**: Add the official `openai` Python package as a new runtime dependency.
- **Rationale**: The constitution's baseline technology list names "OpenAI as the
  initial LLM provider" explicitly — this is not an "unnecessary dependency" under
  Principle VIII, it is the sanctioned, expected one. The official SDK (rather than a
  hand-rolled HTTP client) keeps the adapter small and handles auth/retries/structured
  outputs correctly.
- **Alternatives considered**: A hand-rolled `requests`/`httpx` HTTP client against the
  OpenAI REST API directly — rejected as more code and more surface for subtle bugs
  (auth header handling, retry semantics) for no benefit over the maintained official SDK.

## Decision: Provider protocol shape

- **Decision**: `LLMProvider` is a `typing.Protocol` with one method,
  `complete_structured(*, system_prompt: str, user_prompt: str, schema: type[BaseModel])
  -> LLMCompletion`, where `LLMCompletion` bundles `content: dict[str, Any]` (the raw,
  not-yet-validated structured payload), `prompt_tokens: int`, `completion_tokens: int`,
  and `latency_ms: float`. `generate_thesis` calls `ThesisDraft.model_validate(completion.
  content)` itself — the protocol never returns an already-validated domain object.
- **Rationale**: Keeps the protocol reusable for any future structured-output call (not
  hard-coupled to `ThesisDraft`/`InvestmentThesis`), and keeps "never trust raw model
  text as application state" (constitution Principle III) enforced at one single,
  obvious point (`generate_thesis`), not scattered across provider implementations.
  Bundling token usage and latency directly on the result is the minimal way to satisfy
  the constitution's per-agent-feature cost/latency measurement requirement without a new
  observability subsystem.
- **Alternatives considered**: Protocol returns an already-validated `ThesisDraft`
  directly — rejected; would force every provider implementation (including the fake
  used in tests) to duplicate validation logic, and would blur "transport" vs
  "application validation" responsibilities that the constitution's architecture section
  keeps separate.

## Decision: Cost/latency measurement via structured logging, not a new subsystem

- **Decision**: `generate_thesis` logs one structured log line per generation (token
  usage, latency, model identifier) via Python's standard `logging` module at `INFO`
  level. No new persistence, metrics store, or dashboard is introduced.
- **Rationale**: The constitution's Quality Principles section requires "cost
  measurement, and latency measurement" for agent features; spec.md's FRs did not
  capture this, but the constitution is authoritative over the plan (see plan.md's
  Constitution Check). A structured log line is the smallest possible implementation
  that makes the constitution's own stated goal — "how much does one completed
  investment analysis cost?" — answerable (by inspecting logs), without building
  observability infrastructure before a complete analysis pipeline exists to attach it
  to, which would itself violate Principle VIII (no premature infrastructure).
- **Alternatives considered**: A dedicated `CostTracker`/metrics-persistence component —
  rejected as premature infrastructure for a single, standalone generation step; a
  full observability system belongs to a later iteration once "one completed investment
  analysis" is an actual, executable end-to-end concept (per CLAUDE.md's MVP sequence,
  not yet reached). Skipping measurement entirely — rejected, as it would leave a
  constitution MUST unaddressed with no documented rationale.

## Decision: Settings extension

- **Decision**: Add one optional field to the existing `AppSettings`
  (`src/aic/settings.py`): `openai_api_key: str | None = Field(default=None,
  validation_alias="AIC_OPENAI_API_KEY")`, following 001-repository-bootstrap's
  established `AIC_`-prefixed environment-variable convention exactly.
- **Rationale**: Directly satisfies FR-009/FR-010 ("credentials come from the existing
  settings/configuration mechanism, never hardcoded") using the mechanism the spec
  explicitly names. Optional (not required) so `AppSettings` continues to load
  successfully with zero configuration in every context that doesn't need OpenAI (e.g.,
  running this feature's own tests, which use a fake provider and never read this
  field) — consistent with 001's "no field is required for `AppSettings` to load" design.
- **Alternatives considered**: A separate, feature-specific settings class — rejected;
  the spec explicitly requires reusing "the existing settings/configuration mechanism,"
  and there is exactly one such mechanism in this codebase (`AppSettings`).

## Decision: OpenAI adapter tests mock the SDK client, never the network

- **Decision**: `test_openai_provider.py` constructs `OpenAIProvider` with a mocked
  `openai` client object (e.g., a stand-in exposing the same call surface the adapter
  uses), asserting the adapter maps the mocked response into a correct `LLMCompletion`.
  No test in this feature calls the real OpenAI API.
- **Rationale**: FR-003/SC-003 require zero real network calls anywhere in this
  feature's own test suite — including for the adapter itself, not just for
  `generate_thesis` (which is covered by the separate `FakeLLMProvider` in
  `test_generator.py`). Mocking at the SDK-client boundary (rather than skipping adapter
  tests entirely) still verifies the adapter's own mapping logic is correct.
- **Alternatives considered**: Skipping adapter-level tests and relying only on
  `FakeLLMProvider`-based tests of `generate_thesis` — rejected; would leave the
  actual OpenAI request/response mapping code with zero test coverage.
