# Implementation Plan: Public MVP Validation

**Branch**: `011-public-mvp-validation` | **Date**: 2026-08-15 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/011-public-mvp-validation/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command; its definition describes the execution workflow.

## Summary

Build a small, locally-runnable Python web application that presents AIC's brand and value
proposition, shows the already-validated Amazon/AMZN investment example (feature 009/010)
as a static, human-readable snapshot, and captures three things: CTA-driven early-access
registrations, qualitative feedback, and validation-funnel events — all in SQLite. The
Amazon example is captured once from a real `run_investment_workflow` run (no live LLM
calls at request time), converted into a stable presentation/read model, and served as
static content. No DCF, valuation, thesis, bull/bear, or committee logic is touched; the
public layer only reads a snapshot and writes to three small SQLite tables. Actual live
public deployment (domain, TLS, real hosting) is explicitly out of this plan's
implementation scope — this plan produces a deployment-ready application, not a live
deployment (see Constraints).

## Technical Context

**Language/Version**: Python 3.12+ (matches the rest of the repo; no new version
requirement).

**Primary Dependencies**: `fastapi` (web framework — reuses the project's existing
Pydantic investment directly for request/response validation), `uvicorn` (ASGI server,
dev/local run), `jinja2` (server-rendered HTML templates), `python-multipart` (HTML form
parsing for registration/feedback). `httpx` (needed for `TestClient`) is already present
transitively via `openai`. No new LLM, RAG, vector-store, or orchestration dependency —
LangGraph/LangChain remain unused, consistent with the existing baseline (never introduced
because never yet needed).

**Storage**: SQLite (stdlib `sqlite3`), per the constitution's existing "SQLite locally"
baseline. Three tables: `registrations`, `feedback_submissions`, `validation_events`. No
ORM — the tiny, fixed schema doesn't justify one (Constitution VIII).

**Testing**: `pytest` with FastAPI's `TestClient` (Starlette, backed by the already-present
`httpx`) — no real network, no real LLM calls, since the Amazon example is a static
snapshot loaded at startup. `ruff check .` and `mypy src` MUST also pass.

**Target Platform**: Local server process (uvicorn), runnable identically to every other
script in this repo (`uv run ...`). Deployable later behind any ASGI-capable host; this
plan does not select or provision one (see Constraints).

**Project Type**: Web application layer added to the existing single Python project — not
a separate `backend/`/`frontend/` split. The "frontend" here is server-rendered HTML
(Jinja2 templates + minimal CSS/vanilla JS for the registration/feedback forms), not a
separate SPA project, keeping this feature's footprint small per its own Non-Goals
(no design system, no build toolchain).

**Performance Goals**: N/A beyond "responsive for a small validation experiment" — no
stated throughput target; SQLite and server-rendered HTML comfortably handle early-access
validation traffic volumes.

**Constraints**: MUST NOT modify `aic.dcf`, `aic.domain`, `aic.research`, `aic.bullbear`,
`aic.committee`, `aic.report`, or `aic.workflow` (FR-014; spec Non-Goals). MUST NOT make a
real OpenAI call at request-serving time (spec Assumptions: "static demonstration, not live
recomputation"). MUST NOT introduce authentication/sessions (FR-008). Actual live public
hosting (domain registration, TLS certificates, real S3/CDN wiring, DNS) is explicitly
**out of scope for this plan** — this environment has no AWS credentials or domain-control
access to provision those resources, and the constitution defers AWS until local validation
works; this plan's Definition of Done is a fully working, tested, locally-runnable
application that is deployment-ready, not a live URL.

**Scale/Scope**: One new package (`src/aic/public/`), one new script
(`scripts/capture_amazon_snapshot.py`), one static JSON snapshot file, a handful of Jinja2
templates, three SQLite tables, ~6-8 HTTP routes.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Check | Result |
|---|---|---|
| I. Evidence Before Opinion | Presentation model preserves FACT/CALCULATION/ASSUMPTION labels from the captured snapshot; no new claims invented | PASS |
| II. LLM Proposes, Code Computes | No LLM call in this feature's request path at all (static snapshot); no arithmetic performed here either | PASS |
| III. Structured Outputs Only | Registration/feedback/event payloads are Pydantic models end to end (FastAPI request/response schemas) | PASS |
| IV. Bull/Bear Symmetry | Not touched — snapshot displays the already-generated, already-symmetric Bull/Bear pair unchanged | N/A |
| V. Explicit Assumptions | Snapshot surfaces the same key_assumptions/key_risks already produced by the validated workflow | PASS |
| VI. Deterministic Valuation | Not touched — DCF engine untouched; snapshot is a frozen, already-validated result | PASS |
| VII. Traceability | Snapshot preserves evidence source metadata; presented per FR-005 | PASS |
| **VIII. Minimal Architecture, No Premature Infrastructure** | **Explicit MVP exclusion for "a frontend application" is being knowingly overridden** | **Justified deviation — see below** |
| IX. No RAG in MVP | Not applicable — no retrieval introduced | N/A |
| X. Provider Abstraction | Not touched — no new/duplicated `LLMProvider` | PASS |

**Gap found; explicitly justified (not silently overridden)**: Constitution Principle VIII
lists "a frontend application" among items explicitly excluded from the MVP. Feature 011's
own spec documents this as a deliberate, conscious exception (see spec.md Assumptions
"Constitution interaction"), authorized by an explicit, detailed user requirement and by
the project's own `aic-brand-landing` skill (written in advance specifically to guide this
work) — which the constitution's own Governance section ranks above architecture principles
when the user's requirement is explicit. Recorded formally in Complexity Tracking below.
Every other MVP-VIII exclusion (RAG, vector DB, pgvector, Kubernetes, microservices, Kafka,
Redis, complex event-driven architecture, autonomous agent-to-agent communication) is still
fully honored — this deviation is scoped to "a frontend application" only, and the smallest
version of one this feature can get away with.

No other unjustified violations.

## Project Structure

### Documentation (this feature)

```text
specs/011-public-mvp-validation/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
src/aic/public/                     # new package — the "CLI / Public interface" +
│                                    # "Application" layers for this feature only
├── __init__.py
├── app.py                          # FastAPI app factory + route wiring
├── presentation.py                 # AmazonPresentation read model + builder from
│                                    # a WorkflowResult (or loaded snapshot JSON)
├── registration.py                 # EarlyAccessRegistration model, validation,
│                                    # "qualified" classification (spec Assumptions)
├── feedback.py                     # FeedbackSubmission model (six questions)
├── events.py                       # ValidationEvent model + funnel metric queries
├── storage.py                      # SQLite persistence (Protocol + sqlite3 impl;
│                                    # swappable for tests via an in-memory DB)
├── templates/                      # Jinja2 HTML (landing, registration, feedback,
│                                   #   confirmation)
└── static/                         # minimal CSS/JS (no framework/build step)

data/
└── amazon_snapshot.json            # captured AmazonPresentation, checked into the
                                     # repo; loaded at app startup, never recomputed

scripts/
└── capture_amazon_snapshot.py      # one-off script: runs run_investment_workflow
                                     # for Amazon (real OpenAI call, run manually) and
                                     # writes data/amazon_snapshot.json

tests/unit/public/                  # new, network-free test directory (public_-
│                                    # prefixed basenames from the start, per the
│                                    # 006/007/009/010 lesson on cross-directory
│                                    # test-module collisions)
├── public_fakes.py
├── test_public_presentation.py
├── test_public_registration.py
├── test_public_feedback.py
├── test_public_events.py
├── test_public_storage.py
└── test_public_app.py              # FastAPI TestClient integration tests
```

**Structure Decision**: Single existing Python project, one new package
(`src/aic/public/`) added alongside the existing `aic.dcf`/`aic.research`/`aic.bullbear`/
`aic.committee`/`aic.report`/`aic.workflow` packages — no `backend/`/`frontend/` split, no
new top-level project. `aic.public` depends on `aic.workflow`'s output type
(`WorkflowResult`) only at snapshot-capture time (via the new script); at request-serving
time it depends on nothing from those packages, only on the static JSON snapshot and its
own `storage.py` (SQLite). This keeps the dependency direction from spec.md intact:
`CLI / Public interface (aic.public.app) → Application (aic.public.*) → Domain
(aic.domain, read at capture time only) ↑ Infrastructure (aic.public.storage)`.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|---------------------------------------|
| Constitution VIII: "a frontend application" is explicitly excluded from the MVP, but this feature adds one (`src/aic/public/` + Jinja2 templates) | Feature 011's entire purpose is market validation with real external users, which is impossible without something a browser can render; the spec (explicit, detailed user requirement) and the pre-written `aic-brand-landing` skill both authorize this exception, and the constitution's own Governance section ranks an explicit user requirement above architecture principles | A CLI-only or notebook-only demonstration was rejected because it cannot reach "individual investors, serious retail investors, finance professionals" as the spec's target audience requires, nor can it collect the CTA-click/registration/feedback signals the spec's Success Criteria (SC-001–SC-006) depend on |
