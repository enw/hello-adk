# Chat UI: the agent as a personal web app

Status: ready-for-agent

## Problem Statement

The agent's browser experience is ADK's local dev UI (`adk web`): localhost-only, unauthenticated, no shared history across devices, and separate from the deployed world. The developer wants one dense personal chat UI—reachable from any device, with persistent sessions—without adopting a frontend build pipeline.

## Solution

A FastAPI server (`main.py`) bridges the ADK agent over Server-Sent Events; a single-file client (`static/index.html`) renders it. Sessions persist in Postgres (Neon). A token gate replaces localhost: the URL is public, so every `/api/*` call must carry `APP_TOKEN`; an unset token fails closed. Deploys are git-driven on Vercel: push to main is production, every PR gets a live preview.

Slices:

1. **Shipped** (branch `chat-ui`, merged to main as `712f10b`/`79db7d0`): server + SSE + dense UI + Postgres sessions + token gate, live at hello-adk.vercel.app and phone-verified. 18 offline tests.
2. **Shipped** (branch `chat-ui-titles`, PR #3, merged to main as `43487ba`): rail titles from the first user turn, one collapsible chip per tool call with its result, ↑ recalls the last message. Preview verified through a Vercel protection-bypass secret (32 alphanumeric chars in `hello_world/.env`).
3. *(rough)* Keyboard and composer polish as real use exposes gaps.

## Scope boundary

No frontend build step, no node_modules, no auth beyond the token gate, one user (`enw`). Model stays Gemini; a Nous swap is a separate later decision.
