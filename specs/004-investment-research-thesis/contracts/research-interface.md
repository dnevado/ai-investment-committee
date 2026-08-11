# Contract: `aic.research` Package Public Interface

This feature's "interface" is the Python import surface `aic.research` exposes to future
consumers (a future application/CLI layer, tests). There is no network API, CLI, or UI
in scope. It also touches one existing contract: `aic.settings.AppSettings`.

## Import contract

```python
from aic.research import (
    ResearchContext,
    ThesisDraft,
    LLMCompletion,
    LLMProvider,
    OpenAIProvider,
    generate_thesis,
    render_thesis_document,
)
```

- Every name above MUST be importable directly from `aic.research`.
- Importing `aic.research` MUST succeed with no network access and no OpenAI API key
  required — construction of `OpenAIProvider` may require a key, but merely importing
  the module MUST NOT.

## `LLMProvider` contract (protocol)

```python
class LLMProvider(Protocol):
    def complete_structured(
        self, *, system_prompt: str, user_prompt: str, schema: type[BaseModel]
    ) -> LLMCompletion: ...
```

- Any conforming implementation (including `OpenAIProvider` and a test's
  `FakeLLMProvider`) MUST be substitutable for `generate_thesis`'s `provider` argument.
- `generate_thesis` MUST work correctly against **any** conforming implementation — it
  MUST NOT special-case `OpenAIProvider`.

## `generate_thesis` contract

```python
def generate_thesis(context: ResearchContext, provider: LLMProvider) -> InvestmentThesis: ...
```

- MUST validate the provider's raw response against `ThesisDraft` before further
  processing; an invalid response MUST raise an explicit error (FR-004).
- MUST resolve every `supporting_evidence_ids` entry against
  `context.investment_case.evidence`; an unresolvable ID MUST raise an explicit error,
  and no partial `InvestmentThesis` is ever returned in that case (FR-005).
- MUST NOT perform, request, or infer any financial calculation — `context.dcf_result`'s
  figures are never recomputed (FR-006).
- MUST propagate provider errors (timeouts, rate limits, network failures) to the caller
  explicitly — MUST NOT substitute a fabricated or default `InvestmentThesis` (FR-013).
- MUST log token usage and latency for every invocation (research.md "Cost/latency
  measurement").

## `render_thesis_document` contract

```python
def render_thesis_document(thesis: InvestmentThesis) -> str: ...
```

- MUST be a pure function: no I/O, no randomness, no dependency on wall-clock time.
- MUST produce byte-identical output when called twice with an equal `InvestmentThesis`
  (FR-012).
- MUST include exactly the thesis's own structured content — no additional invented
  narrative (FR-011).

## `OpenAIProvider` contract

```python
class OpenAIProvider:
    def __init__(self, *, api_key: str, model: str = ...) -> None: ...
```

- MUST read its API key from a value the caller supplies (sourced from
  `AppSettings.openai_api_key` by the caller) — MUST NOT read environment variables or
  settings itself, keeping the adapter a thin transport layer (FR-009).
- MUST raise an explicit error if constructed/used without a usable API key — MUST NOT
  attempt a network call with a blank credential (FR-010).

## `AppSettings` contract addition

- `AppSettings.openai_api_key: str | None` — optional; sourced from `AIC_OPENAI_API_KEY`;
  never required for `AppSettings` to load successfully (unchanged 001-repository-bootstrap
  guarantee).

## Non-goals of this contract

- No CLI entry point is defined by this feature.
- No network-facing API is defined by this feature.
- No persistence, repository, or CommitteeDecision/AnalysisAssessment symbol is exported
  by `aic.research`.
- No LangGraph node, graph, or multi-agent orchestration symbol is exported.
