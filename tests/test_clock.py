import os
import socket
import time
import unittest
from datetime import datetime
from unittest.mock import patch
from zoneinfo import ZoneInfo

from google.adk.models import BaseLlm
from google.adk.models.llm_response import LlmResponse
from google.adk.runners import InMemoryRunner
from google.genai import types

from hello_world.agent import root_agent
from hello_world.clock import get_datetime

# google_search in the agent's toolset rejects non-Gemini model ids at
# request time; scripted offline models must bypass that check.
os.environ.setdefault("ADK_DISABLE_GEMINI_MODEL_ID_CHECK", "1")


class ScriptedModel(BaseLlm):
    model: str = "offline-test"
    replies: list[types.Content]

    async def generate_content_async(self, llm_request, stream=False):
        yield LlmResponse(content=self.replies.pop(0))


def reply(*parts):
    return types.Content(role="model", parts=list(parts))


def responses(events):
    return [
        part.function_response.response
        for event in events
        if event.content
        for part in event.content.parts or []
        if part.function_response
    ]


class ClockBoundaryTests(unittest.TestCase):
    def setUp(self):
        network = patch.object(socket.socket, "connect", side_effect=AssertionError("Offline tests forbid network"))
        network.start()
        self.addCleanup(network.stop)
        env = patch.dict(os.environ, {"APP_TIMEZONE": "America/New_York"})
        env.start()
        self.addCleanup(env.stop)

    def test_explicit_timezone_returns_consistent_fields(self):
        result = get_datetime("America/New_York")
        self.assertNotIn("error", result)
        now = datetime.now(ZoneInfo("America/New_York"))
        self.assertEqual(result["date"], now.strftime("%Y-%m-%d"))
        self.assertEqual(result["weekday"], now.strftime("%A"))
        self.assertEqual(result["time"], now.strftime("%H:%M:%S"))
        self.assertEqual(result["iso"], now.isoformat(timespec="seconds"))
        self.assertEqual(result["timezone"], "America/New_York")
        self.assertLess(abs(result["unix"] - time.time()), 5)

    def test_empty_timezone_uses_the_configured_default(self):
        self.assertEqual(get_datetime()["timezone"], "America/New_York")

    def test_unconfigured_default_falls_back_to_utc(self):
        os.environ.pop("APP_TIMEZONE")
        self.assertEqual(get_datetime()["timezone"], "UTC")

    def test_invalid_timezone_returns_an_actionable_error(self):
        result = get_datetime("Not/A_Zone")
        self.assertEqual(result, {"error": "Unknown timezone 'Not/A_Zone'; use an IANA name such as America/New_York."})


class ClockRunnerTests(unittest.TestCase):
    def setUp(self):
        network = patch.object(socket.socket, "connect", side_effect=AssertionError("Offline tests forbid network"))
        network.start()
        self.addCleanup(network.stop)
        env = patch.dict(os.environ, {"APP_TIMEZONE": "America/New_York"})
        env.start()
        self.addCleanup(env.stop)

    async def test_chat_anchors_dates_with_the_tool(self):
        agent = root_agent.model_copy(update={"model": ScriptedModel(replies=[
            reply(types.Part.from_function_call(name="get_datetime", args={})),
            reply(types.Part(text="It is Wednesday, November 11, 2026, in America/New_York.")),
        ])})
        runner = InMemoryRunner(agent=agent, app_name="hello_world")
        self.addAsyncCleanup(runner.close)
        session = await runner.session_service.create_session(app_name="hello_world", user_id="test")
        events = [
            event
            async for event in runner.run_async(
                user_id="test", session_id=session.id,
                new_message=types.Content(role="user", parts=[types.Part(text="What day is it?")]),
            )
        ]
        self.assertEqual(len(responses(events)), 1)
        tool_result = responses(events)[0]
        self.assertNotIn("error", tool_result)
        self.assertEqual(tool_result["timezone"], "America/New_York")
        self.assertLess(abs(tool_result["unix"] - time.time()), 5)
        self.assertTrue(any(event.is_final_response() and event.content for event in events))


if __name__ == "__main__":
    unittest.main()
