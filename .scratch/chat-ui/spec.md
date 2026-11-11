# Chat UI: the agent as a personal web app

Status: ready-for-agent

## Problem Statement

The agent's browser experience is ADK's local dev UI (`adk web`): localhost-only, unauthenticated, no shared history across devices, and separate from the deployed world. The developer wants one dense personal chat UI—reachable from any device, with persistent sessions—without adopting a frontend build pipeline.

## Solution

A FastAPI server (`main.py`) bridges the ADK agent over Server-Sent Events; a single-file client (`static/index.html`) renders it. Sessions persist in Postgres (Neon). A token gate replaces localhost: the URL is public, so every `/api/*` call must carry `APP_TOKEN`; an unset token fails closed. Deploys are git-driven on Vercel: push to main is production, every PR gets a live preview.

Slices:

1. **Shipped** (branch `chat-ui`, merged to main as `712f10b`/`79db7d0`): server + SSE + dense UI + Postgres sessions + token gate, live at hello-adk.vercel.app and phone-verified. 18 offline tests.
2. **Shipped** (branch `chat-ui-titles`, PR #3, merged to main as `43487ba`): rail titles from the first user turn, one collapsible chip per tool call with its result, ↑ recalls the last message. Preview verified through a Vercel protection-bypass secret (32 alphanumeric chars in `hello_world/.env`).
3. **Shipped** (branch `chat-ui-slash`, PR #4, merged to main as `ffc172a`): `/new` `/stop` `/delete` `/title <text>` in-line palette backed by `GET /api/commands`; renames ride ADK session state (content-less `append_event` with a `ui_title` delta). Verified on preview and production.
4. **Shipped** (branch `chat-ui-datetime`, PR #5, merged to main as `cded0c7`): `get_datetime` with an optional IANA timezone; empty resolves to `APP_TIMEZONE` (else UTC), invalid zones return an actionable error. Verified on preview and production.
5. **Search grounding**: current-information answers with Google Search (also on the adk-capabilities roadmap).
6. **Durable preferences**: `remember`/`recall` of stable facts (default tax rate, currency, common quantities) in Postgres (also on the adk-capabilities roadmap).
7. **Task list**: `add_task` / `complete_task` / `list_tasks`, Postgres-backed.
8. **Session search**: full-text search over past chat history in Neon ("what did I ask about X").
9. **URL read**: fetch a page, strip to text, cap size/timeout — first tool with real failure modes (timeouts, huge pages, non-HTML).

Slices 4–9 stay rough until their turn: outcomes and dependencies above, no implementation detail.

## Scope boundary

No frontend build step, no node_modules, no auth beyond the token gate, one user (`enw`). Model stays Gemini; a Nous swap is a separate later decision. Slash commands are UI actions, never tool-forcing hints to the agent. Tools run on Vercel: nothing touching the local machine or vault (unreachable), no email/calendar (same plus auth complexity).
