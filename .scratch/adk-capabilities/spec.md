1. ADK capabilities: from hello world to a useful agent

Status: ready-for-agent

## Problem Statement

The app currently proves that a Google ADK agent can answer a message through the development UI or terminal. It cannot yet perform useful actions, ground answers in external information, remember preferences, collaborate with specialists, or offer a safe production interface.

The developer wants a practical learning path through ten ADK capabilities without turning the starter into an unnecessarily complex framework. Each increment must produce a demonstrable user benefit and preserve a working local experience.

Initial testing exposed two operational problems: a model unavailable to new users and a replacement model repeatedly returning overload errors. Successful server startup is therefore not sufficient evidence of a working agent. Provider errors and long waits must be observable, and live chat must be checked explicitly when a model changes.

## Solution

Evolve the existing agent through ten independently demonstrable capabilities:

1. A deterministic Python tool.
2. Current-information answers with Google Search grounding.
3. Structured state within a conversation.
4. Explicit, persistent memory across conversations.
5. Answers grounded in an approved document collection.
6. A small specialist workflow.
7. Human approval before side effects.
8. One narrowly scoped MCP integration.
9. Automated behavioral tests and agent evaluations.
10. A focused custom UI and authenticated deployment.

These are capability areas, not a requirement to build ten services or ship everything together. Keep one Python ADK application and reuse its runner, session service, and public API boundaries. Introduce infrastructure only when a capability needs it.

### Existing baseline

- A Python agent with a Gemini model, greeting instructions, and no tools.
- Local execution through ADK's development UI or terminal.
- Dependency management with uv and a committed lockfile.
- API credentials kept in an ignored environment file.
- A configured 15-second request timeout per attempt and at most two attempts.
- No application test suite, custom UI, deployed service, or application-level authentication.

### Capability 1: deterministic tool

**User experience:** Ask for the total cost of several identical items, optionally including a tax percentage. The agent calls a Python tool and explains the result instead of inventing arithmetic.

**First implementation:** A quote-total calculator accepting a unit price, positive integer quantity, and optional nonnegative tax percentage. Use decimal arithmetic with documented two-decimal rounding. Return subtotal, tax, total, and currency; do not fetch exchange rates or imply that the quote is a purchase.

**Acceptance criteria:**

- A quote request produces the correct structured calculation and a readable explanation.
- Ordinary conversation does not unnecessarily invoke the tool.
- The tool validates external arguments: finite nonnegative price, positive integer quantity, tax between 0 and 100, and a supported currency. Start with USD only and state that limitation.
- Reject invalid inputs with an actionable message rather than a traceback or fabricated answer.
- The calculation is deterministic, read-only, and makes no network calls.
- Tool failures do not prevent a subsequent ordinary chat turn.

### Capability 2: Google Search grounding

**User experience:** Ask a question requiring current information, request a search explicitly, and inspect the sources supporting the answer.

**Implementation direction:** Use ADK's supported Google Search integration. Verify compatibility with the installed ADK release, selected Gemini model, and other tools before enabling it. If built-in search cannot coexist with custom tools in the chosen configuration, isolate it in a search specialist rather than silently dropping another capability.

**Acceptance criteria:**

- A current-information question can produce a grounded answer with inspectable source links and any provider-required attribution or search suggestions.
- Distinguish retrieved facts from the agent's interpretation; never invent citations.
- Unavailable search or a provider error is reported honestly, without claiming a search succeeded.
- Search is opt-in through configuration, with required credentials, billing implications, and compatibility documented.
- External pages and search snippets are untrusted data, not instructions that can authorize actions or reveal secrets.

### Capability 3: conversation state

**User experience:** Set a preference such as concise answers or a preferred display name, then have later messages in the same conversation honor it.

**Implementation direction:** Store explicit, structured values in ADK session state. Use a small allowlist of supported preferences rather than arbitrary model-written keys. Conversation state and long-term memory must remain distinct.

**Acceptance criteria:**

- A supported preference persists across turns in one session.
- The user can inspect, change, and clear supported session preferences.
- A fresh session begins without another session's preferences unless an explicitly saved long-term preference applies.
- Sessions are isolated by user and session identity; concurrent sessions do not overwrite one another's state.
- Session persistence across a local server restart is verified using the configured persistent session service, not assumed from in-memory tests.

### Capability 4: persistent memory

**User experience:** Explicitly ask the app to remember a non-sensitive preference, use it in a later conversation, and inspect or forget it.

**Implementation direction:** Start with explicit opt-in preference memory backed by durable local storage and an ADK-compatible memory integration. Do not automatically ingest every conversation or promise semantic recall before it is implemented. Introduce a managed memory backend only when deployment requirements justify it.

**Acceptance criteria:**

- Saving a supported preference requires an explicit user request.
- A new session for the same user can recall the saved preference after a server restart.
- Another user cannot retrieve it; user identity comes from trusted application context.
- The user can list saved preferences and delete one or all of them. Deleted values are no longer returned by retrieval, including any derived index.
- A session-specific preference overrides long-term memory for that session without silently changing the saved value.
- Do not save credentials, payment details, or sensitive personal data as preference memory. Report storage failures rather than claiming a save succeeded.

### Capability 5: document question answering

**User experience:** Choose an approved local document collection, ask questions about it, and receive answers with file and passage references.

**Implementation direction:** Begin with Markdown and plain-text files in an explicitly configured root. Use a simple bounded retrieval tool before adding embeddings, a vector database, or PDF parsing. Local-document retrieval and public web search must remain distinguishable in answers.

**Acceptance criteria:**

- Ingest only supported files inside the approved root, with explicit file-size, collection-size, result-count, and retrieved-context limits.
- Reject path traversal and symlink escapes. Do not ingest environment files, credentials, hidden configuration, or arbitrary filesystem locations.
- A matching question returns relevant passages with stable document identifiers and section or line references.
- Answers cite retrieved passages and acknowledge when the collection does not support a conclusion.
- Adding, changing, or removing a document is reflected after an explicit refresh; removed content is no longer retrievable.
- Document instructions cannot override system policy, trigger tools on their own, or authorize side effects.
- Explain that retrieved text is sent to the configured model provider; do not imply that a local index means fully local inference.

### Capability 6: specialist workflow

**User experience:** Request a short researched brief and receive a draft that has been reviewed for unsupported claims and missing citations.

**Implementation direction:** Start with a bounded sequential researcher → writer → reviewer workflow. Use ADK's workflow primitives and explicit handoffs. The researcher uses only enabled information sources, the writer uses the resulting evidence, and the reviewer returns an annotated final result. Parallel execution and open-ended delegation are later experiments, not required foundations.

**Acceptance criteria:**

- A workflow request follows the defined stages and preserves evidence references between them.
- The user can see stage progress and distinguish the final deliverable from intermediate outputs.
- Set finite model-call, tool-call, and output-size budgets. A failed stage terminates with a useful explanation instead of looping indefinitely.
- Unsupported claims are removed or flagged, not asserted as verified because another agent repeated them.
- Ordinary questions can still use the simple agent path without paying for the specialist workflow.
- Specialists do not gain broader filesystem or action permissions merely by delegation.

### Capability 7: approval before actions

**User experience:** Ask the app to draft a note, inspect the exact proposed write, and approve or reject it before anything changes.

**First action:** Create a new Markdown note in a configured output directory. No email sending, arbitrary shell access, deletion, or overwriting existing files in this increment.

**Implementation direction:** Separate proposal from execution. Prefer ADK tool confirmation when supported, but enforce authorization in the action boundary itself. A model statement saying an action is approved is never approval.

**Acceptance criteria:**

- A proposal shows the exact destination and contents before a write occurs.
- Only the initiating user/session can approve a pending proposal through a trusted confirmation surface.
- Approval is bound to immutable action parameters. Edits require a new proposal and approval.
- Rejecting, cancelling, or allowing approval to expire produces no side effect.
- Output paths are confined to the approved root; reject traversal, symlink escapes, and attempts to overwrite an existing file.
- Repeated approval or request replay does not execute the action twice.
- Keep an audit record of proposal identity, approval or rejection, and outcome without recording credentials.
- With no supported confirmation UI, actions remain unavailable; never bypass approval for convenience.

### Capability 8: MCP integration

**User experience:** Query one approved external data source through an MCP tool and see whether the operation succeeded.

**Implementation direction:** Connect one explicitly configured MCP server exposing a read-only lookup tool. Choose the actual service at implementation time based on user need and available credentials. Discover its capabilities, then allowlist the required tools. Do not enable every advertised tool by default.

**Acceptance criteria:**

- Document the selected server, transport, launch or connection procedure, credentials, exposed tools, and data sent externally.
- The app can invoke an allowlisted read-only tool and present its result.
- Missing credentials, timeout, disconnection, and malformed responses have actionable failure behavior and bounded retries.
- Server configuration is trusted operator configuration, not an arbitrary URL or command supplied in chat.
- Shut down subprocesses and connections cleanly; do not leave orphaned servers.
- Treat tool descriptions and results as untrusted external input. Do not expose write-capable MCP tools until they pass through the approval boundary from capability 7.
- The rest of chat works when MCP is disabled or unavailable.

### Capability 9: tests and evaluations

**User experience:** The developer can change instructions, tools, or models and receive evidence of what still works before asking a human to retry the website.

**Implementation direction:** Start automated tests with the first capability, not at the end of the roadmap. Grow a small evaluation corpus alongside each increment. Separate deterministic regression tests from opt-in live model evaluations and deployed smoke tests.

**Acceptance criteria:**

- One documented command runs offline tests without API credentials or paid requests.
- Test agent behavior through ADK's runner and public API boundaries, using controlled model responses and fake external services.
- Cover tool arguments and results, session continuity and isolation, memory deletion, retrieval citations, specialist handoffs, approval enforcement, MCP failures, and provider error handling.
- Evaluation cases include greetings, valid and invalid calculations, unsupported questions, current-information requests, memory changes, malicious retrieved instructions, denied actions, and provider overload.
- Live evaluations use an explicitly selected model, bounded case count, recorded model/version and configuration, and visible cost/quota warnings. They never run implicitly in ordinary offline CI.
- Assess tool selection, groundedness, task completion, refusal of unauthorized actions, latency, and call counts. Avoid exact wording assertions for free-form model answers.
- Establish acceptance thresholds per capability before its implementation is accepted; any unauthorized write or cross-user disclosure is an unconditional failure.
- Changing the configured model requires a live agent-response smoke test, not merely an import or server-start check.

### Capability 10: custom UI and deployment

**User experience:** Open a focused chat interface, sign in when hosted, start or resume a conversation, see progress and sources, and explicitly approve supported actions.

**Implementation direction:** Keep the ADK development UI for local debugging. Build a thin custom client backed by an authenticated application boundary over ADK's API. Do not expose the unauthenticated development server directly to the internet. Select the frontend and hosting platform when this phase begins rather than treating a particular vendor as already agreed.

**Acceptance criteria:**

- Support conversation creation/resumption, message submission, pending/working states, source links, and readable tool or provider errors.
- Support the approval flow with a clearly separate approve/reject control; sending ordinary chat text cannot simulate approval.
- Do not present an indefinitely blank answer: show request progress, bounded failure behavior, and a retry option that warns when action execution status is uncertain.
- Cancellation stops server-side work where supported; otherwise mark it cancelled to the user and prevent new actions while reporting any action that already completed.
- Render model and tool output safely; sanitize Markdown, disallow raw executable HTML, and validate outbound link schemes.
- Hosted requests authenticate users and authorize access to their sessions, memory, documents, and proposals. Never trust an arbitrary client-supplied user ID.
- Store credentials only server-side. Configure explicit allowed origins, CSRF protection where cookie authentication is used, request-size limits, rate limits, and finite per-run budgets.
- Hosted state survives process restarts; deployment docs identify storage, secret injection, retention, backup/deletion limits, and operational costs.
- Provide liveness/readiness checks plus an opt-in end-to-end inference smoke test. Readiness alone is not proof that the model is available.
- Deployment has reproducible setup and rollback instructions. Browser keyboard operation, labelled controls, readable errors, and status announcements are verified.

## User Stories

1. As a developer, I want each capability delivered as a small working increment, so that I can learn ADK without losing a runnable app.
2. As a user, I want accurate quote calculations, so that I do not rely on model-generated arithmetic.
3. As a user, I want invalid calculation inputs explained, so that I can correct my request.
4. As a user, I want to distinguish a calculated quote from a purchase, so that a read-only tool cannot imply a transaction occurred.
5. As a user, I want current information retrieved when needed, so that answers are not limited to model training data.
6. As a user, I want inspectable search sources, so that I can verify claims.
7. As a user, I want unavailable search reported honestly, so that I can distinguish evidence from guesses.
8. As a user, I want to set conversational preferences, so that replies fit the current task.
9. As a user, I want to inspect and reset session preferences, so that I understand what influences replies.
10. As a user, I want separate conversations to have separate state, so that one task does not contaminate another.
11. As a user, I want explicit control over what is remembered, so that conversation content is not silently retained as long-term memory.
12. As a returning user, I want saved preferences available in a new conversation, so that I do not repeat myself.
13. As a user, I want to list and delete saved preferences, so that I control persistent personalization.
14. As a user, I want session preferences to override saved preferences temporarily, so that an exception does not rewrite my defaults.
15. As a user, I want other users excluded from my state and memory, so that private context stays private.
16. As a user, I want answers about an approved document collection, so that I can use my own reference material.
17. As a user, I want document citations with passage locations, so that I can inspect supporting evidence.
18. As a user, I want the agent to admit missing evidence, so that unsupported claims are not presented as document facts.
19. As a user, I want document refresh and removal to work, so that answers reflect my current collection.
20. As a user, I want to know when document passages leave my machine, so that I can make informed privacy choices.
21. As a user, I want a researcher, writer, and reviewer to collaborate on a brief, so that the result has evidence and a quality check.
22. As a user, I want visible workflow progress, so that I understand why a complex request takes longer.
23. As a user, I want simple questions to stay inexpensive, so that specialist workflows run only when appropriate.
24. As a user, I want failures in a workflow explained, so that partial work is not mistaken for a completed result.
25. As a user, I want to preview a proposed note before creation, so that I can verify its destination and contents.
26. As a user, I want approve and reject controls, so that only intended side effects occur.
27. As a user, I want modified proposals to need fresh approval, so that approval cannot authorize a different action.
28. As a user, I want repeated confirmations to be harmless, so that retries do not create duplicate notes.
29. As a developer, I want one read-only MCP integration, so that I can learn interoperability without granting broad permissions.
30. As an operator, I want an explicit MCP tool allowlist, so that server updates cannot silently expand agent authority.
31. As a user, I want MCP outages to leave ordinary chat usable, so that an optional integration does not disable the app.
32. As a developer, I want fast offline behavioral tests, so that most regressions are caught without API calls.
33. As a developer, I want opt-in live evaluations, so that I can verify real model behavior while controlling spend.
34. As a developer, I want evaluations of tool choice and evidence use, so that fluent prose is not confused with correct behavior.
35. As an operator, I want model changes verified with a real response, so that unavailable model names are caught before user testing.
36. As a user, I want a focused chat UI with explicit working and error states, so that waiting does not look like a broken page.
37. As a user, I want to resume my own conversations, so that I can continue work across visits.
38. As a user, I want to cancel work, so that I can stop an unwanted or stalled request.
39. As a keyboard or assistive-technology user, I want accessible chat and approval controls, so that I can use the same capabilities.
40. As an operator, I want authentication, rate limits, and bounded runs, so that a hosted agent is not an open proxy for paid API usage.
41. As an operator, I want sanitized output and scoped credentials, so that external content cannot compromise users or integrations.
42. As an operator, I want reproducible deployment and rollback, so that releasing a change does not strand the app in a broken state.

## Implementation Decisions

- Extend the existing Python ADK agent rather than replacing it with another agent framework or introducing services per capability.
- Keep the currently working model as the baseline, but verify feature compatibility before adding provider-specific tools. Do not assume the latest or listed model is callable by this account.
- Treat the capability designs above as the implementation target. Provider-specific APIs, the MCP service, and hosting choices require verification at the start of their increments; no live infrastructure is provisioned by this spec.
- Use structured tool results and session values. Validate external tool arguments and external-service responses at their boundaries, not with redundant checks throughout trusted internal code.
- Use ADK session services for conversation state and durable storage for explicit preference memory. Do not conflate transcript persistence with permission to extract long-term memory.
- Separate information retrieval from action execution. Search, documents, model text, and MCP results cannot grant permissions.
- Persist approval proposals as immutable action descriptions with ownership, lifecycle state, expiry, and execution outcome. Enforce idempotency at execution, not through prompting alone.
- Start with a single trusted local operator identity. Before exposing a hosted API, derive identity from authentication and enforce ownership at every public resource boundary.
- Preserve bounded provider retries. Transport timeout is not an end-to-end run deadline; add a total run budget and observable terminal status for workflows and custom API requests.
- Record structured operational events for run identity, stage, tool invocation, elapsed time, retry/failure category, and token/call usage where supplied. Do not log API keys or full private documents by default.
- Prefer ADK's existing API and event contracts. Add only the application endpoints necessary for ownership, saved preferences, document refresh, and trusted approvals; do not invent a general plugin framework.
- Keep optional search, document retrieval, memory, workflow, and MCP capabilities explicitly configurable. Missing optional credentials must not break basic chat.
- Give each increment a short run/demo procedure and explicit completion evidence. A server returning HTTP 200 is insufficient if the event stream contains an error or never produces an assistant result.

### Delivery order and dependencies

1. **Foundation:** deterministic tool plus the first offline runner/API tests and a live smoke-test procedure (capabilities 1 and the foundation of 9).
2. **Conversation:** session state, then explicit persistent memory (3 → 4), extending tests for restart behavior and isolation.
3. **Evidence:** search and local document retrieval (2 and 5); they can be implemented independently once the test foundation exists.
4. **Collaboration:** bounded specialist workflow after at least one evidence source works (6 depends on 2 or 5).
5. **Controlled actions:** note proposals and trusted approval before any write-capable integration (7).
6. **Interoperability:** a read-only MCP connection once there is a concrete service to integrate (8). Any later MCP writes depend on 7.
7. **Release:** expand the evaluation suite throughout delivery, then complete custom UI and authenticated hosting (9 and 10). The custom client may start earlier, but public deployment is gated on authentication, isolation, bounded runs, and approval tests.

## Testing Decisions

The user approved testing through ADK's runner/API boundary with fake model and external-service responses, separate opt-in live checks, and browser tests when a custom UI exists.

- Prefer the highest existing seam: submit a user turn through the runner or public API and assert observable messages, events, persisted state, tool effects, and authorization outcomes. Do not assert internal method calls or incidental prompt wording.
- Use deterministic model fakes to request tool calls and simulate follow-up replies. These prove orchestration and safety behavior, not whether a real model reliably selects the tool; live evaluations cover that distinction.
- Test arithmetic rounding and argument validation directly at the tool boundary where precise edge cases are easier to express. Keep additional low-level seams exceptional.
- Exercise real temporary durable storage for session restart, preference deletion, document refresh, and approval idempotency tests. A fake dictionary cannot prove restart persistence.
- Replace search, MCP, and provider transport with controlled external-boundary fakes in offline tests. Include slow responses, malformed payloads, disconnections, unavailable models, overload, and cancellation.
- Test malicious search passages, document text, MCP responses, path traversal, symlink escapes, forged approval, proposal mutation, replay, and cross-user identifiers. Assert no forbidden side effect or disclosure, not just a polite refusal message.
- Test multi-agent workflows from request to final deliverable with bounded calls, preserved citations, stage failures, and ordinary-chat bypass behavior.
- Add browser end-to-end coverage for send/resume, source display, accessible progress/errors, approve/reject, cancellation, and session ownership through the real application API with controlled upstream responses.
- Run live Gemini and tool checks only with explicit credentials and opt-in execution. Record configuration and latency; do not put volatile provider behavior into the mandatory offline suite.
- For deployment, test unauthorized requests and cross-user resource access before a public release, then verify a genuine assistant response through the deployed chat path.
- There is no existing test suite to copy. The initial runner/API harness becomes the shared prior art for later increments; do not introduce a separate testing architecture per capability.

### Definition of done for each increment

- Its acceptance criteria have automated evidence where deterministic testing is possible.
- Offline tests pass without paid API access.
- An opt-in end-to-end smoke test demonstrates the newly enabled real integration when applicable, or explicitly records that verification is blocked rather than claiming success.
- Failure behavior and security boundaries are tested, not only the happy path.
- Setup, credentials, costs, limitations, and a reproducible demonstration are documented.
- Existing basic chat remains functional with optional integrations disabled.

## Out of Scope

- Implementing these capabilities as part of writing this spec.
- Automatically creating implementation tickets or provisioning external accounts.
- Autonomous purchases, email sending, destructive file operations, arbitrary shell execution, or unrestricted filesystem access.
- Automatic extraction of sensitive personal facts or wholesale transcript ingestion into long-term memory.
- PDF/OCR ingestion, embeddings, and a vector database in the first document-retrieval increment.
- General-purpose multi-agent planning, unbounded reviewer loops, or a custom orchestration framework.
- Installing arbitrary MCP servers or accepting MCP launch commands from chat.
- Voice/video, fine-tuning, enterprise SSO, complex role hierarchies, high-availability clustering, and a general multi-tenant SaaS product.
- An automatic switch to an unverified model during provider outages.
- Selecting a frontend framework, hosting vendor, or concrete external MCP service without the needs and compatibility checks for that increment.

## Further Notes

- This is a roadmap-sized spec, not a single implementation task. Break it into tracer-bullet tickets before implementation; each should deliver observable behavior and tests rather than an isolated infrastructure layer.
- Suggested starting slice: a correct quote tool, a runner/API behavioral test, and a real chat smoke check. Next add conversation state. This preserves the earlier recommendation to start with capabilities 1 → 3 → 9 while treating evaluation as continuous work rather than a late phase.
- Retain the development UI for local diagnosis. Public users must use the authenticated application surface, never an internet-exposed ADK development server.
- Unresolved implementation choices: the concrete MCP data source; search/model compatibility; hosted identity, persistence, frontend, and deployment provider. Resolve them in their own increments before committing to provider-specific implementation tickets. They do not block the first local tool/state/testing increments.
- Review cloud data retention, document privacy, provider terms, and estimated usage costs before enabling external retrieval or hosting with real private data.
