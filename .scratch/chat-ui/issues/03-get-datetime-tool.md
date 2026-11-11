# 03: get_datetime tool

**What to build:** A deterministic `get_datetime` tool so the agent anchors date and time answers to the real clock instead of guessing. It takes an optional IANA timezone (empty means the server's configured default, `APP_TIMEZONE`, else UTC) and returns date, weekday, time, timezone, ISO timestamp, and Unix seconds. Invalid zone names return an actionable error.

**Blocked by:** None.

**Status:** ready-for-agent

## Acceptance criteria

- [ ] `get_datetime(timezone)` returns `date`, `weekday`, `time`, `timezone`, `iso`, `unix` consistent with the requested zone; an empty timezone resolves to `APP_TIMEZONE` (else UTC).
- [ ] Unknown zone names return an error naming the problem and an IANA example — never a guessed time and never an exception.
- [ ] Agent instructions route anything about today/now/dates/weekdays to the tool; it stays callable for ordinary conversation otherwise.
- [ ] Offline tests cover the tool boundary (explicit zone, configured default, UTC fallback, invalid zone) and the scripted-model runner wiring (model calls get_datetime, real result returns to it).
- [ ] `APP_TIMEZONE` is configured in `hello_world/.env`, `.env.example`, and Vercel production + preview so the deployed default matches the user's zone.
- [ ] Lands through git: branch → PR → live Vercel preview (verified against its env vars) → merge → production auto-deploy verified.

## Scope boundary

No browser timezone detection, no per-user zones, no formatting options. The clock is read at call time; no injected/frozen clock abstraction in production code (tests read real time with tolerance).

## Source

Chat-ui spec slice 4 (2026-11-11): "trivial, deterministic, fully offline-testable, and fixes the LLM's chronic date confusion".
