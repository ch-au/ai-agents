# Cloud Mode Implementation Spec (v1)

## 1) Goals

Cloud mode should run the full app reliably behind reverse proxies/CDNs and managed platforms, while preserving local development behavior.

### Primary outcomes
- Zero hard-coded localhost assumptions in production paths.
- Stable WebSocket + REST connectivity behind proxy headers.
- Deterministic LLM behavior via structured outputs and explicit schemas.
- Portable deployment profile (single source of truth for env/config).
- Observable, testable request/response lifecycle for cloud incidents.

---

## 2) Scope

### In scope
- Runtime/networking behaviors (session bootstrap, ws/rest URL resolution).
- Configuration model for cloud vs local.
- LLM contract hardening (structured output envelope + validation).
- Prompting and retry policy for schema-constrained outputs.
- Basic rollout/testing checklist.

### Out of scope (v1)
- Full provider-agnostic policy engine for all LLM vendors.
- Multi-region active-active session replication.
- Fine-grained auth/rbac redesign.

---

## 3) Runtime Modes

Define a single runtime selector:
- `APP_RUNTIME_MODE=local|cloud` (default: `local`).

### local
- Existing defaults (`localhost` URLs) remain valid.
- Broad developer CORS defaults allowed.

### cloud
- Strict origin allowlist from env.
- Trust forwarded headers for external scheme/host derivation.
- Prefer server-issued endpoint metadata in session bootstrap.

---

## 4) API and Data Model Changes

## 4.1 Session bootstrap contract (`POST /session`)

Current response has:
- `session_id`
- `status`
- `ws_url` (added)

v1 target response shape:
```json
{
  "session_id": "...",
  "status": "success",
  "endpoints": {
    "api_base_url": "https://app.example.com",
    "ws_base_url": "wss://app.example.com",
    "ws_path": "/ws"
  },
  "runtime": {
    "mode": "cloud",
    "provider": "generic"
  }
}
```

### Notes
- Keep backward compatibility by still accepting/serving legacy `ws_url` for one release cycle.
- Add a typed frontend contract for `endpoints` and feature-gate fallback logic.

## 4.2 Configuration schema

Introduce an explicit config schema (env validated at startup):
- `APP_RUNTIME_MODE`
- `PUBLIC_BASE_URL` (optional override)
- `PUBLIC_WS_BASE_URL` (optional override)
- `CORS_ALLOW_ORIGINS` (required in cloud)
- `TRUST_PROXY_HEADERS=true|false` (default true in cloud)

Startup should fail fast in cloud mode when required config is missing.

---

## 5) LLM/Prompting Iteration Plan

Yes — we **should** iterate on both data model and LLM behavior now. Cloud reliability depends on deterministic contracts.

## 5.1 Structured output envelope

All planning/dispatch/review-critical LLM responses should return a strict envelope:
```json
{
  "schema_version": "1.0",
  "intent": "plan|dispatch|review|finalize",
  "content": { "...": "..." },
  "confidence": 0.0,
  "errors": []
}
```

### Requirements
- JSON schema per intent.
- Parse + validate before state mutation.
- If invalid: auto-repair retry with schema error message, capped retries.

## 5.2 Prompting strategy

Per critical node:
1. System prompt includes concise contract + forbidden fields.
2. Tool/assistant instruction includes **single JSON object only** output requirement.
3. Validation feedback loop includes machine-readable errors.

## 5.3 Retry policy

- Retry only on validation failures / transient provider errors.
- Exponential backoff with jitter.
- Emit typed telemetry event for each retry reason.

---

## 6) Observability Requirements

- Add structured events:
  - `session_bootstrap_generated`
  - `endpoint_resolution_source` (forwarded-header/env/default)
  - `llm_schema_validation_failed`
  - `llm_schema_validation_recovered`
- Include run/session correlation IDs in every event.

---

## 7) Rollout Plan

1. Introduce new response fields + compatibility shim.
2. Ship frontend support for `endpoints.*` with fallback to legacy fields.
3. Enable schema validation in monitor-only mode.
4. Flip to enforce mode for critical intents.
5. Remove legacy fields after one stable release.

---

## 8) Test Plan (Minimum)

### Backend
- Unit tests: endpoint derivation matrix (proxy headers, explicit env, fallback).
- Contract tests: `/session` response schema for local/cloud.
- Negative tests: startup fails on missing cloud-required vars.

### Frontend
- Session bootstrap parser handles both legacy and new fields.
- WebSocket URL selection priority tests.

### Integration
- Reverse-proxy simulation (x-forwarded-*) for ws/wss correctness.
- End-to-end schema-validation retry flow on malformed model output.

---

## 9) Acceptance Criteria

- Cloud deployment works without frontend hardcoded URL changes.
- `POST /session` fully describes connectable endpoints.
- Planning/dispatch/review flows reject malformed LLM payloads safely.
- All critical failures are diagnosable from structured logs.
