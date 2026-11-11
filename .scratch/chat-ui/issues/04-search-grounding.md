# 04: Search grounding

**What to build:** The agent can search the web for current information. `GoogleSearchTool(bypass_multi_tools_limit=True)` joins the agent's tools; the server forwards each event's `grounding_metadata` as a `search` SSE event (queries + citations deduped by URI), history reload includes them as `kind: "search"` items, and the UI renders a collapsible 🔍 chip whose expansion lists the citation links.

**Blocked by:** None (slice 4 merged as `cded0c7`).

**Status:** ready-for-agent

## Acceptance criteria

- [ ] The agent carries `GoogleSearchTool(bypass_multi_tools_limit=True)`; instructions route current-events/news/recent-facts questions to search with citations.
- [ ] `/api/chat` emits `{"type":"search","queries":[…],"citations":[{title,uri}…]}` per unique search batch — citations deduped by URI within a request, so repeated grounding (aggregated finals, repeated calls) emits once.
- [ ] `GET /api/sessions/{id}/messages` includes `{"kind":"search",…}` items in stream order (chip above the answer it grounded), because grounding metadata persists with the event.
- [ ] The UI renders a 🔍 chip showing the queries; expanding lists deduped citation links opening in a new tab; reload re-renders them from history.
- [ ] Offline tests cover the search SSE event (queries, URI dedupe, order), repeated-grounding suppression, and the history item. Runner-based suites set `ADK_DISABLE_GEMINI_MODEL_ID_CHECK=1` — `google_search` otherwise rejects scripted non-Gemini model ids.
- [ ] Lands through git: branch → PR → live Vercel preview verified with a real current-events question → merge → production auto-deploy verified.

## Scope boundary

No separate search API or endpoint, no rendering of `search_entry_point` HTML widgets, no citation numbering inside answer text, no client-side search. The chip reuses the tool-chip markup and styling.

## Source

Chat-ui spec slice 5 (2026-11-10/11): "current-information answers with Google Search (also on the adk-capabilities roadmap)". De-risked probes: ADK 2.13 events carry `grounding_metadata` from the model response, `DatabaseSessionService` persists it, and `ADK_DISABLE_GEMINI_MODEL_ID_CHECK=1` keeps offline scripted runs working with `google_search` in the toolset.
