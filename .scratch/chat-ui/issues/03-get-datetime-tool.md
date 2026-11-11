# 03: get_datetime tool

**What to build:** A deterministic `get_datetime` tool so the agent anchors date and time answers to the real clock instead of guessing. It takes an optional IANA timezone (empty means the server's configured default, `APP_TIMEZONE`, else UTC) and returns date, weekday, time, timezone, ISO timestamp, and Unix seconds. Invalid zone names return an actionable error.

**Blocked by:** None.

**Status:** completed

## Acceptance criteria

- [x] `get_datetime(timezone)` returns `date`, `weekday`, `time`, `timezone`, `iso`, `unix` consistent with the requested zone; an empty timezone resolves to `APP_TIMEZONE` (else UTC).
- [x] Unknown zone names return an error naming the problem and an IANA example — never a guessed time and never an exception.
- [x] Agent instructions route anything about today/now/dates/weekdays to the tool; it stays callable for ordinary conversation otherwise.
- [x] Offline tests cover the tool boundary (explicit zone, configured default, UTC fallback, invalid zone) and the scripted-model runner wiring (model calls get_datetime, real result returns to it).
- [x] `APP_TIMEZONE` is configured in `hello_world/.env`, `.env.example`, and Vercel production + preview so the deployed default matches the user's zone.
- [x] Lands through git: branch → PR → live Vercel preview (verified against its env vars) → merge → production auto-deploy verified.

## Scope boundary

No browser timezone detection, no per-user zones, no formatting options. The clock is read at call time; no injected/frozen clock abstraction in production code (tests read real time with tolerance).

## Source

Chat-ui spec slice 4 (2026-11-11): "trivial, deterministic, fully offline-testable, and fixes the LLM's chronic date confusion".

## Comments

2026-11-11 verification (branch `chat-ui-datetime`, PR #5, preview `hello-adk-git-chat-ui-datetime-…vercel.app`): 29/29 offline tests; on the preview, "What day is it and what time is it?" produced a `get_datetime` call whose result used the deployed `APP_TIMEZONE` (`America/New_York`, 2026-11-10 22:26 EST) and an answer anchored to it; no-token 401; test session deleted.
