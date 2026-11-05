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
