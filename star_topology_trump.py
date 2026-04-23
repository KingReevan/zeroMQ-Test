import asyncio
import sys
import json
import zmq
from zmq.asyncio import Context
from agent_framework import Agent
from agent_framework.openai import OpenAIChatCompletionClient

# Windows compatibility for ZeroMQ
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

ctx = Context()
client = OpenAIChatCompletionClient(model="gpt-4o-mini")


# ==========================================
# 1. THE HUB SERVICE
# ==========================================
async def hub_service():
    """Routes traffic between all connected DEALER sockets."""
    hub = ctx.socket(zmq.ROUTER)
    hub.bind("tcp://*:8000")

    print("🌟 Hub Service is online on port 8000...")

    while True:
        # Hub receives: [Sender_ID, Target_ID, Payload]
        frames = await hub.recv_multipart()
        if len(frames) != 3:
            continue

        sender_id, target_id, payload = frames
        print(f"   [HUB] Routing {sender_id.decode()} -> {target_id.decode()}")

        # Hub forwards: [Target_ID, Sender_ID, Payload]
        await hub.send_multipart([target_id, sender_id, payload])


# ==========================================
# 2. THE PUBLISHER: DONALD TRUMP SERVICE
# ==========================================
async def donald_trump_service():
    """Generates tweets and sends them to the citizens."""
    worker = ctx.socket(zmq.DEALER)
    worker.setsockopt(zmq.IDENTITY, b"DonaldTrump")
    worker.connect("tcp://localhost:8000")

    trump_agent = Agent(
        client=client,
        name="Trump",
        instructions=(
            "You are Donald Trump. Write a very short, single-sentence tweet about a random topic. "
            "Do not use hashtags. Because you have memory, NEVER repeat a topic you have already tweeted about."
        ),
    )

    # Give the agent memory so it doesn't repeat tweets
    session = trump_agent.create_session()

    await asyncio.sleep(2)  # Wait for all services to connect
    print("🦅 [Trump] Connected to Hub. Ready to tweet.")

    while True:
        # Generate the tweet using the session memory
        response = await trump_agent.run("Write a new tweet.", session=session)
        tweet = response.text
        print(f"\n📱 [Trump Tweets]: {tweet}")

        # Create the payload
        payload = json.dumps({"tweet": tweet}).encode("utf-8")

        # Send the exact same message to both citizens
        # Envelope: [Destination_ID, Payload]
        await worker.send_multipart([b"CitizenOne", payload])
        await worker.send_multipart([b"CitizenTwo", payload])

        # Wait 10 seconds before the next tweet to avoid rate limits
        await asyncio.sleep(10)


# ==========================================
# 3. SUBSCRIBER 1: CITIZEN ONE
# ==========================================
async def citizen_one_service():
    """An enthusiastic supporter reacting to tweets."""
    worker = ctx.socket(zmq.DEALER)
    worker.setsockopt(zmq.IDENTITY, b"CitizenOne")
    worker.connect("tcp://localhost:8000")

    citizen_agent = Agent(
        client=client,
        name="Supporter",
        instructions="You are an enthusiastic supporter. React to the provided tweet in one short sentence.",
    )

    print("🧢 [Citizen 1] Online and listening.")

    while True:
        # Receives: [Sender_ID, Payload]
        sender_id, payload = await worker.recv_multipart()
        data = json.loads(payload.decode("utf-8"))

        tweet = data.get("tweet")
        response = await citizen_agent.run(f"React to this tweet: {tweet}")

        print(f"   👍 [Citizen 1 Reacts]: {response.text}")


# ==========================================
# 4. SUBSCRIBER 2: CITIZEN TWO
# ==========================================
async def citizen_two_service():
    """A skeptical critic reacting to tweets."""
    worker = ctx.socket(zmq.DEALER)
    worker.setsockopt(zmq.IDENTITY, b"CitizenTwo")
    worker.connect("tcp://localhost:8000")

    citizen_agent = Agent(
        client=client,
        name="Critic",
        instructions="You are a skeptical critic. React to the provided tweet in one short sentence, questioning the claim.",
    )

    print("📰 [Citizen 2] Online and listening.")

    while True:
        sender_id, payload = await worker.recv_multipart()
        data = json.loads(payload.decode("utf-8"))

        tweet = data.get("tweet")
        response = await citizen_agent.run(f"React to this tweet: {tweet}")

        print(f"   🤨 [Citizen 2 Reacts]: {response.text}")


# ==========================================
# RUN THE INFRASTRUCTURE
# ==========================================
async def main():
    print("Starting the Political Twitter Simulation...\n")

    # Run all 4 services concurrently
    await asyncio.gather(
        hub_service(),
        citizen_one_service(),
        citizen_two_service(),
        donald_trump_service(),
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutting down simulation...")
        ctx.term()
