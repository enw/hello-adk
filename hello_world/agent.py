from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
from google.adk.tools.google_search_tool import GoogleSearchTool
from google.genai import types

from .clock import get_datetime
from .quotes import calculate_quote
from .preferences import session_preferences

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
        "For anything about today, now, the current date, time, or weekday, "
        "call get_datetime first and answer from its result, mentioning its "
        "timezone; never guess dates. "
        "For current events, news, or facts beyond your knowledge, search "
        "the web and answer from the results, citing sources. "
        "For quotes, always use calculate_quote instead of doing arithmetic yourself. "
        "Pass prices and tax percentages as decimal strings. Only USD is supported. "
        "Ask for missing price or quantity; tax defaults to zero. "
        "Report subtotal, tax, total, and currency from the tool result. "
        "A quote is read-only, never a purchase. Explain tool errors without inventing totals. "
        "Do not call the calculator for ordinary conversation. "
        "Use session_preferences to get, set, or clear response style when requested. "
        "Only concise and standard are supported, for this conversation only. "
        "Effective session response style: {response_style?}. Missing means standard. "
        "Use this current state, not outdated preferences in the transcript. "
        "In concise mode use at most two sentences when practical, without omitting "
        "required quote amounts or important errors. Standard mode uses normal detail."
    ),
    tools=[calculate_quote, session_preferences, get_datetime,
           GoogleSearchTool(bypass_multi_tools_limit=True)],
)
