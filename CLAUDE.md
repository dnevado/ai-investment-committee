# CLAUDE.md — AI Investment Committee

## Mission

You are the engineering team building AI Investment Committee (AIC).

AIC is an AI-assisted investment research workflow.

The MVP analyzes a company through:

```text
Data
 → Research
 → Bull
 → Bear
 → Valuation assumptions
 → Deterministic DCF
 → Committee
 → Memo
```

Your priority is correctness, testability and learning speed.

---

# Engineering principles

## 1. Small increments

Implement one task/iteration at a time.

Never implement the whole roadmap unless explicitly requested.

After each meaningful change:

1. run tests
2. inspect failures
3. fix
4. report what changed

## 2. Domain first

Business logic belongs in domain/application modules.

Do not put investment logic inside:
- OpenAI adapters
- LangGraph nodes
- CLI
- AWS infrastructure

## 3. LLMs do not own arithmetic

The LLM may propose assumptions.

Python calculates:
- DCF
- enterprise value
- equity value
- implied price
- scenario deltas

## 4. Providers are replaceable

Depend on protocols/interfaces.

The application must be testable without:
- OpenAI
- external financial APIs
- AWS

## 5. Structured outputs

LLM outputs must be validated with Pydantic.

Never trust raw model text as application state.

## 6. Prompts are production code

Prompt changes require:
- tests where possible
- representative fixtures
- evaluation against prior behavior

## 7. No premature infrastructure

Do not introduce AWS services until local functionality works.

The MVP should run locally.

---

# Technology stack

Use:

- Python 3.12+
- Pydantic
- LangChain only where useful for model/provider integration
- LangGraph for orchestration
- OpenAI as initial LLM provider
- SQLite locally
- AWS later for deployment

Avoid unnecessary dependencies.

---

# Architecture

Preferred dependency direction:

```text
CLI
 ↓
Application
 ↓
Domain
 ↑
Infrastructure
```

Infrastructure implements protocols defined by the application/domain boundary.

Agents should be application services, not domain models.

---

# LangGraph rules

LangGraph is orchestration.

Do not put:
- DCF formulas
- provider-specific code
- persistence logic
- complex business rules

inside graph nodes.

Nodes should call testable services.

Keep graph state explicit and typed.

---

# Agent rules

Each agent has one responsibility.

Research:
> establish evidence.

Bull:
> construct upside case.

Bear:
> attack thesis.

Valuation:
> propose assumptions.

Committee:
> adjudicate evidence, valuation and asymmetry.

Do not turn every task into an agent.

---

# Data rules

Every material external fact should preserve source metadata.

Do not silently mix:
- currencies
- fiscal periods
- annual and quarterly data
- reported and adjusted metrics

When uncertain, fail explicitly or mark the uncertainty.

---

# Testing strategy

Use three layers:

## Unit

Pure deterministic functions.

Examples:
- DCF
- validation
- transformations

## Contract

Provider and agent interfaces.

Use fake providers.

## End-to-end

Mock external providers initially.

Then run real-provider evaluation separately.

---

# Required test commands

At minimum:

```bash
pytest
```

If configured:

```bash
ruff check .
mypy src
```

Do not claim success without actually running the relevant command.

---

# Git discipline

Prefer small commits such as:

```text
feat(domain): add investment committee models
feat(valuation): add deterministic dcf
feat(agent): add research agent
feat(graph): add committee workflow
test(valuation): add scenario coverage
```

Do not mix unrelated changes.

---

# Working style

Before implementing:

1. Read relevant spec.
2. Inspect existing repository.
3. Identify dependencies.
4. State the smallest implementation.
5. Implement.
6. Test.
7. Report.

If requirements conflict, prefer:
1. explicit user requirement
2. current specification
3. architecture
4. convenience

---

# Do not

- invent APIs
- invent financial data
- hard-code secrets
- bypass Pydantic validation
- call OpenAI directly from domain code
- add RAG/vector DB to MVP
- add AWS before local validation
- create autonomous loops without explicit requirement
- rewrite unrelated files

---

# Definition of done

A task is complete only when:

- implementation exists
- tests exist where appropriate
- tests pass
- no obvious lint/type errors remain
- behavior matches the specification
- limitations are documented

---

# Current MVP sequence

Follow:

```text
Iteration 0 Repository
Iteration 1 Domain
Iteration 2 DCF
Iteration 3 LLM contract
Iteration 4 Research
Iteration 5 Bull/Bear
Iteration 6 Valuation
Iteration 7 Committee
Iteration 8 LangGraph
Iteration 9 First vertical slice
Iteration 10 Real ASML
Iteration 11 Multi-company
```

Do not skip directly to AWS or UI.

# MVP public validation

The MVP is now technically converged.

Before major architectural rework, the next objective is to validate the product with the target audience.

The public validation layer includes:

- brand identity
- public landing page
- clear value proposition
- primary CTA
- simple user registration
- controlled access to the MVP
- analytics
- user feedback
- conversion measurement

The public validation layer must not alter the investment-analysis domain.

The landing page is a product-validation interface, not part of the investment engine.

Do not introduce major backend or architectural changes solely to support the landing page.

The purpose of this phase is to answer:

> Do real target users understand the product, trust the proposition, and want to use the investment committee workflow?

Success should be measured through observable user behavior rather than subjective opinions alone.

# Public product identity

The public product brand is:

**Quorum**

Tagline:

> Research the case. Challenge the thesis. Make the decision.

Public positioning:

> Evidence-backed investment research built for better investment decisions.

Quorum is the public-facing brand of the AI-assisted investment research system.

Public-facing materials must use "Quorum" rather than "AI Investment Committee" as the primary product name.

The product should feel:
- institutional
- analytical
- credible
- premium
- evidence-driven
- restrained

Avoid:
- hype
- trading-gamification
- crypto aesthetics
- generic AI-SaaS visual language
- promises of investment returns

The public MVP exists to validate demand with real users before major architectural expansion.

Do not sacrifice domain correctness or deterministic financial logic for marketing/UI changes.