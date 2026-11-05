# Slice 01: verification and lessons

Outcome: completed. Only the USD quote slice was implemented. No commit made; no later slice planned or implemented.

## Delivered

- Read-only `calculate_quote` exposed through the existing agent.
- Decimal USD subtotal, tax, and total with explicit half-up cent rounding; tax calculated on the rounded subtotal.
- Boundary errors without totals for invalid quantity, non-finite/negative/malformed decimal input, tax outside 0–100%, unsupported currency, and values exceeding decimal precision.
- Standard-library offline tests; no new dependencies or lockfile changes.
- Explicitly opt-in live smoke command with a 45-second run deadline and four-model-call limit.
- README setup/demo/verification instructions. Existing web and terminal entry points retained.

## TDD evidence

1. Wrote a runner-level taxed-quote test first. It failed because `calculate_quote` was not registered; ADK returned a missing-tool error.
2. Implemented the minimal decimal tool and agent registration. The runner test passed.
3. Added invalid-argument boundary cases. The test failed with nine failures and eight errors against the happy-path-only implementation.
4. Added boundary validation and structured error results. Both tests passed.
5. Extended coverage for subtotal/tax rounding, zero and maximum tax, greetings, and invalid-tool-call recovery in the same session. All five tests passed.
6. Added an explicit-opt-in smoke-command test. It failed because the command did not yet exist. Implemented the command; all six tests passed.

## Verification results

### Offline

Command:

```sh
uv run --offline python -m unittest discover -s tests -v
```

Result: **6 tests passed**. Repeated successfully with `GOOGLE_API_KEY`, `GEMINI_API_KEY`, and `GOOGLE_APPLICATION_CREDENTIALS` removed from the process environment. Runner/calculator tests block socket connections and substitute only the external model, not the calculator or ADK runner. The smoke-command test invokes the command without opt-in and confirms refusal before credential loading or any provider request.

Coverage includes 17 invalid-argument cases, four rounding/default/tax-limit cases, exact runner-level structured quote output, ordinary greeting without tools, and successful chat after an invalid tool call. ADK emits benign missing-token-metadata warnings for the fake model.

### Live configured agent

Command:

```sh
uv run python -m hello_world.smoke --live
```

Result: **PASS** with `gemini-3.5-flash-lite`. Observed a real calculator invocation, exact structured result (`59.97` subtotal, `4.95` tax, `64.92` total, USD), and a final assistant answer containing all three amounts. This incurred opt-in provider requests; no credentials were logged.

### Existing web API

Restarted the existing local ADK web server to load the tool. Created an isolated smoke-test session and submitted the quote through its chat event-stream endpoint. Result: **PASS**; observed the calculator call, exact structured result, and final answer. Verified the actual API/event stream rather than treating its HTTP 200 as success. No browser automation was performed.

The server remains available at http://127.0.0.1:8000. Refresh the development UI and submit the README example to demo it.

### Repository checks

- Dependency lock check passed; no added dependency required.
- Whitespace check passed.
- API credentials, local sessions, and Python caches remain ignored by Git.

## Lessons

- A runner with a controlled model catches actual tool-registration and execution errors without paying for inference. It does not prove real-model tool selection; the live check supplies that evidence separately.
- Invalid tool arguments are normal boundary input. Return structured actionable errors rather than allowing decimal exceptions or fabricated totals.
- Preserve decimal results as strings and state where rounding happens; subtotal-first rounding is part of the contract.
- A real integration check must inspect both tool events and the final answer. Server health and a successful HTTP status are insufficient.
- Existing ADK interfaces plus standard-library unittest were sufficient; no app factory, custom API, test framework dependency, or tool abstraction was needed.

## Stop point

Ticket 01 is complete. Stop here. Conversation state and all other capabilities remain roadmap outcomes only; wait for user authorization before detailing or implementing another slice.
