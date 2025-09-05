# Byterover Client behavior

This note explains the runtime behavior of `src.mcp_adapter.client.ByteroverClient`.

Key points:

# Byterover Client behavior

This note explains the runtime behavior of `src.mcp_adapter.client.ByteroverClient`.

Key points:

- Headers:
  - If `extension_id` is set, requests include `X-Byterover-Extension: <extension_id>`.
  - If `auth_token` is set, requests include `Authorization: Bearer <auth_token>`.

- Retry/backoff:
  - The client uses a small manual retry loop controlled by `max_retries` and `backoff_factor`.
  - Each failed attempt logs a warning and a debug-level line with retry details.
  - Backoff uses `backoff_factor * (2 ** attempt)` seconds.

- Offline fallback:
  - When `endpoint` is None or all retries are exhausted, the client writes a JSON record to `offline_dir`.
  - The offline record contains: `action`, `payload`, and `saved_at` timestamp.

- Testing notes:
  - Unit tests patch `client.session.post` with a fake to assert headers and retry semantics.
  - The client attempts to mount a urllib3 `Retry` adapter if available; unit tests still exercise manual retries.

Examples:

```py
client = ByteroverClient(endpoint=None, offline_dir='byterover_offline')
client.byterover_save_implementation_plan({ 'title': 'Plan' })
```

This document should be updated if header names, offline format, or retry semantics change.
