# ADK capabilities roadmap

Source: [capability spec](spec.md).

## Working agreement

Plan broadly, execute one slice at a time. Detail and approve only the next small end-to-end slice. Each slice includes behavior, automated tests, necessary documentation, and a demonstration. Later rows are outcomes and genuine dependencies, not implementation tickets.

After a slice is verified, record evidence and lessons, update its status, then choose and detail the next slice. Do not advance automatically or treat roadmap order as authorization to implement.

## Current frontier

[01 — Calculate validated USD quotes through chat](issues/01-calculate-usd-quotes.md) is completed and verified. See [results and lessons](results-01.md). Stopped here: no next-slice tickets or implementation authorized.

## Capability map

| Capability | User-visible outcome | Gates / ordering |
| --- | --- | --- |
| 1. Python tool | Accurate, validated USD quotes through chat | Completed ticket 01; offline tests and live runner/web-API checks passed |
| 3. Conversation state | Inspect, change, and clear preferences within an isolated session | Recommended next after the first slice is verified |
| 4. Persistent memory | Explicitly save, recall, and delete preferences across sessions | Conversation state and a trusted local user identity |
| 2. Search grounding | Current-information answers with inspectable sources | Verify model/tool compatibility; reuse the test foundation |
| 5. Document retrieval | Cited answers from an approved local collection | Choose collection and limits; reuse the test foundation |
| 6. Specialists | A bounded researched brief with evidence and review | At least one working evidence source: search or documents |
| 7. Human approval | Preview and approve a confined Markdown note creation | Trusted approval surface and execution-boundary authorization |
| 8. MCP | Query one explicitly approved read-only external source | Choose a useful service and allowlisted tools; any later writes require approval |
| 9. Evaluations | Repeatable evidence of correctness, safety, and real integration behavior | Starts in slice one; grows with every capability, not a final testing phase |
| 10. Custom UI + deployment | Accessible chat with progress, sources, approvals, and safe hosted access | Public release requires authentication, ownership checks, durable storage, bounded runs, and evaluation evidence |

Rows are not tickets. Select one narrow user-visible behavior within a capability when it reaches the frontier; split larger capabilities only then.

## First-slice completion gate

- A real quote request produces correct subtotal, tax, and total through the existing agent.
- Invalid tool input fails safely; a subsequent chat turn still works.
- Repeatable offline tests require no credentials or paid calls.
- An explicit live smoke check confirms real tool use and a final response, not just server startup; report blocked verification honestly.
- Record the demo commands, results, and lessons before planning conversation state.

## Deferred choices

Resolve only when relevant: search/model compatibility, concrete MCP service, document collection, hosted identity/storage, frontend, and deployment provider.

## Completed slices and lessons

- **01 — USD quote tool:** completed. Six offline tests pass; live configured-agent and existing web-API checks observed real tool execution and the correct final quote. [Evidence and lessons](results-01.md).
- Reuse the runner boundary and standard-library test setup. Keep live tool-selection checks separate from controlled-model offline tests. No new test dependency was necessary.
- No next slice detailed or implemented.
