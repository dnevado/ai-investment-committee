<!--
Sync Impact Report
- Version change: (unratified template) → 1.0.0
- Rationale: Initial ratification of the Spec Kit governance file. Content is migrated and
  consolidated from the repository's existing informal constitution (CONSTITUION.md, v0.1,
  2026-08-09), which was never wired into the Spec Kit workflow. Treated as MAJOR since this is
  the first binding version.
- Modified principles: n/a (initial adoption)
- Added sections: Core Principles (I-X), Architecture & Agent Design Constraints,
  Quality, Observability & Development Workflow, Governance (with Definition of Done and
  MVP Success Criterion folded in)
- Removed sections: none
- Deferred/TODO items:
  - TODO(ORIGINAL_RATIFICATION_DATE): The informal CONSTITUION.md is undated in origin (only
    "Last Updated: 2026-08-09" is known, matching repo initialization). Ratification date below
    uses 2026-08-09 as the effective adoption date of this formal governance file.
  - RESOLVED 2026-08-12: the informal root-level file (renamed CONSTITUION.md →
    CONSTITUTION.md to fix a typo) now contains only a pointer to this file, removing the
    two-document drift risk noted above.
-->

# AI Investment Committee Constitution

## Core Principles

### I. Evidence Before Opinion

Every material investment claim MUST be grounded in identifiable evidence. The system MUST
distinguish between facts, derived calculations, assumptions, interpretations, and opinions.
The LLM MUST NOT present an unsupported assumption as a factual statement.

Rationale: AIC's output is a decision-support memo, not a trading signal. Its credibility
depends entirely on the reader being able to tell what is known versus what is inferred.

### II. LLM Proposes, Code Computes

LLMs are responsible for synthesis, reasoning, interpretation, hypothesis generation, argument
construction, and committee deliberation. Deterministic application code is responsible for all
financial calculations: DCF, multiples, scenario math, percentages, aggregation, and validation.
LLMs MUST NOT own arithmetic.

Rationale: Language models are unreliable at exact computation and non-auditable. Financial
conclusions must be reproducible and independently testable.

### III. Structured Outputs Only

All material LLM outputs MUST use explicit typed schemas (Pydantic, OpenAI structured outputs,
or LangGraph state schemas). Free-form text MUST NOT be used as an internal interface between
agents. Raw model text MUST NOT be trusted as application state.

Rationale: Untyped text between agents is a silent source of parsing errors and hallucinated
state that is invisible until it causes a downstream failure.

### IV. Bull/Bear Symmetry

The product MUST NOT be designed to confirm a predefined investment thesis. For every analysis,
the Bull Agent MUST argue the strongest credible upside case, the Bear Agent MUST argue the
strongest credible downside case and actively attempt to invalidate the thesis, and the
Committee Chair MUST evaluate both without simply averaging them.

Rationale: An investment committee that only confirms a starting bias is not useful; adversarial
symmetry is what produces a defensible recommendation.

### V. Explicit Assumptions

Investment conclusions MUST expose the assumptions that drive them (e.g., revenue growth,
operating margin, FCF conversion, WACC, terminal growth, valuation multiple, market growth,
competitive assumptions). A user MUST be able to answer: "What would have to be true for this
conclusion to be correct?"

Rationale: Valuation is assumption-sensitive by nature; hiding the assumptions hides the actual
risk being taken.

### VI. Deterministic Valuation

Financial calculations MUST be implemented in Python or equivalent deterministic code. The LLM
MAY propose assumptions but MUST NOT directly perform or control the mathematical implementation
of the valuation engine. The valuation engine MUST be independently testable, decoupled from any
LLM call.

Rationale: A DCF must produce the same output for the same inputs every time; correctness here is
non-negotiable and unit-testable.

### VII. Traceability

Material data points and claims MUST retain source metadata whenever possible, sufficient to
identify provider, dataset/document, publication date, retrieval date, and the relevant
field/location. The system MUST avoid presenting generated information as sourced information,
and MUST NOT silently mix currencies, fiscal periods, annual/quarterly data, or reported/adjusted
metrics. When uncertain, the system MUST fail explicitly or mark the uncertainty.

Rationale: Financial data is easy to misattribute or misalign across periods and units; silent
mixing produces confidently wrong numbers.

### VIII. Minimal Architecture, No Premature Infrastructure

The MVP MUST optimize for speed of development, simplicity, debuggability, low operating cost,
and ease of swapping components. The MVP MUST NOT introduce infrastructure without a demonstrated
need. Explicitly excluded from MVP: RAG, vector databases, pgvector, Kubernetes, microservices,
Kafka, Redis, complex event-driven architecture, autonomous agent-to-agent communication, a
frontend application, portfolio management, and broker integration. AWS and PostgreSQL are
deferred until the local vertical slice has been validated.

Rationale: Infrastructure adopted before the workflow is validated locally is a common source of
wasted effort and premature lock-in.

### IX. No RAG in MVP

The MVP uses structured financial data, controlled public sources, explicit source metadata, and
direct model context. Document ingestion and RAG MAY be introduced later only if user validation
demonstrates that structured data is insufficient.

Rationale: RAG adds retrieval-quality risk and infrastructure cost that is unjustified until the
structured-data approach is proven inadequate.

### X. Provider Abstraction

The initial LLM provider is OpenAI, but the application domain MUST NOT be tightly coupled to
OpenAI-specific implementation details. The architecture MUST permit future support for other LLM
providers without rewriting the domain model or investment logic. The application MUST be
testable without OpenAI, external financial APIs, or AWS, by depending on protocols/interfaces
that infrastructure implements.

Rationale: Provider and API landscapes shift; the investment logic must outlive any single
vendor's SDK.

## Architecture & Agent Design Constraints

Dependency direction: CLI → Application → Domain, with Infrastructure implementing
protocols/interfaces defined at the application/domain boundary (Infrastructure → Domain is the
inversion point). Concretely: CLI → Application Layer → LangGraph → Agents → Data Providers →
Financial Engine.

Business logic (investment logic, DCF, valuation rules) MUST live in domain/application modules,
never inside OpenAI adapters, LangGraph nodes, the CLI, or AWS infrastructure code. LangGraph is
orchestration only: graph nodes MUST NOT contain DCF formulas, provider-specific code,
persistence logic, or complex business rules — nodes call testable services, and graph state MUST
be explicit and typed.

Agents MUST be single-purpose, explicitly scoped, deterministic in their interface, and
independently testable, and MUST be implemented as application services, not domain models. Not
every task warrants an agent. Initial agents are Research, Bull, Bear, and Committee Chair; the
valuation engine is not an agent. Agents MUST NOT recursively create or invoke arbitrary other
agents, and the graph topology MUST remain explicit.

The Committee Chair MUST NOT simply average Bull and Bear outputs. It MUST identify the central
investment thesis, supporting evidence, assumptions, disagreements, valuation, downside risks,
and invalidation conditions, then produce a recommendation (BUY, WATCH, or AVOID) with a
conviction score and explanation. These recommendations are research outputs, not personalized
financial advice.

Baseline technology: Python 3.12+, Pydantic, LangChain (where useful for model/provider
integration), LangGraph for orchestration, OpenAI as the initial LLM provider, SQLite locally,
pytest. Avoid unnecessary dependencies.

## Quality, Observability & Development Workflow

Testing uses three layers: unit tests for pure deterministic functions (DCF, validation,
transformations); contract tests for provider and agent interfaces using fake providers; and
end-to-end tests that mock external providers initially, with real-provider evaluation run
separately. Every feature MUST include unit tests, schema validation, error handling, acceptance
criteria, and relevant evaluation cases. Agent features MUST additionally include
structured-output tests, evidence/attribution tests, hallucination/unsupported-claim tests where
practical, cost measurement, and latency measurement. At minimum, `pytest` MUST be run before
claiming success; `ruff check .` and `mypy src` MUST be run if configured.

The system MUST make it possible to measure, at minimum: analysis duration, LLM call count, token
usage where available, estimated LLM cost, failed runs, completed runs, source count, and
validation failures — sufficient to answer "how much does one completed investment analysis
cost?"

Development follows: Specify → Clarify → Plan → Tasks → Implement → Test → Evaluate → Review.
Work MUST proceed in small increments — implement one task/iteration at a time, never the whole
roadmap unless explicitly requested — and after each meaningful change: run tests, inspect
failures, fix, report what changed. Prompt changes are production code changes and require tests
where possible, representative fixtures, and evaluation against prior behavior.

When implementing a feature, only necessary files MUST be modified; speculative abstractions,
premature optimization, and unjustified infrastructure MUST be avoided; existing behavior MUST be
preserved; relevant tests MUST be run. If a requirement conflicts with this Constitution, the
conflict MUST be identified explicitly before implementation. Prohibited without explicit
justification: inventing APIs or financial data, hard-coding secrets, bypassing Pydantic
validation, calling OpenAI directly from domain code, adding RAG/vector DB to the MVP, adding AWS
before local validation, creating autonomous loops without explicit requirement, and rewriting
unrelated files.

## Governance

This Constitution supersedes conflicting practices described elsewhere in the repository,
including the informal root-level `CONSTITUTION.md` (which now just points back to this file).
Where a requirement conflicts with this
document, resolve in this priority order: (1) explicit user requirement, (2) the current feature
specification, (3) this Constitution's architecture principles, (4) convenience. `CLAUDE.md`
remains the operative runtime guidance file for day-to-day implementation behavior and MUST stay
consistent with this Constitution; where they diverge, this Constitution governs and `CLAUDE.md`
should be updated to match.

Amendment procedure: any change to this file MUST update the Sync Impact Report at the top,
increment `CONSTITUTION_VERSION` per the versioning policy below, and set `Last Amended` to the
date of the change. Ambiguous version-bump decisions MUST be resolved by stating the reasoning
before finalizing.

Versioning policy (semantic versioning applied to governance):
- MAJOR: backward-incompatible governance changes — principle removals or redefinitions that
  change what was previously required.
- MINOR: a new principle or section added, or materially expanded guidance.
- PATCH: clarifications, wording, typo fixes, non-semantic refinements.

Compliance review: a feature is complete only when its acceptance criteria pass, automated tests
pass, schemas validate, error cases are handled, output is inspectable, documentation is updated
where necessary, and no unrelated architectural complexity has been introduced. For the MVP
specifically, "done" additionally means a user can execute the complete investment committee
workflow for a supported public company from the command line and obtain a usable Investment
Committee Memo — i.e., a ticker can be provided as input; company and financial data can be
retrieved; research is synthesized; Bull and Bear cases are generated independently; a
deterministic valuation is calculated; the Committee Chair evaluates the evidence; a structured
Investment Committee Memo is produced; material claims trace to a source or are explicitly
labeled as assumptions; and the workflow repeats across companies (initial targets: ASML,
NVIDIA, Microsoft, Apple, Alphabet, Amazon — ASML is the first end-to-end validation case)
without changing application code.

**Version**: 1.0.0 | **Ratified**: 2026-08-09 | **Last Amended**: 2026-08-09
