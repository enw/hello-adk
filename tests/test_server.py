import json
import os
import socket
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from google.adk.models import BaseLlm
from google.adk.models.llm_response import LlmResponse
from google.adk.sessions import InMemorySessionService
from google.genai import types

from hello_world.agent import root_agent
from main import create_app


class ScriptedModel(BaseLlm):
    model: str = "offline-test"
    replies: list[types.Content]

    async def generate_content_async(self, llm_request, stream=False):
        yield LlmResponse(content=self.replies.pop(0))


def reply(*parts):
    return types.Content(role="model", parts=list(parts))


def tool_call(**arguments):
    return reply(types.Part.from_function_call(name="calculate_quote", args=arguments))


AUTH = {"x-chat-token": "test-token"}


def sse_events(response):
    events = []
    for block in response.text.split("\n\n"):
        for line in block.split("\n"):
            if line.startswith("data:"):
                events.append(json.loads(line[len("data:"):]))
    return events


class ServerTests(unittest.TestCase):
    def setUp(self):
        network = patch.object(socket.socket, "connect", side_effect=AssertionError("Offline tests forbid network"))
        network.start()
        self.addCleanup(network.stop)
        env = patch.dict(os.environ, {"APP_TOKEN": "test-token"})
        env.start()
        self.addCleanup(env.stop)

    def client(self, replies):
        agent = root_agent.model_copy(update={"model": ScriptedModel(replies=list(replies))})
        return self.enterContext(TestClient(create_app(service=InMemorySessionService(), agent=agent)))

    def test_index_served_without_token(self):
        client = self.client([])
        response = client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("<!doctype html>", response.text.lower())

    def test_api_requires_the_configured_token(self):
        client = self.client([])
        self.assertEqual(client.get("/api/state").status_code, 401)
        self.assertEqual(client.get("/api/state", headers={"x-chat-token": "wrong"}).status_code, 401)
        response = client.get("/api/state", headers=AUTH)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["model"], "offline-test")
        self.assertEqual(response.json()["user"], "enw")

    def test_unset_app_token_fails_closed(self):
        os.environ.pop("APP_TOKEN", None)
        client = self.client([])
        response = client.get("/api/state", headers={"x-chat-token": "anything"})
        self.assertEqual(response.status_code, 401)

    def test_session_crud_roundtrip(self):
        client = self.client([])
        created = client.post("/api/sessions", headers=AUTH).json()
        listed = client.get("/api/sessions", headers=AUTH).json()["sessions"]
        self.assertIn(created["id"], [s["id"] for s in listed])
        messages = client.get(f"/api/sessions/{created['id']}/messages", headers=AUTH)
        self.assertEqual(messages.status_code, 200)
        self.assertEqual(messages.json()["items"], [])
        deleted = client.delete(f"/api/sessions/{created['id']}", headers=AUTH)
        self.assertEqual(deleted.status_code, 200)
        self.assertEqual(
            client.get(f"/api/sessions/{created['id']}/messages", headers=AUTH).status_code, 404
        )

    def test_session_list_titles_come_from_first_user_message(self):
        client = self.client([reply(types.Part(text="Answer."))])
        session = client.post("/api/sessions", headers=AUTH).json()["id"]
        client.post("/api/chat", headers=AUTH,
                    json={"session_id": session, "text": "  hello   there  "})
        listed = client.get("/api/sessions", headers=AUTH).json()["sessions"]
        mine = next(s for s in listed if s["id"] == session)
        self.assertEqual(mine["title"], "hello there")

    def test_session_without_messages_lists_untitled(self):
        client = self.client([])
        session = client.post("/api/sessions", headers=AUTH).json()["id"]
        listed = client.get("/api/sessions", headers=AUTH).json()["sessions"]
        mine = next(s for s in listed if s["id"] == session)
        self.assertEqual(mine["title"], "")

    def test_commands_endpoint_lists_palette(self):
        client = self.client([])
        self.assertEqual(client.get("/api/commands").status_code, 401)
        commands = client.get("/api/commands", headers=AUTH).json()["commands"]
        self.assertEqual([c["name"] for c in commands], ["new", "stop", "delete", "title"])
        title = next(c for c in commands if c["name"] == "title")
        self.assertTrue(title["takes_arg"])
        self.assertFalse(next(c for c in commands if c["name"] == "new")["takes_arg"])

    def test_rename_overrides_derived_title(self):
        client = self.client([reply(types.Part(text="Answer."))])
        session = client.post("/api/sessions", headers=AUTH).json()["id"]
        client.post("/api/chat", headers=AUTH, json={"session_id": session, "text": "hello there"})
        renamed = client.patch(f"/api/sessions/{session}", headers=AUTH,
                               json={"title": "  my   name  "})
        self.assertEqual(renamed.status_code, 200)
        self.assertEqual(renamed.json()["title"], "my name")
        listed = client.get("/api/sessions", headers=AUTH).json()["sessions"]
        mine = next(s for s in listed if s["id"] == session)
        self.assertEqual(mine["title"], "my name")
        # the rename event carries no parts, so the history is unchanged
        items = client.get(f"/api/sessions/{session}/messages", headers=AUTH).json()["items"]
        self.assertEqual([i["kind"] for i in items], ["text", "text"])

    def test_rename_rejects_unknown_session_and_empty_title(self):
        client = self.client([])
        session = client.post("/api/sessions", headers=AUTH).json()["id"]
        unknown = client.patch("/api/sessions/missing", headers=AUTH, json={"title": "x"})
        self.assertEqual(unknown.status_code, 404)
        empty = client.patch(f"/api/sessions/{session}", headers=AUTH, json={"title": "   "})
        self.assertEqual(empty.status_code, 422)

    def test_chat_still_streams_after_rename(self):
        # The rename leaves a content-less event in the history; the runner
        # must tolerate it on the next turn.
        client = self.client([reply(types.Part(text="Still fine."))])
        session = client.post("/api/sessions", headers=AUTH).json()["id"]
        client.patch(f"/api/sessions/{session}", headers=AUTH, json={"title": "renamed"})
        response = client.post("/api/chat", headers=AUTH, json={"session_id": session, "text": "hi"})
        self.assertEqual(response.status_code, 200)
        events = sse_events(response)
        self.assertEqual(events[-1]["type"], "done")
        text = "".join(e.get("text", "") for e in events if e["type"] in ("delta", "replace"))
        self.assertIn("Still fine.", text)

    def test_chat_rejects_unknown_session_and_empty_text(self):
        client = self.client([])
        unknown = client.post("/api/chat", headers=AUTH, json={"session_id": "missing", "text": "hi"})
        self.assertEqual(unknown.status_code, 404)
        empty = client.post("/api/chat", headers=AUTH, json={"session_id": "missing", "text": "  "})
        self.assertEqual(empty.status_code, 422)

    def test_chat_streams_tool_call_result_and_text(self):
        client = self.client([
            tool_call(unit_price="19.99", quantity=3, tax_percent="8.25"),
            reply(types.Part(text="Your quote totals USD 64.92.")),
        ])
        session = client.post("/api/sessions", headers=AUTH).json()["id"]
        response = client.post(
            "/api/chat", headers=AUTH,
            json={"session_id": session, "text": "Quote 3 items at $19.99 plus 8.25% tax"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.headers["content-type"].startswith("text/event-stream"))

        events = sse_events(response)
        self.assertEqual(events[-1]["type"], "done")
        calls = [e for e in events if e["type"] == "tool" and e["phase"] == "call"]
        self.assertEqual(calls[0]["name"], "calculate_quote")
        self.assertEqual(calls[0]["args"], {"unit_price": "19.99", "quantity": 3, "tax_percent": "8.25"})
        results = [e for e in events if e["type"] == "tool" and e["phase"] == "result"]
        self.assertEqual(results[0]["response"]["total"], "64.92")
        deltas = "".join(e["text"] for e in events if e["type"] == "delta")
        replaces = [e["text"] for e in events if e["type"] == "replace"]
        self.assertIn("64.92", (replaces[-1] if replaces else deltas) or "")

        items = client.get(f"/api/sessions/{session}/messages", headers=AUTH).json()["items"]
        texts = [i["text"] for i in items if i["kind"] == "text"]
        self.assertTrue(any("19.99" in t for t in texts))  # the user turn persists
        self.assertTrue(any("64.92" in t for t in texts))  # so does the model answer
        self.assertTrue(any(i["kind"] == "call" for i in items))
        self.assertTrue(any(i["kind"] == "response" for i in items))


if __name__ == "__main__":
    unittest.main()
