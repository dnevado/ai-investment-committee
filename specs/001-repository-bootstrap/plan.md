# Implementation Plan: Repository Bootstrap

**Branch**: `001-repository-bootstrap` | **Date**: 2026-08-09 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-repository-bootstrap/spec.md`

## Summary

Establish the minimal, production-quality Python repository foundation for AIC: a `src`-layout
`aic` package, `pyproject.toml` as canonical config, `uv`-managed virtual environment and
dependencies, pytest/Ruff/mypy quality tooling, Pydantic Settings-based configuration loaded from
environment variables (with a safe `.env.example`), a smoke test proving the package imports, a
Windows-PowerShell-first README, an appropriate `.gitignore`, and the `specs/`, `docs/`, `data/`,
`outputs/` directory scaffold. No investment domain logic, LLM/agent code, or cloud infrastructure
is introduced.

## Technical Context

**Language/Version**: Python 3.12+ (verified locally: CPython 3.12.12 via `uv`-managed `.venv`)

**Primary Dependencies**: `pydantic` + `pydantic-settings` (runtime); `pytest`, `ruff`, `mypy` (dev
only, via a `uv` dependency group)

**Storage**: N/A — no persistence in this feature

**Testing**: pytest (single smoke test proving `import aic` succeeds)

**Target Platform**: Local developer machine; Windows PowerShell is the primary documented/
verified shell, standard cross-platform Python tooling elsewhere

**Project Type**: Single Python package (library-style `src`-layout), no web/mobile/service split

**Performance Goals**: N/A — no performance-sensitive runtime code in this feature

**Constraints**: Dependency set must stay minimal (constitution: "Minimal Architecture, No
Premature Infrastructure" and "No RAG in MVP" principles); `uv` is a development-time tool only,
application code must not import or require it (FR-014); must be reproducible from a clean
checkout (SC-001); must work on Windows PowerShell (SC-008)

**Scale/Scope**: One package (`aic`), a handful of files; this is the foundation the later
iterations (domain, DCF, agents, LangGraph) build directly on top of — no scope beyond that here

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle / Section | Applies to this feature? | Status | Notes |
|---|---|---|---|
| I. Evidence Before Opinion | No — no investment claims produced | N/A | Out of scope by design |
| II. LLM Proposes, Code Computes | No — no LLM calls in this feature | N/A | Out of scope by design |
| III. Structured Outputs Only | Yes — application settings are the only "output" this feature produces | PASS | Settings modeled as a typed `pydantic-settings` class, not free-form text |
| IV. Bull/Bear Symmetry | No — no agents in this feature | N/A | Out of scope by design |
| V. Explicit Assumptions | Yes — plan/spec must expose assumptions | PASS | Captured in spec Assumptions section and Research decisions below |
| VI. Deterministic Valuation | No — no valuation logic in this feature | N/A | Out of scope by design |
| VII. Traceability | No — no external data ingestion in this feature | N/A | Out of scope by design |
| VIII. Minimal Architecture, No Premature Infrastructure | Yes — this is the primary gate for a bootstrap feature | PASS | No AWS, Docker, DB, RAG, vector DB, frontend, or broker integration introduced; matches spec's explicit out-of-scope list |
| IX. No RAG in MVP | Yes | PASS | No document ingestion or RAG introduced |
| X. Provider Abstraction | Partially — settings must not hardcode a provider | PASS | Settings module carries no OpenAI/provider-specific fields yet; deferred to the LLM-contract iteration |
| Architecture & Agent Design Constraints (CLI → Application → Domain) | Yes — package skeleton must not pre-empt this direction | PASS | This feature adds no CLI, application, or domain modules — only the package shell and settings, so the dependency direction is not yet exercised or violated |
| Quality, Observability & Development Workflow | Yes — pytest/Ruff/mypy baseline is this feature's core deliverable | PASS | Directly satisfied by FR-003–FR-005 |

No violations identified. No entries required in Complexity Tracking.

## Project Structure

### Documentation (this feature)

```text
specs/001-repository-bootstrap/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md         # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
│   └── package-interface.md
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
pyproject.toml           # Canonical project config: metadata, deps, uv dependency group,
                          # pytest/Ruff/mypy tool configuration
.env.example              # Documents supported env vars (e.g., AIC_ENV) with placeholder values
.gitignore
README.md                 # Local dev instructions (uv-based, Windows PowerShell first)

src/
└── aic/
    ├── __init__.py       # Exposes package version; the "import aic" contract
    └── settings.py        # Pydantic Settings: AppSettings + get_settings()

tests/
└── unit/
    └── test_smoke.py     # Proves `import aic` succeeds (FR-008)

specs/                     # Already present (Spec Kit artifacts, this feature included)
docs/                      # Already present (ARCHITECTURE.md, PRD.md, PROMPTS.md)
data/                      # New: placeholder dir for future data artifacts (FR-011)
outputs/                   # New: placeholder dir for future generated outputs (FR-011)
```

**Structure Decision**: Single-project, `src`-layout Python package (Option 1 from the template).
`specs/` and `docs/` already exist in the repository; this feature adds `data/` and `outputs/` to
complete FR-011, and adds the `aic` package shell, tests, and root-level config files. The source
surface delivered by this feature is limited to exactly `src/aic/__init__.py` and
`src/aic/settings.py` — no agents, prompts, investment domain modules, or LLM integration are part
of this plan.

## Complexity Tracking

*No Constitution Check violations — this section intentionally left empty.*
