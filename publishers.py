import asyncio
import zmq
from agent_framework import Agent
from settings import llm_client, zmq_context


async def quote_service():
    """Generates data and publishes it to the ZMQ socket."""
    # 1. Setup ZMQ PUB socket
    socket = zmq_context.socket(zmq.PUB)
    socket.bind("tcp://localhost:5555")

    # 2. Setup the Agent
    generator = Agent(
        client=llm_client,
        name="QuoteGenerator",
        instructions=(
            "You are a quote generator that provides random quotes of the day. Only respond with the quote text, no formatting or additional information."
        ),
    )

    print("[QuoteService] Bound to tcp://localhost:5555. Starting broadcast...")

    # Allow subscribers a moment to connect before blasting messages
    await asyncio.sleep(1)

    while True:
        # Ask the agent to generate new fake data
        response = await generator.run("Give a random quote of the day.")
        payload = response.text

        # 3. Publish the message with a topic
        topic = b"QUOTE"
        message = payload.encode("utf-8")

        # ZeroMQ multipart sends: [Topic, Message]
        await socket.send_multipart([topic, message])
        print(f"📡 [QuoteService] Sent: {payload}")

        # Wait 8 seconds before sending the next reading
        await asyncio.sleep(8)


async def lyric_publisher_service():
    """Generates song lyrics and publishes them to the ZMQ socket."""
    # 1. Setup ZMQ PUB socket on a NEW port
    socket = zmq_context.socket(zmq.PUB)
    socket.bind("tcp://*:5556")

    # 2. Setup the Agent
    lyric_agent = Agent(
        client=llm_client,
        name="LyricGenerator",
        instructions=(
            "You are a creative songwriter. Every time you are called, output "
            "exactly one line of a song. Do not include labels like 'Chorus:'. "
            "Just output the raw lyric text."
        ),
    )

    print("[LyricPublisher] Bound to tcp://*:5556. Starting broadcast...")
    await asyncio.sleep(1)

    while True:
        response = await lyric_agent.run("Give me the next line.")
        payload = response.text

        # 3. Publish the message with the SONG topic
        topic = b"SONG"
        message = payload.encode("utf-8")

        await socket.send_multipart([topic, message])
        print(f"🎵 [LyricPublisher] Sent: {payload}")

        # Publish at a slightly different interval to see the asynchronous concurrency
        await asyncio.sleep(8)
