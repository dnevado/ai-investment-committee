# Phase 0 Research: Repository Bootstrap

All Technical Context items were resolvable from the spec, the constitution, and the machine's
existing local state (a `uv`-created `.venv` already targets CPython 3.12.12). No open
`NEEDS CLARIFICATION` markers remain.

## Decision: Environment & dependency management via `uv`

- **Decision**: Use `uv` to create the virtual environment (`uv venv`) and to install/synchronize
  dependencies (`uv sync`), driven entirely by `pyproject.toml`. Day-to-day commands are run via
  `uv run <tool>` (e.g., `uv run pytest`) rather than requiring a manually activated shell.
- **Rationale**: Explicitly required by the spec (FR-013–FR-015). `uv run` avoids PowerShell
  execution-policy friction around activating `Scripts\Activate.ps1`, which keeps the documented
  Windows workflow to a small, copy-pasteable set of commands (SC-001, SC-008). `uv` is already
  present and working in this environment (`uv 0.9.7`, confirmed venv at Python 3.12.12).
- **Alternatives considered**:
  - Poetry — explicitly excluded by the spec.
  - Plain `venv` + `pip` — was the original default assumption before clarification; rejected now
    that `uv` is an explicit requirement.
  - `pipx`/global tool installs — inappropriate; project-local, reproducible tooling is required.

## Decision: Build backend / project metadata

- **Decision**: `pyproject.toml` with `hatchling` as the PEP 517 build backend, package name
  `aic`, `src`-layout declared via `[tool.hatch.build.targets.wheel] packages = ["src/aic"]`.
- **Rationale**: `hatchling` is `uv`'s own default build backend when scaffolding projects, has no
  extra runtime dependency footprint, and supports `src`-layout with a one-line config — keeping
  the dependency set minimal (constitution Principle VIII).
- **Alternatives considered**: `setuptools` (more verbose `src`-layout config, heavier legacy
  surface); `flit` (less common pairing with `uv`, no material benefit here).

## Decision: Dependency grouping

- **Decision**: Runtime dependencies (`pydantic`, `pydantic-settings`) go in
  `[project.dependencies]`. Dev-only tools (`pytest`, `ruff`, `mypy`) go in a `uv`
  `[dependency-groups] dev = [...]` group, installed by default via `uv sync`.
- **Rationale**: Keeps the distinction between "the package needs this to run" and "contributors
  need this to develop it" explicit and machine-checkable, per FR-014 (app code must not depend on
  `uv`, and by extension should not conflate dev tooling with runtime deps).
- **Alternatives considered**: `[project.optional-dependencies].dev` — older convention, works
  with `uv` but the native `[dependency-groups]` (PEP 735) is the more current `uv`-idiomatic
  choice and was chosen for that reason; no functional difference for this feature's scope.

## Decision: Application settings shape

- **Decision**: A single `pydantic-settings` `BaseSettings` subclass (`AppSettings`) in
  `src/aic/settings.py`, reading from a local `.env` file (`env_file=".env"`) with environment
  variables namespaced under an `AIC_` prefix (e.g., `AIC_ENV`). A `get_settings()` accessor
  returns a cached instance. Exactly one field is defined for this feature: `environment: str`
  (default `"local"`) — enough to prove the loading/validation mechanism end-to-end without
  inventing configuration that belongs to a later, unbuilt feature.
- **Rationale**: Spec FR-006/FR-007 and User Story 3 require a working, typed, env-var-driven
  settings mechanism and a documented `.env.example`, but no real external service exists yet
  (spec Assumptions: "No real external services"). Adding speculative fields (API keys, DB URLs)
  for integrations not yet built would violate Principle VIII (no premature infrastructure) and
  the "don't invent APIs" rule in `CLAUDE.md`.
- **Alternatives considered**: Plain `os.environ` reads — rejected, spec explicitly requires
  Pydantic Settings (FR-006) for validation and typed structure, consistent with constitution
  Principle III (Structured Outputs Only).

## Decision: Test, lint, and type-check configuration location

- **Decision**: Configure pytest, Ruff, and mypy entirely inside `pyproject.toml`
  (`[tool.pytest.ini_options]`, `[tool.ruff]`, `[tool.mypy]`) rather than separate config files.
- **Rationale**: One canonical config file matches FR-013's requirement that `pyproject.toml`
  remain canonical, and keeps the root directory minimal per the constitution's simplicity
  preference.
- **Alternatives considered**: Separate `pytest.ini` / `ruff.toml` / `mypy.ini` — more files for no
  behavioral benefit at this scale; rejected in favor of consolidation.

## Decision: `.gitignore` scope

- **Decision**: Standard Python `.gitignore` covering `.venv/`, `__pycache__/`, `*.pyc`,
  `.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/`, `.env`, build artifacts (`dist/`, `build/`,
  `*.egg-info/`), and a way to keep `data/`/`outputs/` directories tracked while ignoring their
  generated contents (`data/*` / `outputs/*` ignored with a tracked `.gitkeep` in each, or an
  explicit `!.gitkeep` exception).
- **Rationale**: Directly required by FR-012 and the edge case in the spec about accidental secret
  commits (`.env` must never be tracked).
- **Alternatives considered**: None — this is a well-established pattern with no meaningful
  alternative design.
