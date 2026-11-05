# 02: Manage response style within one conversation

**What to build:** Set, inspect, change, and clear concise/standard response style in the existing chat; preserve it when resuming the same persisted conversation after restart without affecting other conversations or users.

**Blocked by:** 01 — Calculate validated USD quotes through chat (completed).

**Status:** completed

Verification and lessons: [slice 02 results](../results-02.md).

## Plan

1. Write a failing runner-level preference test; add the minimal validated state tool and current-state instruction.
2. Extend tests for changes, reset, invalid requests, instruction injection, and user/session isolation.
3. Verify persistence through a reopened temporary SQLite session service.
4. Extend opt-in live verification, document manual tests, record evidence, and stop.

Unresolved questions: none.

## Acceptance criteria

- [x] Users can get/set/clear concise or standard style through the existing agent; defaults and reset resolve to standard.
- [x] Later turns receive the effective style in their model instructions; concise mode preserves required quote details.
- [x] Invalid actions/styles return useful errors and leave the preference unchanged.
- [x] Separate sessions and users remain isolated, including independently updated sessions.
- [x] The same persisted session retains its style after reopening SQLite storage with a fresh runner/service.
- [x] Offline tests run without credentials/network and all quote regressions remain green.
- [x] An explicitly opted-in bounded live scenario verifies preference tools across turns and a final answer; the existing quote smoke scenario remains available.
- [x] Document manual set/inspect/reset/new-session/restart checks and record results/lessons.

## Source

The session-state capability in the parent spec, narrowed by [slice 02 spec](../spec-02.md). No long-term memory or later-slice work.
