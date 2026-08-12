<p align="center">
  <img src=".github/assets/logo.svg" width="140" alt="AI Investment Committee logo" />
</p>

<h1 align="center">AI Investment Committee</h1>
<p align="center"><strong>Institutional-grade investment research, without the institution.</strong></p>

<p align="center">
  <img alt="Status" src="https://img.shields.io/badge/status-MVP%20in%20development-orange" />
  <img alt="Python" src="https://img.shields.io/badge/python-3.12%2B-3776AB?logo=python&logoColor=white" />
  <img alt="Tests" src="https://img.shields.io/badge/tests-155%20passing-2ea44f?logo=pytest&logoColor=white" />
  <img alt="Architecture" src="https://img.shields.io/badge/architecture-domain--first-1B3A6B" />
</p>

AIC turns a public company ticker into a structured, evidence-based **Investment Committee
Memo** — the kind of document a real investment committee produces after a debate, not the kind
a chatbot produces after a prompt.

```text
Data → Research → Bull → Bear → Valuation Assumptions → Deterministic DCF → Committee → Memo
```

*Research and decision-support tool. Not a trading system. Not financial advice.*

---

## 🔍 The problem

Serious investment research is a debate: someone builds the case, someone else tries to break
it, and a decision-maker weighs both against a valuation before committing capital. That process
is expensive, slow, and out of reach for most individual investors and small funds.

The AI shortcut everyone reaches for instead — "ask a chatbot to analyze this stock" — skips the
debate entirely. One model plays researcher, bull, bear, and judge at once, and does arithmetic
along the way. The result reads confidently and can't be trusted: there's no way to tell which
sentence is a fact, which is a calculation, and which is the model improvising.

## 🏛️ The product

AIC rebuilds that committee process as software. A ticker goes in; a memo comes out — and every
claim in it can be traced back to evidence, an explicit assumption, or a deterministic
calculation.

```text
┌─────────┐  ┌──────────┐  ┌──────┐  ┌──────┐  ┌────────────┐  ┌─────┐  ┌───────────┐  ┌──────┐
│  Data   │→ │ Research │→ │ Bull │→ │ Bear │→ │ Valuation  │→ │ DCF │→ │ Committee │→ │ Memo │
│         │  │          │  │      │  │      │  │ Assumptions│  │(det)│  │  (adjud.) │  │      │
└─────────┘  └──────────┘  └──────┘  └──────┘  └────────────┘  └─────┘  └───────────┘  └──────┘
```

| | Stage | Role |
|---|---|---|
| 📊 | **Data** | Structured company and financial data — the only permitted starting point. |
| 🔎 | **Research** | Establishes the evidence base from that data. |
| 🐂 | **Bull** | Builds the strongest credible upside case. |
| 🐻 | **Bear** | Actively tries to invalidate it. |
| 📐 | **Valuation** | Proposes growth, margin, and discount-rate assumptions — as a proposal, never a calculation. |
| 🧮 | **DCF** | Deterministic Python. Same inputs, same output, every time, independently auditable. |
| ⚖️ | **Committee** | Adjudicates evidence, valuation, and asymmetry — does not average Bull and Bear. |
| 📄 | **Memo** | The structured, human-readable artifact a person can read, question, and trust. |

Every memo ends in a recommendation of `BUY`, `WATCH`, or `AVOID` — a research output, not
personalized financial advice, with the reasoning behind it fully exposed.

## 🛡️ Why it's defensible

The rule that makes AIC trustworthy — and hard to copy by prompting a single model harder — is
enforced in the architecture, not just the wording of a prompt:

> **The LLM proposes. The code computes.**

Every dollar figure in a memo — enterprise value, equity value, implied share price, scenario
deltas — comes from a deterministic, independently-tested valuation engine that never touches an
LLM. Models handle synthesis, argument, and judgment; they are structurally incapable of
inventing a number that matters.

| | Principle | What it means in practice |
|---|---|---|
| 🔍 | **Evidence before opinion** | Every material claim is tagged as fact, calculation, assumption, or opinion — never blurred together. |
| ⚖️ | **Bull and Bear are symmetric** | The Bear agent is instructed to actually try to kill the thesis, not to be a token counterpoint. |
| 📐 | **Explicit assumptions** | Every valuation exposes what would have to be true for its conclusion to hold. |
| 🔗 | **Traceability** | Material data points carry source metadata — provider, document, publication and retrieval date. Generated content is never presented as sourced. |
| 🧩 | **Structured outputs only** | All agent output is schema-validated. Free-form text is never used as an inter-agent interface — so behavior is testable, not just plausible-sounding. |
| 🔌 | **Provider abstraction** | The domain model doesn't know which LLM vendor it's talking to — no lock-in baked into the architecture. |

## 🧭 Where this goes

The MVP targets a single workflow — one ticker, one memo, run from the command line — as proof
that the adversarial-committee approach produces research worth trusting. Validated on that,
the same architecture extends naturally toward:

- **Portfolio-scale coverage** — running the committee across a watchlist, not one ticker at a time.
- **A reviewable research platform** — memos as a queryable, comparable archive, not one-off documents.
- **Deeper evidence sources** — richer filings and market data behind the same evidence/assumption discipline.
- **A team workflow** — the Committee Chair output as a structured starting point for a *human* investment committee, not a replacement for one.

None of that is built yet, and none of it gets built before the core workflow is proven end to
end on real companies — see [Principle 8, Minimal Architecture](.specify/memory/constitution.md).
Sequencing discipline is itself part of the product bet: prove the workflow before scaling it.

---

## 📊 Status: MVP in active development

AIC is built iteration by iteration, each one specified, planned, and tested before the next
begins ([`specs/`](specs/), governed by [`.specify/memory/constitution.md`](.specify/memory/constitution.md)).

| Iteration | Scope | Status |
|---|---|---|
| 0 | Repository bootstrap | ✅ Done |
| 1 | Domain model (Company, Money, Evidence, Thesis, Valuation, Decision…) | ✅ Done |
| 2 | Deterministic DCF valuation engine | ✅ Done |
| 3 | LLM provider contract | ✅ Done |
| 4 | Research & thesis generation | ✅ Done |
| 5 | Investment Committee Report (composes evidence, DCF, and decision into one memo) | ✅ Done |
| 6 | Bull / Bear adjudication agents | 🚧 Prompts drafted, orchestration pending |
| 7 | Committee chair agent | 🚧 Prompts drafted, orchestration pending |
| 8 | LangGraph orchestration | ⏳ Not started |
| 9 | First end-to-end vertical slice (CLI → memo) | ⏳ Not started |
| 10 | Real ASML validation run | ⏳ Not started |
| 11 | Multi-company support | ⏳ Not started |

**155 unit and contract tests passing.** Every completed layer — domain, valuation, research,
report — is independently validated before the next is wired on top, so the foundation stays
provably correct as the pipeline closes.

**First validation target:**

```text
ASML → structured Investment Committee Memo
```

followed by NVIDIA, Microsoft, Apple, Alphabet, and Amazon. The MVP is successful when the full
pipeline runs for any of them without changing application code.

---

## ⚙️ Under the hood

```text
CLI
 ↓
Application
 ↓
Domain
 ↑
Infrastructure
```

```text
src/aic/
├── domain/     # Company, Money, Currency, Evidence, InvestmentThesis, Valuation, Decision...
├── dcf/        # Deterministic DCF engine — assumptions, engine, result
├── research/   # Evidence-grounded research and thesis generation
├── report/     # Composes thesis + DCF + committee decision into a structured memo
└── agents/     # Bull / Bear / Committee prompts (orchestration pending)
```

- **Domain first** — investment logic lives in `domain/`, `dcf/`, `research/`, `report/`, never
  inside LLM adapters, orchestration nodes, or the CLI.
- **LangGraph is orchestration only** — no valuation formulas or business rules live in graph
  nodes; nodes call testable services.
- **Infrastructure implements protocols** defined at the application/domain boundary, so LLM and
  data providers are replaceable without touching investment logic.
- **Deliberately excluded until proven necessary**: RAG, vector database, Kubernetes,
  microservices, Kafka, Redis, autonomous agent-to-agent communication, frontend, portfolio
  management, broker integration, AWS.

## 💻 For developers

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) for environment and dependency management

### Setup

```powershell
uv venv
uv sync
Copy-Item .env.example .env
```

`uv sync` installs runtime and dev dependencies (pytest, Ruff, mypy) from `pyproject.toml`. Run
everything via `uv run <command>` — no manual activation needed. Configuration loads from
environment variables via `aic.settings.get_settings()`, backed by `.env` (never committed) and
sensible defaults when it's absent.

### Tests and quality checks

```powershell
uv run pytest
uv run ruff check .
uv run mypy src
```

Three test layers, per the constitution: **unit** (pure deterministic functions — DCF math,
validation, transformations), **contract** (provider and agent interfaces against fake
providers), and **end-to-end** (mocked providers first, real-provider evaluation run
separately). Every feature ships with tests, schema validation, and error handling before it's
considered done.

---

## 📜 Governing documents

- [`.specify/memory/constitution.md`](.specify/memory/constitution.md) — ratified product and
  architecture principles; source of truth for scope disputes
- [`CLAUDE.md`](CLAUDE.md) — engineering rules for AI-assisted development in this repo
- [`specs/`](specs/) — per-iteration spec, plan, and task breakdown ([Spec Kit](https://github.com/github/spec-kit) workflow: Specify → Clarify → Plan → Tasks → Implement → Test → Evaluate → Review)
