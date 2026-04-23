import asyncio
import zmq
from zmq.asyncio import Context
from agent_framework.openai import OpenAIChatCompletionClient

llm_client = OpenAIChatCompletionClient(model="gpt-4o-mini")

# We use a single shared ZMQ context for the application
zmq_context = Context()
