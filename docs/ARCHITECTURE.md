# AI Investment Committee — Architecture

**Version:** 0.1
**Status:** MVP 0.1
**Date:** 2026-08-09

---

# 1. Architecture Objective

The architecture exists to validate the core product hypothesis:

> Can a structured AI investment committee produce a useful, evidence-based investment memo for a public company?

The architecture must therefore optimize for:

1. simplicity
2. correctness
3. observability
4. deterministic financial calculations
5. replaceable external providers
6. fast iteration
7. easy evaluation

The MVP is intentionally a **modular monolith**, not a distributed system.

---

# 2. Architectural Decision

## MVP Architecture

```text
                    ┌─────────────────┐
                    │      CLI        │
                    │  analyze.py     │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ Application     │
                    │ Orchestrator    │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │   LangGraph     │
                    │ Investment      │
                    │ Committee       │
                    └────────┬────────┘
                             │
            ┌────────────────┼────────────────┐
            ▼                ▼                ▼
       Research           Bull/Bear       Valuation
         Agent             Agents           Engine
            │                │                │
            └────────────────┼────────────────┘
                             ▼
                    ┌─────────────────┐
                    │ Committee Chair │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ Structured      │
                    │ Decision        │
                    └────────┬────────┘
                             │
                 ┌───────────┴───────────┐
                 ▼                       ▼
              Markdown                 SQLite
               Memo                    Record
```

---

# 3. Architectural Principles

## 3.1 Modular Monolith

All components live in one Python repository.

Do not introduce:

* microservices
* message queues
* service meshes
* containers for individual components
* distributed workers

unless a later specification explicitly requires them.

---

## 3.2 Domain First

Business/domain models must not depend on:

* OpenAI
* LangChain
* LangGraph
* a specific financial data provider
* CLI implementation

The dependency direction should be:

```text
Infrastructure
      ↓
Application
      ↓
Domain
```

Never the reverse.

---

# 4. Repository Structure

```text
ai-investment-committee/
│
├── .claude/
│   └── ...
│
├── .specify/
│   └── ...
│
├── docs/
│   ├── PRD.md
│   ├── ARCHITECTURE.md
│   └── DECISIONS.md
│
├── specs/
│   └── 001-investment-committee-mvp/
│       └── spec.md
│
├── src/
│   └── aic/
│       │
│       ├── domain/
│       │   ├── models/
│       │   │   ├── company.py
│       │   │   ├── financials.py
│       │   │   ├── research.py
│       │   │   ├── valuation.py
│       │   │   └── committee.py
│       │   │
│       │   └── protocols/
│       │       ├── data_provider.py
│       │       └── llm_provider.py
│       │
│       ├── application/
│       │   ├── analyze.py
│       │   └── services/
│       │       └── investment_analysis.py
│       │
│       ├── agents/
│       │   ├── research.py
│       │   ├── bull.py
│       │   ├── bear.py
│       │   └── committee.py
│       │
│       ├── graph/
│       │   ├── state.py
│       │   └── investment_committee.py
│       │
│       ├── valuation/
│       │   ├── dcf.py
│       │   └── scenarios.py
│       │
│       ├── infrastructure/
│       │   ├── data/
│       │   │   └── ...
│       │   ├── llm/
│       │   │   └── openai.py
│       │   ├── persistence/
│       │   │   └── sqlite.py
│       │   └── observability/
│       │       └── logging.py
│       │
│       ├── presentation/
│       │   └── markdown.py
│       │
│       └── config.py
│
├── tests/
│   ├── unit/
│   │   ├── domain/
│   │   ├── valuation/
│   │   └── presentation/
│   │
│   ├── integration/
│   │   ├── agents/
│   │   └── graph/
│   │
│   └── evaluation/
│       └── companies/
│
├── data/
│
├── outputs/
│
├── analyze.py
├── pyproject.toml
├── .env.example
├── .gitignore
└── README.md
```

---

# 5. Layer Responsibilities

## 5.1 Domain

Contains:

* business models
* typed schemas
* interfaces/protocols
* domain-level validation

The domain must be independent from external frameworks.

Example:

```python
class FinancialDataProvider(Protocol):
    ...
```

is acceptable.

Importing LangGraph into domain models is not.

---

# 6. Application Layer

The application layer coordinates the use case:

```text
Analyze Company
```

Responsibilities:

* initialize dependencies
* create analysis context
* execute graph
* persist result
* generate memo
* return result

It must not contain detailed financial calculations.

---

# 7. LangGraph Layer

LangGraph is responsible for workflow orchestration.

The graph represents the investment committee process.

Initial graph:

```text
START
  │
  ▼
load_company
  │
  ▼
load_financials
  │
  ▼
research
  │
  ├──────────────┐
  ▼              ▼
bull            bear
  │              │
  └──────┬───────┘
         ▼
valuation_assumptions
         │
         ▼
valuation
         │
         ▼
committee
         │
         ▼
generate_memo
         │
         ▼
END
```

---

# 8. LangGraph State

State should contain only information required by downstream nodes.

Example:

```python
class InvestmentCommitteeState(TypedDict):
    analysis_id: str
    ticker: str

    company: Company | None
    financials: list[FinancialPeriod]
    market_data: MarketData | None
    sources: list[Source]

    research: ResearchReport | None
    bull_case: BullCase | None
    bear_case: BearCase | None

    valuation_assumptions: ValuationAssumptions | None
    valuation: ValuationResult | None

    committee_decision: CommitteeDecision | None

    errors: list[str]
```

Do not place arbitrary objects or framework-specific state into the graph.

---

# 9. Agent Architecture

Each agent is a thin orchestration layer around an LLM call.

Example:

```text
Agent
 │
 ├── build_prompt()
 │
 ├── invoke_model()
 │
 ├── validate_structured_output()
 │
 └── return_domain_model
```

Agents must not:

* perform database migrations
* calculate DCF
* access environment variables directly
* write files directly
* call arbitrary agents
* modify global state

---

# 10. Research Agent

Input:

```text
Company
Financials
Market Data
Sources
```

Output:

```text
ResearchReport
```

The Research Agent may synthesize supplied data but must not invent unavailable financial facts.

---

# 11. Bull Agent

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

The Bull Agent is explicitly biased toward finding the strongest credible upside argument.

It must remain evidence-based.

---

# 12. Bear Agent

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

The Bear Agent is explicitly responsible for challenging the thesis.

It should identify:

* fragile assumptions
* competitive risks
* valuation risks
* execution risks
* external risks
* thesis breakers

---

# 13. Committee Chair

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

The Chair must reconcile conflicting arguments.

It should not mechanically average scores.

---

# 14. LLM Architecture

OpenAI is the initial LLM provider.

The provider is isolated behind an application/infrastructure boundary.

Conceptually:

```text
Agent
  ↓
LLM Provider Interface
  ↓
OpenAI Adapter
  ↓
OpenAI API
```

The domain must not directly import OpenAI SDK types.

---

# 15. Model Selection

The exact model is configuration, not business logic.

Example:

```text
LLM_MODEL=gpt-...
```

Agents must not hard-code a model identifier.

Model selection may later vary by agent.

For example:

```text
Research       → model A
Bull           → model A
Bear           → model A
Committee      → model B
```

But MVP should use the smallest number of models necessary.

---

# 16. Prompt Architecture

Prompts should be stored separately from business models.

Recommended:

```text
src/aic/agents/prompts/
    research.txt
    bull.txt
    bear.txt
    committee.txt
```

Prompts should specify:

* role
* task
* available context
* constraints
* output requirements

They must not contain company-specific assumptions.

---

# 17. Structured Output

LLM responses must map directly into Pydantic models.

Example:

```text
OpenAI structured output
        ↓
Pydantic validation
        ↓
Domain model
```

If validation fails:

1. retry where appropriate
2. record failure
3. fail explicitly if retry limit is exceeded

Never silently accept malformed output.

---

# 18. Financial Data Architecture

Financial data must be accessed through a provider interface.

```text
FinancialDataProvider
        │
        ├── ProviderA
        │
        └── ProviderB
```

The rest of the application must depend only on the interface.

This allows providers to be replaced without modifying agents or valuation logic.

---

# 19. Source Architecture

Every external data item should retain source metadata.

Source:

```python
class Source:
    id: str
    provider: str
    dataset: str
    url: str | None
    published_at: datetime | None
    retrieved_at: datetime
```

Claims can reference source IDs.

---

# 20. No RAG

The MVP does not contain:

```text
Embeddings
Vector DB
Chunking
Retrieval pipeline
Semantic search
pgvector
```

If additional context is required, the appropriate approach for MVP is to add a structured data source or explicitly scoped source adapter.

---

# 21. Valuation Architecture

The valuation engine is deterministic.

```text
ValuationAssumptions
        ↓
DCF Engine
        ↓
ValuationScenario
```

No LLM is involved in the calculation.

---

# 22. DCF Requirements

The DCF engine should:

1. project revenue
2. project operating profit
3. calculate taxes
4. derive NOPAT
5. derive FCF
6. calculate terminal value
7. discount cash flows
8. calculate enterprise value
9. adjust for cash/debt
10. calculate equity value
11. calculate implied share price

Every step should be independently testable.

---

# 23. Scenario Architecture

Scenarios are explicit objects:

```text
BEAR
BASE
BULL
```

Each scenario contains its own assumptions.

Do not hide scenario differences inside prompt text.

---

# 24. Persistence

SQLite is the initial persistence layer.

Purpose:

* analysis history
* metadata
* cost
* duration
* structured result

The application must use a persistence abstraction so SQLite can later be replaced by PostgreSQL.

---

# 25. File Output

The final memo is generated from structured objects.

Preferred flow:

```text
CommitteeDecision
       +
ValuationResult
       +
ResearchReport
       +
Sources
       ↓
Markdown Renderer
       ↓
.md
```

Do not ask the LLM to generate the complete final document unless explicitly required.

---

# 26. Observability

Every analysis receives:

```text
analysis_id
```

Logs should allow reconstruction of:

```text
start
data retrieval
agent calls
valuation
committee
memo generation
end
```

Record:

* duration
* model
* token usage where available
* estimated cost
* status
* errors

---

# 27. Error Boundaries

Errors should be categorized:

```text
InputError
DataProviderError
LLMError
SchemaValidationError
ValuationError
PersistenceError
RenderingError
```

Do not catch broad exceptions and continue with incomplete state.

---

# 28. Dependency Injection

External dependencies should be injected.

Example:

```python
AnalysisService(
    data_provider=...,
    llm_provider=...,
    repository=...
)
```

This enables testing with mocks/fakes.

---

# 29. Testing Architecture

## Unit

Fast, deterministic tests.

No network.

Examples:

* DCF
* schemas
* transformations
* memo renderer

## Integration

Test:

```text
provider → graph → models
```

External services should generally be mocked.

## Evaluation

Use real LLM calls on a controlled set of companies.

Evaluation results should be stored separately from ordinary unit tests.

---

# 30. Security

Secrets are loaded from environment variables.

Never:

* commit `.env`
* log API keys
* embed credentials in prompts
* put credentials in source code

---

# 31. Configuration

Centralize configuration.

Example:

```python
class Settings:
    openai_api_key: str
    llm_model: str
    data_provider_api_key: str
    database_url: str
```

Configuration should be loaded once at application startup.

---

# 32. Future Architecture

The architecture is intentionally designed to evolve toward:

```text
                    Web UI
                      │
                      ▼
                    API
                      │
                Application
                      │
                LangGraph
                      │
        ┌─────────────┼─────────────┐
        ▼             ▼             ▼
      Data          Research      Thesis
     Sources         Agents       Engine
                      │
                      ▼
                  Monitoring
                      │
                      ▼
                 PostgreSQL
```

AWS, PostgreSQL, authentication and frontend are future stages.

They are not MVP dependencies.

---

# 33. Architectural Decision Records

Significant decisions should be documented in:

```text
docs/DECISIONS.md
```

Examples:

* why no RAG
* why SQLite
* why LangGraph
* why deterministic valuation
* why OpenAI
* why modular monolith

Architecture changes must be explicit rather than accidental.
