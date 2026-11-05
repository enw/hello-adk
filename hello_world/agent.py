from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
from google.genai import types

root_agent = Agent(
    name="hello_world",
    model=Gemini(
        model="gemini-3.5-flash-lite",
        client_kwargs={"http_options": types.HttpOptions(timeout=15000)},
        retry_options=types.HttpRetryOptions(attempts=2, initial_delay=1),
    ),
    description="A friendly hello-world agent.",
    instruction="Greet the user warmly. Answer questions clearly and concisely.",
)
