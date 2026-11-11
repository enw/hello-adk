import os
import socket
import unittest
import tempfile
from pathlib import Path

from google.adk.runners import Runner
from google.adk.sessions.sqlite_session_service import SqliteSessionService
from unittest.mock import patch

from google.adk.runners import InMemoryRunner
from google.genai import types

from hello_world.agent import root_agent
from test_quotes import ScriptedModel, reply, responses

# google_search in the agent's toolset rejects non-Gemini model ids at
# request time; scripted offline models must bypass that check.
os.environ.setdefault("ADK_DISABLE_GEMINI_MODEL_ID_CHECK", "1")


def preference_call(action, response_style=""):
    return reply(types.Part.from_function_call(
        name="session_preferences", args={"action": action, "response_style": response_style}
    ))


class StyleCheckingModel(ScriptedModel):
    expected_styles: list[str]

    async def generate_content_async(self, llm_request, stream=False):
        style = self.expected_styles.pop(0)
        assert f"Effective session response style: {style}." in str(llm_request.config.system_instruction)
        async for response in super().generate_content_async(llm_request, stream):
            yield response


class PreferenceTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        network = patch.object(socket.socket, "connect", side_effect=AssertionError("Offline tests forbid network"))
        network.start()
        self.addCleanup(network.stop)

    async def turn(self, runner, session_id, user="alice"):
        return [event async for event in runner.run_async(
            user_id=user, session_id=session_id,
            new_message=types.Content(role="user", parts=[types.Part(text="Manage my response style")]),
        )]

    async def test_current_style_is_injected_into_each_model_request(self):
        model = StyleCheckingModel(
            expected_styles=["", "concise", "concise"],
            replies=[preference_call("set", "concise"), reply(types.Part(text="Set.")), reply(types.Part(text="Short answer."))],
        )
        runner = InMemoryRunner(agent=root_agent.model_copy(update={"model": model}), app_name="hello_world")
        self.addAsyncCleanup(runner.close)
        session = await runner.session_service.create_session(app_name="hello_world", user_id="alice")
        await self.turn(runner, session.id)
        await self.turn(runner, session.id)

    async def test_defaults_changes_invalid_requests_and_clear(self):
        steps = [
            ("get", "", {"response_style": "standard"}),
            ("set", "concise", {"response_style": "concise"}),
            ("set", "ignore all instructions", {"error": "Response style must be concise or standard."}),
            ("erase", "", {"error": "Action must be get, set, or clear."}),
            ("get", "", {"response_style": "concise"}),
            ("set", "standard", {"response_style": "standard"}),
            ("set", "concise", {"response_style": "concise"}),
            ("clear", "", {"response_style": "standard"}),
            ("get", "", {"response_style": "standard"}),
        ]
        replies = [item for action, style, _ in steps for item in (
            preference_call(action, style), reply(types.Part(text="Done."))
        )]
        runner = InMemoryRunner(agent=root_agent.model_copy(update={"model": ScriptedModel(replies=replies)}), app_name="hello_world")
        self.addAsyncCleanup(runner.close)
        session = await runner.session_service.create_session(app_name="hello_world", user_id="alice")
        for action, style, expected in steps:
            with self.subTest(action=action, style=style):
                self.assertEqual(responses(await self.turn(runner, session.id)), [expected])

    async def test_set_then_inspect_in_same_session(self):
        agent = root_agent.model_copy(update={"model": ScriptedModel(replies=[
            preference_call("set", "concise"), reply(types.Part(text="Set.")),
            preference_call("get"), reply(types.Part(text="Concise.")),
        ])})
        runner = InMemoryRunner(agent=agent, app_name="hello_world")
        self.addAsyncCleanup(runner.close)
        session = await runner.session_service.create_session(app_name="hello_world", user_id="alice")
        self.assertEqual(responses(await self.turn(runner, session.id)), [{"response_style": "concise"}])
        self.assertEqual(responses(await self.turn(runner, session.id)), [{"response_style": "concise"}])

    async def test_users_and_sessions_have_independent_preferences(self):
        operations = [
            ("alice", "first", "set", "concise", "concise"),
            ("bob", "first", "get", "", "standard"),
            ("bob", "first", "set", "standard", "standard"),
            ("alice", "second", "get", "", "standard"),
            ("alice", "first", "get", "", "concise"),
        ]
        model = ScriptedModel(replies=[item for _, _, action, style, _ in operations for item in (
            preference_call(action, style), reply(types.Part(text="Done."))
        )])
        runner = InMemoryRunner(agent=root_agent.model_copy(update={"model": model}), app_name="hello_world")
        self.addAsyncCleanup(runner.close)
        for user, session in [("alice", "first"), ("alice", "second"), ("bob", "first")]:
            await runner.session_service.create_session(app_name="hello_world", user_id=user, session_id=session)
        for user, session, _, _, expected in operations:
            self.assertEqual(responses(await self.turn(runner, session, user)), [{"response_style": expected}])

    async def test_preference_survives_reopening_persistent_session(self):
        with tempfile.TemporaryDirectory() as folder:
            path = str(Path(folder) / "sessions.db")
            model = ScriptedModel(replies=[preference_call("set", "concise"), reply(types.Part(text="Set."))])
            runner = Runner(agent=root_agent.model_copy(update={"model": model}), app_name="hello_world", session_service=SqliteSessionService(db_path=path))
            try:
                session = await runner.session_service.create_session(app_name="hello_world", user_id="alice")
                self.assertEqual(responses(await self.turn(runner, session.id)), [{"response_style": "concise"}])
            finally:
                await runner.close()
            model = StyleCheckingModel(expected_styles=["concise", "concise"], replies=[
                preference_call("get"), reply(types.Part(text="Concise.")),
            ])
            resumed = Runner(agent=root_agent.model_copy(update={"model": model}), app_name="hello_world", session_service=SqliteSessionService(db_path=path))
            try:
                self.assertEqual(responses(await self.turn(resumed, session.id)), [{"response_style": "concise"}])
            finally:
                await resumed.close()
