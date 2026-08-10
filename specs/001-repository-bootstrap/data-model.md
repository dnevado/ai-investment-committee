# Phase 1 Data Model: Repository Bootstrap

This feature introduces exactly one entity, matching the spec's Key Entities section. It is a
configuration/settings object, not a domain or persistence model — there is no storage layer in
this feature.

## AppSettings

Represents the application's typed, validated runtime configuration, loaded from environment
variables (optionally via a local `.env` file). Contains no secrets by default and no
investment-domain or provider-specific fields — those belong to later iterations.

| Field | Type | Required | Default | Source | Validation |
|---|---|---|---|---|---|
| `environment` | `str` | No | `"local"` | Env var `AIC_ENV` | Free-text label; no enum constraint imposed by this feature (kept minimal per research.md) |

**Relationships**: None — standalone configuration object.

**State transitions**: None — settings are loaded once per process and treated as immutable for
the lifetime of that process (`get_settings()` returns a cached instance).

**Validation rules**:

- Loading MUST fail explicitly (raise a validation error) if an environment variable is present
  but cannot be coerced to its declared type — no silent fallback to an incorrect value (spec
  Edge Cases).
- No field in this feature is required to be present for `AppSettings` to load successfully
  (`environment` has a safe default), so a clean checkout with no `.env` file still boots
  successfully — this keeps User Story 1 (working local environment) independent of User Story 3
  (environment configuration).
