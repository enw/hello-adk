# 02: Slash commands with an in-line palette

**What to build:** Typing `/` at the start of the composer opens a filterable palette of commands above the input; ↑/↓ select, Tab/Enter insert, Esc dismisses. Enter on a completed command runs it: `/new`, `/stop`, `/delete`, `/title <text>`. The palette comes from `GET /api/commands`; renaming persists a manual title that overrides the first-message derivation.

**Blocked by:** None.

**Status:** completed

## Acceptance criteria

- [x] `GET /api/commands` returns the palette entries (name, hint, takes_arg) behind the token gate.
- [x] `/` in an empty composer opens the palette, filtered as the command token is typed; ↑/↓ move the selection, Tab/Enter insert the completion (`/title ` leaves room for the argument), Esc dismisses. ↑/↓ serve the palette, not last-message recall, while it is open.
- [x] Enter on a completed command dispatches client-side: `/new` starts a session, `/stop` aborts a stream, `/delete` removes the current session, `/title <text>` renames it and refreshes the rail. An unknown command reports an error, nothing is sent to the agent.
- [x] `PATCH /api/sessions/{id}` persists a manual title (whitespace-collapsed, ≤80 chars) that overrides the derived one; 404 for unknown sessions, 422 for empty titles. Renames ride ADK session state — a content-less `append_event` with a state delta, no new table.
- [x] Offline tests cover the command list, the rename override, validation errors, and that chat still streams after a rename (the content-less event must not break the runner).
- [x] Lands through git: branch → PR → live Vercel preview (verified against its env vars) → merge → production auto-deploy verified.

## Scope boundary

Commands are UI actions only — no tool-forcing hints sent to the agent, no server-side dispatch. Rename reuses ADK session state (`ui_title` key) rather than a second table or endpoint family; no revert-to-derived-title (empty is a 422, not a reset). No command arguments beyond `/title`'s free text.

## Source

Design conversation 2026-11-10/11; palette sketch approved with the command set new/stop/delete/title. "UI actions vs tool-forcing hints" was left open in the sketch — decided UI actions: the agent already routes tool calls itself, and forced tools would bypass its judgment.

## Comments

2026-11-11 verification (branch `chat-ui-slash`, PR #4, preview `hello-adk-git-chat-ui-slash-…vercel.app`): 24/24 offline tests; on the preview — no-token 401, `GET /api/commands` palette, chat stream, rename persisted through the Neon-backed `DatabaseSessionService` (rail showed the override), and a post-rename chat still streamed (`delta`, `done`). ADK 2.13 has no `update_session`, so rename rides `append_event` with a content-less event carrying `state_delta` — the same shape ADK uses for error events.
