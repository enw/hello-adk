"""Explicitly opt-in verification of a real agent/tool round trip."""

import argparse
import asyncio
import os
from pathlib import Path
import sys

from dotenv import load_dotenv
from google.adk.agents.run_config import RunConfig
from google.adk.runners import InMemoryRunner
from google.genai import types

from .agent import root_agent


async def check_quote():
    runner = InMemoryRunner(agent=root_agent, app_name="hello_world")
    try:
        async with asyncio.timeout(45):
            session = await runner.session_service.create_session(
                app_name="hello_world", user_id="smoke_test"
            )
            called = False
            calculated = False
            final_text = ""
            async for event in runner.run_async(
                user_id="smoke_test",
                session_id=session.id,
                new_message=types.Content(role="user", parts=[types.Part(text=(
                    "What is the total for 3 items at $19.99 each with 8.25% sales tax? "
                    "Use the quote tool and show subtotal, tax, total, and currency."
                ))]),
                run_config=RunConfig(max_llm_calls=4),
            ):
                if event.error_code:
                    raise RuntimeError(f"{event.error_code}: {event.error_message}")
                for part in event.content.parts if event.content else []:
                    if part.function_call and part.function_call.name == "calculate_quote":
                        called = True
                    if part.function_response and part.function_response.name == "calculate_quote":
                        calculated = part.function_response.response == {
                            "subtotal": "59.97", "tax": "4.95", "total": "64.92", "currency": "USD",
                        }
                if event.is_final_response() and event.content:
                    final_text = "".join(part.text or "" for part in event.content.parts)
            if not called or not calculated or not all(
                amount in final_text for amount in ("59.97", "4.95", "64.92")
            ):
                raise RuntimeError("Incomplete verification: need tool call, correct result, and final quote text.")
            print(f"PASS: {root_agent.model.model}; real tool invocation and correct quote verified.")
            print(final_text)
    finally:
        await runner.close()


def main():
    parser = argparse.ArgumentParser(description="Live quote smoke check; may incur API charges.")
    parser.add_argument("--live", action="store_true", help="Opt in to paid provider requests")
    args = parser.parse_args()
    if not args.live:
        parser.error("Pass --live to opt in; this check may incur API charges.")
    load_dotenv(Path(__file__).with_name(".env"))
    key = os.getenv("GOOGLE_API_KEY")
    if not key or key == "your-google-ai-studio-api-key":
        parser.error("Set GOOGLE_API_KEY in the environment or hello_world/.env before live verification.")
    try:
        asyncio.run(check_quote())
    except Exception as error:
        print(f"FAIL: {type(error).__name__}: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
