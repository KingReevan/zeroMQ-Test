import asyncio
import zmq
from agent_framework import Agent
from settings import llm_client, zmq_context


async def quote_comedy_service():
    """Listens to telemetry and formats it."""
    # 1. Setup ZMQ SUB socket
    socket = zmq_context.socket(zmq.SUB)
    socket.connect("tcp://localhost:5555")
    # Subscribe specifically to the QUOTE topic
    socket.setsockopt(zmq.SUBSCRIBE, b"QUOTE")

    comedy_agent = Agent(
        client=llm_client,
        name="QuoteComedian",
        instructions="You are a comedian who takes a quote and adds a funny twist to it. Only respond with the joke, no formatting or additional information.",
    )

    print("[QuoteComedian] Subscribed to QUOTE.")

    while True:
        # 2. Wait for messages asynchronously
        topic, message = await socket.recv_multipart()
        raw_data = message.decode("utf-8")

        # Process with the agent
        response = await comedy_agent.run(f"Make a joke about this quote: {raw_data}")
        print(f"🤣 [QuoteComedian] {response.text}")


async def quote_explainer_service():
    """Listens to quotes and explains them."""
    socket = zmq_context.socket(zmq.SUB)
    socket.connect("tcp://localhost:5555")
    socket.setsockopt(zmq.SUBSCRIBE, b"QUOTE")

    explainer_agent = Agent(
        client=llm_client,
        name="QuoteExplainer",
        instructions=(
            "You are a helpful assistant who can explain the meaning behind quotes. Only respond with the explanation, no formatting or additional information."
        ),
    )

    print("[QuoteExplainer] Subscribed to QUOTE.")

    while True:
        topic, message = await socket.recv_multipart()
        raw_data = message.decode("utf-8")

        response = await explainer_agent.run(
            f"Explain the meaning of this quote: {raw_data}"
        )
        print(f"🧐 [QuoteExplainer] {response.text}")


async def song_guesser_service():
    """Listens to telemetry and lyrics, then formats them."""
    socket = zmq_context.socket(zmq.SUB)

    try:
        socket.connect("tcp://localhost:5555")  # Quote port
        socket.connect("tcp://localhost:5556")  # Lyric port
        # Subscribe to BOTH topics
        socket.setsockopt(zmq.SUBSCRIBE, b"SONG")
    except Exception as e:
        print(f"Error connecting to ZMQ sockets: {e}")

    logger_agent = Agent(
        client=llm_client,
        name="SongGuesser",
        instructions="Guess the song based on the lyrics.",
    )

    print("[SongGuesser] Subscribed to SONG.")

    while True:
        topic_bytes, message = await socket.recv_multipart()
        topic_str = topic_bytes.decode("utf-8")
        raw_data = message.decode("utf-8")

        # You can use the topic to change how you handle the data before giving it to the agent
        prompt = f"Topic: {topic_str} | Data: {raw_data}"
        response = await logger_agent.run(prompt)
        print(f"📝 [SongGuesser] {response.text}")
