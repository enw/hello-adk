from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
from google.genai import types

from .quotes import calculate_quote

root_agent = Agent(
    name="hello_world",
    model=Gemini(
        model="gemini-3.5-flash-lite",
        client_kwargs={"http_options": types.HttpOptions(timeout=15000)},
        retry_options=types.HttpRetryOptions(attempts=2, initial_delay=1),
    ),
    description="A friendly hello-world agent.",
    instruction=(
        "Greet the user warmly. Answer questions clearly and concisely. "
        "For quotes, always use calculate_quote instead of doing arithmetic yourself. "
        "Pass prices and tax percentages as decimal strings. Only USD is supported. "
        "Ask for missing price or quantity; tax defaults to zero. "
        "Report subtotal, tax, total, and currency from the tool result. "
        "A quote is read-only, never a purchase. Explain tool errors without inventing totals. "
        "Do not call the calculator for ordinary conversation."
    ),
    tools=[calculate_quote],
)
