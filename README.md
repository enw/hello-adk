# Google ADK hello world

Minimal Python agent using Google's [Agent Development Kit](https://google.github.io/adk-docs/).

## Setup

Requires [uv](https://docs.astral.sh/uv/) and Python 3.12+.

```sh
uv sync
cp hello_world/.env.example hello_world/.env
```

Get a [Gemini API key](https://aistudio.google.com/apikey), then replace the placeholder in `hello_world/.env`. This file is ignored by Git. API usage may incur charges, depending on your quota and billing settings.

## Run

Browser UI:

```sh
uv run adk web
```

Open http://127.0.0.1:8000, select `hello_world`, and say hello.
Keep this development server local; it has no authentication.

Or chat in your terminal:

```sh
uv run adk run hello_world
```

Edit `hello_world/agent.py` to change the agent's instructions or model (currently `gemini-3.5-flash-lite`). Requests use a 15-second timeout per attempt and at most two attempts.

## Quote calculator

Try in the existing web UI or terminal:

> What's the total for 3 items at $19.99 each, with 8.25% sales tax? Show subtotal, tax, and total.

Expected USD quote: **subtotal 59.97, tax 4.95, total 64.92**. This is a read-only calculation, not a purchase; no payment or external lookup occurs.

The agent uses `calculate_quote` for quote arithmetic. Prices and tax percentages are decimal strings; quantity is a positive integer. Tax defaults to zero. Only USD is supported. Invalid inputs return an error without a total. For example:

- “Quote -3 items at $19.99.” → request a positive integer quantity.
- “Quote 3 items at $19.99 with 101% tax.” → explain the 0–100% tax limit.
- “Quote 3 items at EUR 19.99.” → explain that only USD is supported; do not convert currencies.

Rounding: multiply the decimal unit price by quantity, round subtotal to two decimals using `ROUND_HALF_UP`, calculate tax on that rounded subtotal and round tax the same way, then add them. Results are two-decimal strings. Values exceeding supported decimal precision return an actionable error rather than a partial quote.

## Session response style

The agent can remember one preference **within the current conversation**: `concise` or `standard` (the default). No preference is shared with a new conversation or another user.

Try these in one web-UI conversation:

1. “Use concise responses for this conversation.”
2. “What's my current response style? Check the preference tool.” → `concise`.
3. Ask the quote example above → still includes all three amounts, with a short explanation.
4. “Use standard responses instead.” → `standard`.
5. “Reset my response style preference.” → `standard`.
6. Start a **new session** and inspect its style → `standard`, regardless of another session's setting.

Only those two styles are stored. Invalid tool actions/styles return errors without changing the preference. Concise is a best-effort instruction to use at most two sentences when practical, not a hard output truncation.

For persistence testing, set concise, note the conversation/session, stop and restart `uv run adk web`, then **resume that same conversation** and inspect the style. It should still be concise. Default local ADK session storage under `hello_world/.adk/` preserves it; in-memory sessions do not survive restart. Resetting clears the effective preference back to standard, not the conversation history. This is not long-term cross-chat memory. The development UI remains local-only and unauthenticated; user-ID isolation in tests is not hosted authentication.

## Verify

After `uv sync`, run the offline suite (standard-library `unittest`; no added test dependencies):

```sh
uv run --offline python -m unittest discover -s tests -v
```

No API credentials or paid requests are required. Runner tests substitute a controlled model and block network connections. They verify real tool execution, validation, greetings, and recovery within a session—not real-model tool selection or exact model wording.

Explicitly opt in to a **live** check, using your configured Gemini key (API usage may incur charges):

```sh
uv run python -m hello_world.smoke --live
```

Without `--live`, the command refuses to run. Missing credentials, provider errors, a wrong result, or no final quote are failures (nonzero exit). It checks the configured agent's real calculator invocation, exact structured result, and final answer containing all three amounts. It uses an isolated in-memory session, a 45-second run deadline, and at most four model calls; it does not require the web server. Live checks are never part of the offline suite. Server startup or HTTP 200 alone is not verification.

For the live multi-turn session scenario:

```sh
uv run python -m hello_world.smoke --live --scenario session
```

This checks set → inspect → quote in concise mode → clear → inspect in one isolated in-memory session. Each step must produce its expected real tool result and a final reply. It has a 90-second total run deadline and at most four model calls per turn (five turns, at most twenty calls). API charges may apply. Restart persistence is tested offline with real temporary SQLite storage and a fresh runner/service; the live scenario does not claim to test persistence.

The offline suite also checks defaults, preference changes, invalid-input nonmutation, per-request instruction updates, user/session isolation, and SQLite reopen/resume behavior. The existing quote smoke command remains unchanged.
