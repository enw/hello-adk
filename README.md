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
