# Quickstart: Validate Repository Bootstrap

Validates the three user stories from `spec.md` end-to-end. Run from the repository root in
Windows PowerShell (the primary supported shell for this feature — SC-008).

## Prerequisites

- Python 3.12+ available (or let `uv` manage it)
- `uv` installed ([uv docs](https://docs.astral.sh/uv/))

## User Story 1 — Working local environment

```powershell
uv venv
uv sync
uv run python -c "import aic; print(aic.__version__)"
uv run pytest
```

**Expected outcome**: virtual environment created, dependencies installed, the version string
prints with no error, and the full test suite (including the smoke test) passes — satisfies
SC-001, SC-002, SC-005.

## User Story 2 — Quality checks

```powershell
uv run ruff check .
uv run mypy src
```

**Expected outcome**: both commands complete with zero reported issues — satisfies SC-003, SC-004.

## User Story 3 — Environment-variable configuration

```powershell
Copy-Item .env.example .env
uv run python -c "from aic.settings import get_settings; print(get_settings())"
```

**Expected outcome**: `.env.example` lists every supported variable with a placeholder value and
no real credential; the settings object loads successfully and prints its (non-secret) values —
satisfies User Story 3's acceptance scenarios.

## Full validation in one pass

```powershell
uv venv
uv sync
uv run pytest
uv run ruff check .
uv run mypy src
```

All commands above exiting with code `0` on a clean checkout is the complete acceptance signal for
this feature (spec Success Criteria SC-001–SC-005, SC-008; SC-006/SC-007 are verified by
inspection — no secrets and no investment/LLM/agent/AWS code present — rather than by a command).
