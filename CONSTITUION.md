# AI Investment Committee — Project Constitution

**Version:** 0.1
**Status:** Active
**Last Updated:** 2026-08-09

## 1. Purpose

AI Investment Committee (AIC) is an AI-assisted investment research product designed to help investors analyze public companies through a structured investment committee process.

The MVP must demonstrate one core capability:

> Given a public company ticker, produce a structured, evidence-based Investment Committee Memo containing financial analysis, a Bull Case, a Bear Case, valuation scenarios, risks, assumptions, and a final committee decision.

The system is an **investment research and decision-support tool**, not an autonomous trading system and not a financial advisor.

---

# 2. Core Product Principles

## Principle 1 — Evidence Before Opinion

Every material investment claim must be grounded in identifiable evidence.

The system must distinguish between:

* Facts
* Derived calculations
* Assumptions
* Interpretations
* Opinions

The LLM must never present an unsupported assumption as a factual statement.

---

## Principle 2 — LLMs Reason; Code Calculates

LLMs are responsible for:

* synthesis
* reasoning
* interpretation
* hypothesis generation
* argument construction
* committee deliberation

Deterministic application code is responsible for:

* financial calculations
* DCF calculations
* multiples
* scenario calculations
* percentages
* aggregation
* validation

Rule:

> **LLM proposes. Code computes.**

---

## Principle 3 — Structured Outputs

All material LLM outputs must use explicit typed schemas.

Preferred technology:

* Pydantic
* OpenAI structured outputs
* LangGraph state schemas

Free-form text must not be used as an internal interface between agents.

---

## Principle 4 — Bull and Bear Must Be Symmetric

The product must not be designed to confirm a predefined investment thesis.

For every investment analysis:

* Bull Agent argues the strongest credible upside case.
* Bear Agent argues the strongest credible downside case.
* Committee Agent evaluates both.

The Bear Case must actively attempt to invalidate the investment thesis.

---

## Principle 5 — Explicit Assumptions

Investment conclusions must expose the assumptions that drive them.

Examples:

* Revenue growth
* Operating margin
* FCF conversion
* WACC
* Terminal growth
* Valuation multiple
* Market growth
* Competitive assumptions

A user must be able to understand:

> "What would have to be true for this conclusion to be correct?"

---

## Principle 6 — Deterministic Valuation

Financial calculations must be implemented in Python or equivalent deterministic code.

The LLM may propose assumptions but must not directly perform or control the mathematical implementation of the valuation engine.

The valuation engine must be independently testable.

---

## Principle 7 — Traceability

Material data points and claims should retain source metadata whenever possible.

A source should contain enough information to identify:

* provider
* dataset/document
* publication date
* retrieval date
* relevant field or location

The system must avoid presenting generated information as sourced information.

---

## Principle 8 — Minimal Architecture

The MVP must optimize for:

* speed of development
* simplicity
* debuggability
* low operating cost
* ability to change components

The MVP must NOT introduce infrastructure unless there is a demonstrated need.

Explicitly excluded from MVP:

* RAG
* vector database
* pgvector
* Kubernetes
* microservices
* Kafka
* Redis
* complex event-driven architecture
* autonomous agent-to-agent communication
* frontend application
* portfolio management
* broker integration

---

## Principle 9 — No RAG in MVP

The MVP uses:

* structured financial data
* controlled public sources
* explicit source metadata
* direct model context

Document ingestion and RAG may be introduced later if user validation demonstrates that structured data is insufficient.

---

## Principle 10 — Provider Abstraction

The initial LLM provider is OpenAI.

However, the application domain must not be tightly coupled to OpenAI-specific implementation details.

The architecture should permit future support for other LLM providers without rewriting the domain model or investment logic.

---

# 3. Architecture Principles

The initial architecture consists of:

```text
CLI
  ↓
Application Layer
  ↓
LangGraph
  ↓
Agents
  ↓
Data Providers
  ↓
Financial Engine
```

Initial technologies:

* Python 3.12+
* LangGraph
* LangChain where useful
* OpenAI API
* Pydantic
* SQLite
* pytest

AWS and PostgreSQL are deferred until the vertical slice has been validated.

---

# 4. Agent Design Principles

Agents must be:

* single-purpose
* explicitly scoped
* deterministic in their interface
* independently testable

Initial agents:

1. Research Agent
2. Bull Agent
3. Bear Agent
4. Committee Chair

The valuation engine is not an agent.

Agents must not recursively create or invoke arbitrary other agents.

The graph topology must remain explicit.

---

# 5. Investment Decision Principles

The Committee Chair must not simply average Bull and Bear outputs.

It must:

1. Identify the central investment thesis.
2. Identify supporting evidence.
3. Identify assumptions.
4. Identify disagreements.
5. Assess valuation.
6. Assess downside risks.
7. Identify invalidation conditions.
8. Produce a recommendation.
9. Assign a conviction score with explanation.

Recommendations in MVP:

* BUY
* WATCH
* AVOID

These recommendations are research outputs, not personalized financial advice.

---

# 6. Quality Principles

Every feature must include:

* unit tests
* schema validation
* error handling
* acceptance criteria
* relevant evaluation cases

Agent features must additionally include:

* structured-output tests
* evidence/attribution tests
* hallucination/unsupported-claim tests where practical
* cost measurement
* latency measurement

---

# 7. Observability

The system must measure at minimum:

* analysis duration
* LLM calls
* token usage where available
* estimated LLM cost
* failed runs
* completed runs
* source count
* validation failures

The MVP must make it possible to answer:

> How much does one completed investment analysis cost?

---

# 8. Development Principles

Claude Code is the primary implementation agent.

Spec Kit is used to define requirements and implementation plans.

Development workflow:

```text
Specify
   ↓
Clarify
   ↓
Plan
   ↓
Tasks
   ↓
Implement
   ↓
Test
   ↓
Evaluate
   ↓
Review
```

Claude Code must not introduce architectural components that are not required by the current specification.

---

# 9. Scope Discipline

When implementing a feature, Claude Code must:

* modify only necessary files
* avoid speculative abstractions
* avoid premature optimization
* avoid adding infrastructure without justification
* preserve existing behavior
* run relevant tests

If a requirement conflicts with this Constitution, the conflict must be explicitly identified before implementation.

---

# 10. Definition of Done

A feature is complete only when:

* acceptance criteria pass
* automated tests pass
* schemas validate
* error cases are handled
* output is inspectable
* documentation is updated where necessary
* no unrelated architectural complexity has been introduced

For the MVP, "done" additionally means:

> A user can execute the complete investment committee workflow for a supported public company from the command line and obtain a usable Investment Committee Memo.

---

# 11. MVP Success Criterion

The MVP is successful if:

1. A company ticker can be provided as input.
2. Company and financial information can be retrieved.
3. Research can be synthesized.
4. Bull and Bear cases are generated independently.
5. A deterministic valuation is calculated.
6. A Committee Chair evaluates the evidence.
7. A structured Investment Committee Memo is generated.
8. Material claims can be traced to their source or explicitly labeled as assumptions.
9. The workflow can be repeated for multiple companies without changing application code.

The first target companies are:

* ASML
* NVIDIA
* Microsoft
* Apple
* Alphabet
* Amazon

ASML is the first end-to-end validation case.
