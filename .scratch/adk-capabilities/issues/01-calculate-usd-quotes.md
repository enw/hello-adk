# 01: Calculate validated USD quotes through chat

**What to build:** Ask the existing agent for the cost of several identical items, optionally including tax, and receive an accurate USD quote calculated by a deterministic Python tool. Invalid inputs fail safely, ordinary conversation remains usable, and the developer can verify the behavior offline and with an explicit live smoke check.

**Blocked by:** None (can start immediately).

**Status:** completed

Verification and lessons: [slice 01 results](../results-01.md).

## Acceptance criteria

- [x] The existing chat agent exposes a read-only quote calculator accepting unit price, positive integer quantity, optional tax percentage, and currency (USD only).
- [x] Use decimal arithmetic, document the two-decimal rounding policy, and return structured subtotal, tax, total, and currency. A quote for three items at USD 19.99 with 8.25% tax returns subtotal 59.97, tax 4.95, and total 64.92.
- [x] Validate arguments at the tool boundary: reject non-finite or negative prices, non-integer or nonpositive quantities, tax outside 0–100%, and unsupported currencies. Invalid requests return actionable errors rather than tracebacks or fabricated totals.
- [x] Instructions distinguish a quote from a purchase and direct the agent to use the calculator for quote arithmetic. The calculator performs no network calls or other side effects.
- [x] Offline tests exercise tool-call arguments, structured results, and completion through ADK's runner/public API boundary using controlled model responses. Direct boundary tests cover arithmetic and validation edge cases.
- [x] Offline tests cover a normal greeting without a tool call and a failed calculation followed by a successful ordinary chat turn in the same session. Do not claim fake-model tests prove real-model tool selection.
- [x] One documented command runs the offline suite without credentials, network access, or paid API calls. Include only the test dependencies needed for this slice.
- [x] Provide a separately invoked live smoke check that requires explicit opt-in and credentials, exercises the actual configured agent/model, observes a calculator invocation and its correct result, and requires a final assistant response. Server startup or HTTP 200 alone does not pass.
- [x] Keep live verification bounded; report provider errors, missing credentials, and incomplete verification honestly. Live checks never run as part of the default offline suite.
- [x] Document setup, offline/live verification commands, example valid and invalid prompts, and possible API costs. Preserve the existing UI and terminal workflows.
- [x] Record verification evidence and lessons before marking the slice completed. If live verification is blocked, record the blocker rather than claiming the completion gate passed.

## Scope boundary

Deliver only this slice. Do not add session preferences, persistent memory, search, retrieval, specialists, approval actions, MCP, a custom UI, hosting, or a general tool framework. Reuse the existing ADK boundaries; no prefactoring is currently required.

## Source

Capability 1 and the initial testing foundation of capability 9 in the parent ADK capabilities spec. Ticket granularity and lack of blockers approved by the user.
