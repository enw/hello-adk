"""Chat server: FastAPI + Server-Sent Events over the hello_world agent.

Sessions persist in Postgres through ADK's DatabaseSessionService (Neon in
production; tests inject an InMemorySessionService). Every /api/* request must
carry an x-chat-token header matching APP_TOKEN; an unset APP_TOKEN rejects
everyone, so production never runs accidentally open. The UI is one static
file with no build step. Deployed as a single Vercel Python function
(vercel.json) where uvicorn's app is imported from this module.
"""

from __future__ import annotations

import hmac
import json
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncIterator

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from google.adk.agents.run_config import RunConfig, StreamingMode
from google.adk.runners import Runner
from google.adk.sessions import BaseSessionService, DatabaseSessionService
from google.genai import types
from pydantic import BaseModel
from sqlalchemy.engine import make_url

from hello_world.agent import root_agent

# Local runs read hello_world/.env (gitignored); on Vercel it does not exist
# and real env vars win because load_dotenv never overrides.
load_dotenv(Path(__file__).parent / "hello_world" / ".env")

APP_NAME = "hello_world"
USER_ID = "enw"
MAX_LLM_CALLS = 8
STATIC_INDEX = Path(__file__).parent / "static" / "index.html"


class ChatRequest(BaseModel):
    session_id: str
    text: str


def _epoch_ms(value: Any) -> int | None:
    """Normalize ADK timestamps (datetime or float seconds) to epoch ms."""
    if value is None:
        return None
    return int(value.timestamp() * 1000) if hasattr(value, "timestamp") else int(value * 1000)


def _sse(payload: dict) -> str:
    return f"data: {json.dumps(payload, default=str)}\n\n"


def _event_items(event) -> list[dict]:
    """Flatten one persisted event into client-renderable items."""
    items = []
    for part in (event.content.parts if event.content else None) or []:
        if part.text:
            items.append({"kind": "text", "author": event.author, "text": part.text, "ts": _epoch_ms(event.timestamp)})
        elif part.function_call:
            items.append({"kind": "call", "name": part.function_call.name, "args": part.function_call.args})
        elif part.function_response:
            items.append({"kind": "response", "name": part.function_response.name, "response": part.function_response.response})
    return items


def _db_service(db_url: str) -> DatabaseSessionService:
    """Neon connection strings carry libpq's sslmode, but SQLAlchemy's
    asyncpg dialect forwards URL params to asyncpg.connect verbatim and
    asyncpg spells it ssl=. Strip sslmode from the URL and pass it along."""
    url = make_url(db_url)
    query = dict(url.query)
    mode = query.pop("sslmode", None)
    # str(URL) masks the password; render_as_string keeps it usable.
    cleaned = url.set(query=query).render_as_string(hide_password=False)
    if mode:
        return DatabaseSessionService(db_url=cleaned, connect_args={"ssl": mode})
    return DatabaseSessionService(db_url=cleaned)


class TokenGate:
    """ASGI middleware guarding /api/*; a missing APP_TOKEN fails closed."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http" and scope["path"].startswith("/api/"):
            expected = os.environ.get("APP_TOKEN", "")
            provided = next((v.decode() for k, v in scope.get("headers", []) if k == b"x-chat-token"), "")
            if not expected or not hmac.compare_digest(expected.encode(), provided.encode()):
                await send({"type": "http.response.start", "status": 401,
                            "headers": [(b"content-type", b"application/json")]})
                await send({"type": "http.response.body", "body": b'{"error":"unauthorized"}'})
                return
        await self.app(scope, receive, send)


def create_app(service: BaseSessionService | None = None, agent=None) -> FastAPI:
    """Compose the server. Tests inject a service and a scripted agent;
    production reads DATABASE_URL and uses the Gemini root_agent."""
    owns_service = service is None and bool(os.environ.get("DATABASE_URL"))
    if service is None:
        service = _db_service(os.environ["DATABASE_URL"]) if os.environ.get("DATABASE_URL") else None
    agent = agent or root_agent

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        if service is None:
            raise RuntimeError("DATABASE_URL is not set; the chat server needs Postgres sessions")
        prepare = getattr(service, "prepare_tables", None)
        if prepare is not None:
            await prepare()
        yield
        if owns_service:
            close = getattr(service, "close", None)
            if close is not None:
                await close()

    app = FastAPI(lifespan=lifespan)
    app.add_middleware(TokenGate)

    def model_name() -> str:
        model = agent.model
        return model if isinstance(model, str) else getattr(model, "model", "unknown")

    @app.get("/api/state")
    async def get_state() -> dict:
        return {"model": model_name(), "app": APP_NAME, "user": USER_ID, "max_llm_calls": MAX_LLM_CALLS}

    @app.get("/api/sessions")
    async def get_sessions() -> dict:
        found = await service.list_sessions(app_name=APP_NAME, user_id=USER_ID)
        return {"sessions": [{"id": s.id, "updated": _epoch_ms(s.last_update_time)} for s in found.sessions]}

    @app.post("/api/sessions")
    async def post_session() -> dict:
        created = await service.create_session(app_name=APP_NAME, user_id=USER_ID)
        return {"id": created.id, "updated": _epoch_ms(created.last_update_time)}

    @app.delete("/api/sessions/{session_id}")
    async def delete_session(session_id: str) -> dict:
        if await service.get_session(app_name=APP_NAME, user_id=USER_ID, session_id=session_id) is None:
            raise HTTPException(status_code=404, detail="unknown session")
        await service.delete_session(app_name=APP_NAME, user_id=USER_ID, session_id=session_id)
        return {"ok": True}

    @app.get("/api/sessions/{session_id}/messages")
    async def get_messages(session_id: str) -> dict:
        session = await service.get_session(app_name=APP_NAME, user_id=USER_ID, session_id=session_id)
        if session is None:
            raise HTTPException(status_code=404, detail="unknown session")
        # Persisted events carry full turns; partial stream chunks are not stored,
        # but the filter keeps that invariant true if that ever changes.
        return {"items": [item for event in session.events if not event.partial for item in _event_items(event)]}

    @app.post("/api/chat")
    async def post_chat(req: ChatRequest):
        if not req.text.strip():
            raise HTTPException(status_code=422, detail="empty message")
        if await service.get_session(app_name=APP_NAME, user_id=USER_ID, session_id=req.session_id) is None:
            raise HTTPException(status_code=404, detail="unknown session")

        async def stream() -> AsyncIterator[str]:
            streamed = ""  # text already sent as deltas within the current model turn
            try:
                # One runner per request, never closed: closing it would close
                # the shared session service every other request still uses.
                runner = Runner(agent=agent, app_name=APP_NAME, session_service=service)
                run = runner.run_async(
                    user_id=USER_ID,
                    session_id=req.session_id,
                    new_message=types.Content(role="user", parts=[types.Part(text=req.text)]),
                    run_config=RunConfig(streaming_mode=StreamingMode.SSE, max_llm_calls=MAX_LLM_CALLS),
                )
                async for event in run:
                    if event.error_message:
                        yield _sse({"type": "error", "message": event.error_message})
                        continue
                    parts = (event.content.parts if event.content else None) or []
                    for part in parts:
                        if part.function_call and not event.partial:
                            yield _sse({"type": "tool", "phase": "call",
                                        "name": part.function_call.name, "args": part.function_call.args})
                        elif part.function_response and not event.partial:
                            yield _sse({"type": "tool", "phase": "result",
                                        "name": part.function_response.name, "response": part.function_response.response})
                    text = "".join(part.text for part in parts if part.text)
                    if not text:
                        continue
                    if event.partial:
                        streamed += text
                        yield _sse({"type": "delta", "text": text})
                    elif text != streamed:
                        # Aggregated finals are authoritative: ADK SSE can
                        # duplicate partial text, so replace instead of append.
                        yield _sse({"type": "replace", "text": text})
                        streamed = ""
                    else:
                        streamed = ""
                yield _sse({"type": "done"})
            except Exception as exc:  # every failure must reach the client on the stream
                yield _sse({"type": "error", "message": f"{type(exc).__name__}: {exc}"})

        return StreamingResponse(stream(), media_type="text/event-stream",
                                 headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

    @app.get("/", include_in_schema=False)
    async def index():
        return FileResponse(STATIC_INDEX)

    return app


app = create_app()
