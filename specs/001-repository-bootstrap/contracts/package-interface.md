# Contract: `aic` Package Public Interface

This feature's only "interface" is the Python import surface the `aic` package exposes to future
features and to the test suite. There is no network API, CLI, or UI in scope.

## Import contract

```python
import aic
```

- MUST succeed with no side effects that require external services, network access, or real
  credentials (FR-008, SC-005).
- `aic.__version__` MUST be present as a string (basic package identity, standard Python
  packaging convention).

## Settings contract

```python
from aic.settings import AppSettings, get_settings

settings = get_settings()
```

- `get_settings()` MUST return an `AppSettings` instance (see `data-model.md`) without requiring
  any environment variable to be set (defaults apply).
- `get_settings()` MUST raise a clear validation error (not a silent fallback) if an environment
  variable is present but invalid for its declared field type.
- Calling `get_settings()` multiple times within a process MUST be safe and MUST NOT re-read the
  environment inconsistently (cached instance).

## Non-goals of this contract

- No CLI entry point is defined by this feature.
- No network-facing API is defined by this feature.
- No domain, agent, or valuation symbols are exported by `aic` as a result of this feature.
