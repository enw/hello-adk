# Slice 02: session response-style preference

Status: ready-for-agent

## Problem Statement

Users must currently repeat their preferred answer style on every turn. We need one useful session-state capability without prematurely building long-term memory.

## Solution

Let a user set, inspect, change, or clear a response-style preference for the current conversation. Supported values: `concise` and `standard`; a new or cleared session uses `standard`. Concise means at most two sentences when practical, without omitting required quote amounts or important errors.

## User Stories

1. As a user, I want to request concise answers for this conversation, so later turns honor that preference.
2. As a user, I want to inspect the effective style, so I know the current setting.
3. As a user, I want to change or reset the style, so the preference is reversible.
4. As a user, I want fresh conversations to use defaults, so unrelated tasks stay separate.
5. As a user, I want another user's conversations isolated, so preferences do not leak.
6. As a user, I want a resumed conversation to retain its style after a local server restart, so resuming does not reset it unexpectedly.

## Implementation Decisions

- Add one ADK tool for `get`, `set`, and `clear`. Validate action/style at this boundary; return structured errors without changing state on invalid input.
- Store one allowlisted, session-scoped state key. Do not use app/user prefixes, arbitrary keys, client-provided identity, or cross-session memory.
- Inject the effective session style into the agent's instructions on every model request. Treat unsupported values as errors, never instructions.
- Clear resets the effective preference to `standard`; it does not erase chat history. Previous preferences remain in the transcript but the explicit current-state instruction wins.
- Reuse ADK's session persistence and existing development UI; no new database or API layer. Concurrent sessions have independent state; simultaneous writes within one session are not a conflict-resolution feature.

## Testing Decisions

- Use the already approved runner/public session-service seams with a controlled external model and blocked network connections.
- Verify set/get/change/clear across turns, injected instructions, invalid-input nonmutation, and separate user/session identities.
- Reopen real temporary SQLite storage with a new session service/runner, then inspect the preference through a tool turn. Do not inspect raw database rows.
- Extend the opt-in live smoke command with a session scenario; verify tool events and final responses rather than assuming a model's prose proves storage.
- Keep the quote suite green. Live brevity is a practical instruction, not a rigid exact-wording assertion.

## Out of Scope

Long-term memory, automatic preference extraction, additional preference types, authentication/hosting, custom UI, simultaneous same-session edits, and any later roadmap capability.

## Further Notes

User authorized specification, planning, and implementation of this next slice. No further design choices block it. Record verification and lessons, then stop without automatically detailing another slice.
