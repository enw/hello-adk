import os
import socket
import unittest
from unittest.mock import patch

from google.adk.models import BaseLlm
from google.adk.models.llm_response import LlmResponse
from google.adk.runners import InMemoryRunner
from google.genai import types

from hello_world.agent import root_agent
from hello_world.quotes import calculate_quote

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


def tool_call(**arguments):
    return reply(types.Part.from_function_call(name="calculate_quote", args=arguments))


def responses(events):
    return [
        part.function_response.response
        for event in events
        if event.content
        for part in event.content.parts or []
        if part.function_response
    ]


class QuoteBoundaryTests(unittest.TestCase):
    def setUp(self):
        network = patch.object(socket.socket, "connect", side_effect=AssertionError("Offline tests forbid network"))
        network.start()
        self.addCleanup(network.stop)

    def test_rounding_defaults_and_tax_limits(self):
        for arguments, expected in [
            ({"unit_price": "0.335", "quantity": 3}, ("1.01", "0.00", "1.01")),
            ({"unit_price": "0.05", "quantity": 1, "tax_percent": "10"}, ("0.05", "0.01", "0.06")),
            ({"unit_price": "0", "quantity": 2, "tax_percent": "100"}, ("0.00", "0.00", "0.00")),
            ({"unit_price": "5", "quantity": 2, "tax_percent": "100"}, ("10.00", "10.00", "20.00")),
        ]:
            with self.subTest(arguments=arguments):
                result = calculate_quote(**arguments)
                self.assertEqual(tuple(result[key] for key in ("subtotal", "tax", "total")), expected)
                self.assertEqual(result["currency"], "USD")

    def test_invalid_arguments_return_errors_not_totals(self):
        for arguments in [
            {"unit_price": "-1"}, {"unit_price": "NaN"},
            {"unit_price": "Infinity"}, {"unit_price": "oops"},
            {"unit_price": None}, {"quantity": 0}, {"quantity": -1},
            {"quantity": 1.5}, {"quantity": True}, {"quantity": "3"},
            {"tax_percent": "-1"}, {"tax_percent": "101"},
            {"tax_percent": "NaN"}, {"tax_percent": "Infinity"},
            {"tax_percent": "oops"}, {"currency": "EUR"},
            {"unit_price": "1e999999"},
        ]:
            with self.subTest(arguments=arguments):
                result = calculate_quote(**({"unit_price": "19.99", "quantity": 3} | arguments))
                self.assertTrue(result.get("error"))
                self.assertNotIn("total", result)


class AgentQuoteTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.network = patch.object(
            socket.socket, "connect", side_effect=AssertionError("Offline tests forbid network")
        )
        self.network.start()
        self.addCleanup(self.network.stop)

    async def start_chat(self, replies):
        agent = root_agent.model_copy(update={"model": ScriptedModel(replies=replies)})
        runner = InMemoryRunner(agent=agent, app_name="hello_world")
        self.addAsyncCleanup(runner.close)
        session = await runner.session_service.create_session(
            app_name="hello_world", user_id="test"
        )
        return runner, session.id

    async def turn(self, runner, session_id, text):
        return [
            event
            async for event in runner.run_async(
                user_id="test", session_id=session_id,
                new_message=types.Content(role="user", parts=[types.Part(text=text)]),
            )
        ]

    async def test_greeting_needs_no_tool(self):
        runner, session = await self.start_chat([reply(types.Part(text="Hello!"))])
        events = await self.turn(runner, session, "Hello")
        self.assertEqual(responses(events), [])
        self.assertTrue(any(event.is_final_response() and event.content for event in events))

    async def test_invalid_quote_then_chat_in_same_session(self):
        runner, session = await self.start_chat([
            tool_call(unit_price="19.99", quantity=0),
            reply(types.Part(text="Please provide a positive integer quantity.")),
            reply(types.Part(text="Hello!")),
        ])
        failed = await self.turn(runner, session, "Quote zero items at $19.99")
        self.assertEqual(responses(failed), [{"error": "Quantity must be a positive integer."}])
        self.assertTrue(any(event.is_final_response() for event in failed))
        recovered = await self.turn(runner, session, "Hello")
        self.assertEqual(responses(recovered), [])
        self.assertTrue(any(event.is_final_response() and event.content for event in recovered))

    async def test_chat_calculates_a_taxed_quote(self):
        runner, session = await self.start_chat([
            tool_call(unit_price="19.99", quantity=3, tax_percent="8.25"),
            reply(types.Part(text="Your quote totals USD 64.92.")),
        ])
        events = await self.turn(runner, session, "Quote 3 items at $19.99 plus 8.25% tax")
        self.assertEqual(responses(events), [{
            "subtotal": "59.97", "tax": "4.95", "total": "64.92", "currency": "USD",
        }])
        self.assertTrue(any(event.is_final_response() and event.content for event in events))
