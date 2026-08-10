# AI Investment Committee MVP

Initial local prototype for an adversarial AI investment research workflow.

## Stack

- Python 3.12+
- OpenAI
- LangChain
- LangGraph
- Pydantic
- SQLite
- AWS later

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) — used to create the local virtual environment and install/sync
  dependencies

## Setup

From the repository root, in Windows PowerShell:

```powershell
uv venv
uv sync
```

`uv venv` creates a local `.venv` virtual environment targeting Python 3.12+. `uv sync` installs
the project's runtime and development dependencies (pytest, Ruff, mypy) declared in
`pyproject.toml`. Day-to-day commands are run via `uv run <command>`, which uses `.venv`
automatically — no manual activation step is required.

## Running Tests

```powershell
uv run pytest
```

## Quality Checks

```powershell
uv run ruff check .
uv run mypy src
```

## Configuration

Application configuration is loaded from environment variables via `aic.settings.get_settings()`,
backed by a local `.env` file (never committed — see `.gitignore`).

```powershell
Copy-Item .env.example .env
```

`.env.example` documents every supported variable with a placeholder value. Edit `.env` locally as
needed; `get_settings()` returns a typed, validated `AppSettings` instance and works with sensible
defaults even if `.env` is absent.

## First goal

Get this working locally:

```bash
python analyze.py ASML
```

with a Markdown investment memo.

## Development

Read:

1. `CLAUDE.md`
2. `docs/PROMPTS.md`
3. `specs/001-investment-committee-mvp/ITERATIVE_BUILD_PLAN.md`

Then implement one iteration at a time.

## Philosophy

No RAG/vector database in the first MVP.

No UI initially.

No AWS initially.

Prove the investment workflow first.
