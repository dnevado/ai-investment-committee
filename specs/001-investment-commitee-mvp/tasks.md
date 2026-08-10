# AI Investment Committee — MVP Implementation Tasks

**Specification:** 001-investment-committee-mvp
**Version:** 0.1
**Status:** Ready for implementation
**Date:** 2026-08-09

---

# 1. Implementation Strategy

The MVP must be implemented as a sequence of small, verifiable increments.

The implementation order is intentional:

```text
Repository
    ↓
Domain
    ↓
Data
    ↓
Valuation
    ↓
LLM abstraction
    ↓
Agents
    ↓
LangGraph
    ↓
Memo
    ↓
End-to-end evaluation
```

Do not implement the entire graph before the underlying components are tested independently.

---

# 2. Task 001 — Repository Bootstrap

## Objective

Create the initial Python project structure.

## Tasks

Create:

```text
pyproject.toml
src/aic/
tests/
data/
outputs/
analyze.py
.env.example
.gitignore
README.md
```

Configure:

* Python 3.12+
* pytest
* ruff
* mypy or equivalent type checking
* Pydantic
* LangGraph
* LangChain where required
* OpenAI SDK
* SQLite support

## Acceptance Criteria

```text
□ Python project installs successfully
□ pytest executes
□ lint executes
□ type checking executes
□ imports work
□ no application logic yet
```

---

# 3. Task 002 — Domain Models

## Objective

Implement the core domain models.

Create:

```text
src/aic/domain/models/
    company.py
    financials.py
    research.py
    valuation.py
    committee.py
```

Implement:

* Company
* FinancialPeriod
* MarketData
* Source
* Claim
* ResearchReport
* BullCase
* BearCase
* ValuationAssumptions
* ValuationScenario
* ValuationResult
* CommitteeDecision

Use Pydantic where external/LLM validation is required.

## Tests

Create:

```text
tests/unit/domain/
```

Test:

* required fields
* optional fields
* enum constraints
* numeric validation
* serialization/deserialization

## Acceptance Criteria

All models can be instantiated and serialized.

---

# 4. Task 003 — Provider Protocols

## Objective

Define interfaces for external dependencies.

Create:

```text
src/aic/domain/protocols/
    data_provider.py
    llm_provider.py
    repository.py
```

Define protocols for:

```text
FinancialDataProvider
LLMProvider
AnalysisRepository
```

## Acceptance Criteria

Domain/application code can depend on protocols rather than concrete providers.

No OpenAI or provider SDK imports in domain models.

---

# 5. Task 004 — Configuration

## Objective

Create centralized application configuration.

Create:

```text
src/aic/config.py
```

Support:

```text
OPENAI_API_KEY
LLM_MODEL
DATA_PROVIDER_API_KEY
DATABASE_URL
```

Provide safe defaults where appropriate.

## Acceptance Criteria

```text
□ .env.example exists
□ secrets are not hard-coded
□ missing mandatory configuration produces clear errors
□ configuration can be injected during tests
```

---

# 6. Task 005 — Company Resolver

## Objective

Implement company/ticker resolution.

Create:

```text
src/aic/infrastructure/data/
    company_provider.py
```

The resolver must return:

```text
Company
```

for supported tickers.

Initial target:

```text
ASML
NVDA
MSFT
AAPL
GOOG
AMZN
```

Avoid hard-coding financial data.

Ticker mapping may be configuration/provider-specific.

## Tests

Mock the external provider.

Test:

* valid ticker
* invalid ticker
* missing fields
* provider failure

---

# 7. Task 006 — Financial Data Provider

## Objective

Implement the first financial data adapter.

The provider must retrieve, where available:

```text
revenue
gross profit
operating income
net income
operating cash flow
capex
free cash flow
cash
debt
shares outstanding
```

and market data:

```text
price
market cap
currency
as_of
```

All data must be converted into domain models.

## Important

The provider must not leak SDK-specific objects into the domain.

---

# 8. Task 007 — Source Tracking

## Objective

Ensure every external dataset retains source metadata.

Implement:

```text
Source
```

and source propagation through:

```text
FinancialPeriod
MarketData
Claim
```

Minimum metadata:

```text
provider
dataset
retrieved_at
```

## Acceptance Criteria

A financial value can be traced to its provider/source metadata.

---

# 9. Task 008 — SQLite Repository

## Objective

Implement minimal persistence.

Create:

```text
src/aic/infrastructure/persistence/
    sqlite.py
```

Store:

```text
analysis_id
ticker
created_at
status
model
duration
estimated_cost
output_path
```

Optionally store the structured result as JSON.

## Tests

Test using a temporary SQLite database.

Do not use production files in tests.

---

# 10. Task 009 — Deterministic DCF Engine

## Objective

Implement the valuation engine independently of LangGraph and LLMs.

Create:

```text
src/aic/valuation/
    dcf.py
    scenarios.py
```

Implement:

```text
Revenue projection
Operating profit
Taxes
NOPAT
FCF
Terminal value
Discounting
Enterprise value
Equity value
Implied share price
```

## Critical Requirement

No LLM calls.

No LangChain.

No LangGraph.

Pure deterministic Python.

---

# 11. Task 010 — DCF Test Suite

## Objective

Prove valuation correctness before connecting it to AI.

Create:

```text
tests/unit/valuation/
    test_dcf.py
    test_scenarios.py
```

Test:

1. known simple DCF
2. zero-growth company
3. different WACC
4. different terminal growth
5. Bear scenario
6. Base scenario
7. Bull scenario
8. invalid WACC
9. terminal growth >= WACC
10. missing required inputs

## Acceptance Criterion

The DCF engine must pass all deterministic tests before Task 014.

---

# 12. Task 011 — OpenAI Provider Adapter

## Objective

Implement the OpenAI adapter behind `LLMProvider`.

Create:

```text
src/aic/infrastructure/llm/
    openai.py
```

Responsibilities:

* initialize OpenAI client
* send structured-output requests
* capture token usage where available
* return validated domain models

The rest of the application must not depend directly on the OpenAI SDK.

---

# 13. Task 012 — Prompt Infrastructure

## Objective

Create version-controlled prompts.

Create:

```text
src/aic/agents/prompts/
    research.txt
    bull.txt
    bear.txt
    committee.txt
```

Each prompt must define:

```text
ROLE
OBJECTIVE
AVAILABLE CONTEXT
RULES
OUTPUT REQUIREMENTS
```

Prompts must not contain company-specific facts.

---

# 14. Task 013 — Research Agent

## Objective

Implement the Research Agent.

Create:

```text
src/aic/agents/research.py
```

Input:

```text
Company
Financials
MarketData
Sources
```

Output:

```text
ResearchReport
```

The agent must:

* summarize business
* identify financial trends
* identify growth drivers
* identify risks
* create claims
* reference source IDs
* distinguish facts from assumptions

## Tests

Mock the LLM.

Verify:

```text
LLM output
 ↓
Pydantic validation
 ↓
ResearchReport
```

---

# 15. Task 014 — Bull Agent

## Objective

Implement the Bull Agent.

Create:

```text
src/aic/agents/bull.py
```

Input:

```text
Company
ResearchReport
Financials
```

Output:

```text
BullCase
```

Must identify:

* strongest upside thesis
* catalysts
* assumptions
* evidence

It must not simply output "BUY".

---

# 16. Task 015 — Bear Agent

## Objective

Implement the Bear Agent.

Create:

```text
src/aic/agents/bear.py
```

Input:

```text
Company
ResearchReport
Financials
```

Output:

```text
BearCase
```

Must identify:

* downside thesis
* thesis breakers
* risks
* fragile assumptions
* evidence

The Bear Case should challenge the Bull Case.

---

# 17. Task 016 — Valuation Assumption Agent

## Objective

Create a small structured LLM step that proposes valuation assumptions.

Create:

```text
src/aic/agents/valuation.py
```

Input:

```text
ResearchReport
BullCase
BearCase
Financials
```

Output:

```text
ValuationAssumptions
```

Required:

```text
revenue_cagr
operating_margin
tax_rate
wacc
terminal_growth
projection_years
```

## Critical Rule

The agent proposes assumptions.

It does not calculate valuation.

---

# 18. Task 017 — LangGraph State

## Objective

Implement the graph state.

Create:

```text
src/aic/graph/state.py
```

Implement:

```text
InvestmentCommitteeState
```

The state must contain only data required by the workflow.

---

# 19. Task 018 — LangGraph Workflow

## Objective

Implement the complete graph.

Create:

```text
src/aic/graph/investment_committee.py
```

Initial graph:

```text
START
  ↓
load_company
  ↓
load_financials
  ↓
research
  ↓
 ┌───────┴───────┐
 ↓               ↓
bull             bear
 └───────┬───────┘
         ↓
valuation_assumptions
         ↓
valuation
         ↓
committee
         ↓
generate_memo
         ↓
END
```

Bull and Bear may execute independently where supported.

Do not introduce dynamic agent loops.

---

# 20. Task 019 — Committee Chair

## Objective

Implement final committee synthesis.

Create:

```text
src/aic/agents/committee.py
```

Input:

```text
ResearchReport
BullCase
BearCase
ValuationResult
Sources
```

Output:

```text
CommitteeDecision
```

The Chair must produce:

```text
recommendation
conviction
thesis
key_assumptions
key_risks
catalysts
invalidation_conditions
disagreements
```

Recommendation:

```text
BUY
WATCH
AVOID
```

Conviction:

```text
1-10
```

---

# 21. Task 020 — Markdown Renderer

## Objective

Create deterministic Markdown generation.

Create:

```text
src/aic/presentation/markdown.py
```

Input:

```text
ResearchReport
BullCase
BearCase
ValuationResult
CommitteeDecision
Sources
```

Output:

```text
Markdown string
```

Sections:

```text
Executive Summary
Business Overview
Financial Analysis
Bull Case
Bear Case
Valuation
Risks
Catalysts
Invalidation Conditions
Committee Decision
Sources
```

Do not use an LLM to generate the document structure.

---

# 22. Task 021 — Application Service

## Objective

Create the complete application use case.

Create:

```text
src/aic/application/services/
    investment_analysis.py
```

The service should:

1. create analysis ID
2. resolve company
3. load financial data
4. execute graph
5. persist analysis
6. write memo
7. return result

External dependencies must be injected.

---

# 23. Task 022 — CLI

## Objective

Implement the user-facing CLI.

Create/complete:

```text
analyze.py
```

Usage:

```bash
python analyze.py ASML
```

Optional:

```bash
python analyze.py ASML --output outputs/asml.md
```

Display:

```text
✓ Company resolved
✓ Financial data retrieved
✓ Research completed
✓ Bull case completed
✓ Bear case completed
✓ Valuation completed
✓ Committee completed
✓ Memo generated
```

The CLI must remain thin.

---

# 24. Task 023 — End-to-End Test

## Objective

Create an end-to-end test with mocked external providers.

Test:

```text
CLI
 ↓
Application
 ↓
Graph
 ↓
Agents
 ↓
DCF
 ↓
Committee
 ↓
Markdown
```

Use deterministic mock responses for LLM agents.

Acceptance:

The complete workflow produces a valid memo.

---

# 25. Task 024 — ASML Real Evaluation

## Objective

Run the first real analysis.

Command:

```bash
python analyze.py ASML
```

Use real:

* financial provider
* OpenAI
* valuation engine

Inspect:

* financial accuracy
* Bull Case
* Bear Case
* valuation
* committee decision
* sources
* cost
* latency

This is an evaluation task, not a coding task.

---

# 26. Task 025 — Multi-Company Evaluation

Run:

```text
ASML
NVDA
MSFT
AAPL
GOOG
AMZN
```

Record:

```text
completion
latency
cost
financial correctness
citation/source quality
Bull quality
Bear quality
Committee quality
hallucinations
```

---

# 27. Task 026 — MVP Hardening

Only after real evaluation.

Fix:

* data issues
* schema failures
* prompt weaknesses
* valuation edge cases
* source traceability
* error handling
* cost problems
* latency problems

Do not add new product functionality.

---

# 28. Task 027 — MVP Review

Conduct a product review using the following questions:

### Question 1

Is the memo genuinely useful?

### Question 2

Does the Bear Case challenge the thesis?

### Question 3

Can we trust the financial numbers?

### Question 4

Can we understand the valuation assumptions?

### Question 5

Can we identify why the Committee reached its conclusion?

### Question 6

Would an investor use this instead of doing the analysis manually?

### Question 7

Would the investor pay for it?

---

# 29. Implementation Order

Claude Code must execute tasks in this order:

```text
001 Repository
002 Domain Models
003 Protocols
004 Configuration
005 Company Resolver
006 Financial Provider
007 Sources
008 SQLite
009 DCF
010 DCF Tests
011 OpenAI Adapter
012 Prompts
013 Research Agent
014 Bull Agent
015 Bear Agent
016 Valuation Assumptions
017 Graph State
018 LangGraph
019 Committee
020 Markdown
021 Application Service
022 CLI
023 E2E
024 ASML Evaluation
025 Multi-Company Evaluation
026 Hardening
027 MVP Review
```

---

# 30. Parallelization

Tasks may be parallelized only when dependencies allow it.

Safe examples:

```text
002 Domain
    +
004 Configuration
```

or:

```text
009 DCF
    +
011 OpenAI Adapter
```

Do not parallelize tasks where one depends materially on the output of another.

---

# 31. Milestones

## Milestone 1 — Technical Foundation

Tasks:

```text
001-004
```

Result:

> Clean Python project with domain models and configuration.

---

## Milestone 2 — Financial Engine

Tasks:

```text
005-010
```

Result:

> Reliable company data + deterministic DCF.

At this point the project can already calculate an investment valuation without AI.

---

## Milestone 3 — AI Reasoning

Tasks:

```text
011-016
```

Result:

> Individual investment research agents work independently.

---

## Milestone 4 — Committee

Tasks:

```text
017-023
```

Result:

> Complete end-to-end workflow.

---

## Milestone 5 — Validation

Tasks:

```text
024-027
```

Result:

> Evidence about whether the product actually works.

---

# 32. Claude Code Execution Rule

Claude Code should normally implement **one task at a time**.

After each task:

```text
Implement
 ↓
Test
 ↓
Review
 ↓
Commit
```

Do not implement 10 tasks and test at the end.

---

# 33. Task Completion Format

After completing a task, Claude Code should report:

```text
Task: 009 — Deterministic DCF Engine

Status: COMPLETE

Implemented:
- ...
- ...

Tests:
- ...
- ...

Files:
- ...
- ...

Architecture impact:
None

Known limitations:
- ...

Next task:
010 — DCF Test Suite
```

---

# 34. Definition of MVP Complete

The MVP is complete only when:

```text
□ ASML analysis works end-to-end
□ DCF tests pass
□ structured agent outputs validate
□ sources are preserved
□ memo is generated
□ cost is measured
□ latency is measured
□ at least 3 additional companies work
□ no critical hallucination is found in evaluation
□ Bull and Bear cases are meaningfully differentiated
□ Committee decision is explainable
```

---

# 35. Final Rule

Do not optimize for the number of features implemented.

Optimize for learning.

The most valuable output of this MVP is not the code.

It is the answer to:

> **Can this AI Investment Committee produce investment research that a sophisticated investor considers materially better or faster than their current workflow?**
