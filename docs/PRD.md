# AI Investment Committee — Product Requirements Document

**Version:** 0.1
**Status:** MVP
**Date:** 2026-08-09

---

# 1. Product Overview

AI Investment Committee (AIC) is an AI-powered investment research assistant that simulates a structured investment committee process.

The product takes a public company ticker and produces a structured investment analysis by combining:

* financial data
* company research
* Bull Case analysis
* Bear Case analysis
* deterministic valuation
* committee-level synthesis

The initial product is a command-line vertical slice.

There is no frontend in MVP 0.1.

---

# 2. Problem

Investment research is fragmented across:

* financial statements
* market data
* company information
* analyst opinions
* assumptions
* valuation models

Investors spend significant time:

* gathering data
* constructing a thesis
* challenging their own assumptions
* building valuation scenarios
* updating previous conclusions

AI can accelerate this process, but generic LLM research has several weaknesses:

* hallucinations
* unsupported claims
* confirmation bias
* inconsistent reasoning
* poor separation between facts and assumptions
* unreliable financial calculations

AIC aims to solve this by imposing a structured investment committee workflow.

---

# 3. Product Vision

AIC should eventually become a persistent investment research system where every investment thesis has:

```text
Evidence
   ↓
Assumptions
   ↓
Thesis
   ↓
Valuation
   ↓
Decision
   ↓
Monitoring
   ↓
Outcome
```

The MVP only implements the first five stages.

---

# 4. MVP Objective

The MVP objective is:

> Determine whether an AI-driven investment committee can produce a sufficiently useful and trustworthy investment memo to justify building the full product.

The first successful workflow is:

```text
Ticker
  ↓
Research
  ↓
Bull
  ↓
Bear
  ↓
Valuation
  ↓
Committee
  ↓
Investment Memo
```

---

# 5. Target User

Primary MVP user:

> Sophisticated retail investor, independent investor, analyst, or financially literate professional who performs fundamental research on public companies.

The user is expected to understand basic investment concepts.

The MVP is not designed for:

* novice investors
* automated trading
* institutional portfolio execution
* financial advisors managing client portfolios

---

# 6. User Story

### Primary

> As an investor, I want to provide a company ticker and receive a structured investment committee analysis so that I can understand the strongest reasons to invest, the strongest reasons not to invest, the valuation, and what could invalidate the thesis.

### Secondary

> As an investor, I want to understand which conclusions are based on facts versus assumptions.

### Secondary

> As an investor, I want the valuation to be calculated deterministically rather than hallucinated by an LLM.

---

# 7. MVP User Experience

The complete interaction is:

```bash
python analyze.py ASML
```

The application displays progress:

```text
Resolving company...
Retrieving financial data...
Building research context...
Running Research Agent...
Running Bull Agent...
Running Bear Agent...
Calculating valuation...
Running Committee Chair...
Generating memo...
```

The final output is:

```text
outputs/ASML_YYYY-MM-DD.md
```

---

# 8. Investment Memo Requirements

The final memo must contain:

## Executive Summary

* company
* recommendation
* conviction
* current valuation context
* central thesis

## Business Overview

* business description
* major revenue drivers
* competitive position

## Financial Analysis

* revenue trend
* profitability trend
* cash-flow trend
* balance-sheet observations

## Bull Case

* core upside thesis
* catalysts
* supporting evidence
* assumptions

## Bear Case

* core downside thesis
* risks
* thesis breakers
* assumptions at risk

## Valuation

* Bear scenario
* Base scenario
* Bull scenario
* assumptions
* implied value
* current price
* upside/downside

## Key Risks

* business
* financial
* competitive
* regulatory
* valuation

## Key Catalysts

* operational
* financial
* market
* strategic

## Invalidation Conditions

Explicit conditions that would materially weaken or invalidate the thesis.

## Committee Decision

* BUY / WATCH / AVOID
* conviction score from 1–10
* rationale
* key disagreements

## Sources

List of material data sources used.

---

# 9. Functional Requirements

## FR-001 Company Input

The system must accept a company ticker.

Example:

```text
ASML
```

---

## FR-002 Company Resolution

The system must resolve the ticker to:

* legal/company name
* ticker
* country
* exchange where available
* reporting currency

---

## FR-003 Financial Data

The system must retrieve, where available:

* revenue
* gross profit
* operating income
* net income
* operating cash flow
* capital expenditure
* free cash flow
* cash
* debt
* shares outstanding
* market price
* market capitalization

Historical data should cover approximately five years where available.

---

## FR-004 Source Metadata

Every external dataset must provide source metadata.

Minimum:

```text
provider
dataset
retrieved_at
```

---

## FR-005 Research Agent

The Research Agent must produce a structured report containing:

* business summary
* financial trends
* growth drivers
* risks
* important claims
* supporting sources

---

## FR-006 Bull Agent

The Bull Agent must produce:

* investment thesis
* upside drivers
* catalysts
* assumptions
* supporting evidence
* potential valuation implications

---

## FR-007 Bear Agent

The Bear Agent must produce:

* downside thesis
* risks
* thesis breakers
* assumptions at risk
* supporting evidence
* potential valuation implications

---

## FR-008 Valuation Engine

The system must calculate at minimum:

* Bear scenario
* Base scenario
* Bull scenario

The initial valuation methodology is DCF.

A simple multiples-based framework may be included if it does not materially delay the MVP.

---

## FR-009 Deterministic Calculations

All valuation calculations must be implemented in deterministic code.

Given identical inputs, the valuation engine must return identical outputs.

---

## FR-010 Committee Chair

The Committee Chair must evaluate:

* Research
* Bull Case
* Bear Case
* Valuation
* Evidence

It must produce:

* recommendation
* conviction
* thesis
* assumptions
* risks
* catalysts
* invalidation conditions
* disagreements

---

## FR-011 Structured Output

All internal agent outputs must be validated using typed schemas.

Invalid outputs must be rejected or retried.

---

## FR-012 Memo Generation

The system must convert the structured final decision into Markdown.

---

## FR-013 Multiple Companies

The workflow must work for multiple supported companies without company-specific logic.

---

# 10. Non-Functional Requirements

## NFR-001 Simplicity

No unnecessary infrastructure.

---

## NFR-002 Reliability

A failed agent call must not silently produce an incomplete investment memo.

---

## NFR-003 Reproducibility

Inputs, model configuration and source metadata should be recorded sufficiently to understand how an analysis was produced.

---

## NFR-004 Cost

The system must estimate LLM cost per completed analysis.

Target:

> Ideally below $1 per complete analysis during MVP testing.

This is a target, not a hard acceptance criterion.

---

## NFR-005 Performance

Target:

> Complete analysis in less than 5 minutes.

---

# 11. Out of Scope

The following are explicitly excluded:

* web frontend
* authentication
* payments
* portfolio management
* broker integration
* trading
* automated orders
* RAG
* vector database
* PDF ingestion
* real-time market monitoring
* alerts
* mobile application
* multi-user architecture
* advanced AWS deployment
* autonomous agent loops

---

# 12. Initial Data Strategy

The MVP should prioritize:

1. structured financial data
2. controlled public data sources
3. explicit source metadata

The system should avoid uncontrolled web search as the primary research mechanism.

Document/RAG capabilities are deferred.

---

# 13. Evaluation

AIC must maintain a small evaluation dataset containing known companies and expected properties.

Initial evaluation companies:

* ASML
* NVIDIA
* Microsoft
* Apple
* Alphabet
* Amazon

Evaluation dimensions:

### Financial correctness

Are retrieved financial figures correct?

### Calculation correctness

Are valuation outputs mathematically correct?

### Evidence quality

Are material claims supported?

### Bull/Bear quality

Are arguments substantive and non-generic?

### Committee quality

Does the final decision correctly represent conflicting evidence?

### Hallucination rate

How often does the system state unsupported factual claims?

---

# 14. MVP Success Metrics

Primary:

* analysis completion rate >80%
* median analysis time <5 minutes
* citation/source accuracy >95%
* valuation calculation correctness = 100%

Secondary:

* useful Bull Case according to human evaluator
* useful Bear Case according to human evaluator
* useful Committee Decision according to human evaluator

---

# 15. Future Product Direction

After MVP validation:

```text
MVP
 ↓
Web Application
 ↓
Persistent Thesis
 ↓
What's Changed?
 ↓
Monitoring
 ↓
Portfolio
 ↓
Alerts
```

RAG should only be introduced when users demonstrate demand for deeper document-level research.
