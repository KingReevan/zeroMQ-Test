import json
import zmq
from agent_framework import Agent
from settings import llm_client, zmq_context
import asyncio
import sys

# Add this Windows-specific fix:
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


async def foreign_citizen_service():
    """An foreign citizen reacting to tweets."""
    worker = zmq_context.socket(zmq.DEALER)
    worker.setsockopt(zmq.IDENTITY, b"ForeignCitizen")
    worker.connect("tcp://localhost:8000")  # Connect to the Hub's ROUTER socket

    citizen_agent = Agent(
        client=llm_client,
        name="ForeignCitizen",
        instructions="You are a foreign citizen. React to the provided tweet in one short sentence.",
    )

    print("🧢 [ForeignCitizen] Online and listening.")

    while True:
        # Receives: [Sender_ID, Payload]
        sender_id, payload = await worker.recv_multipart()
        data = json.loads(payload.decode("utf-8"))

        tweet = data.get("tweet")
        response = await citizen_agent.run(f"React to this tweet: {tweet}")

        print(f"   👍 [ForeignCitizen Reacts]: {response.text}")


async def main():
    print("Starting ZeroMQ Agent Network...\n")

    # Run publisher and both subscribers simultaneously
    await asyncio.gather(
        foreign_citizen_service(),
    )


if __name__ == "__main__":
    # Handle graceful shutdown on Ctrl+C
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutting down Foreign Citizen...")
        zmq_context.term()
