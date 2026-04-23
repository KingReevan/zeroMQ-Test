from settings import zmq_context
import asyncio
import sys
from subscribers import (
    quote_comedy_service,
    quote_explainer_service,
    song_guesser_service,
)
from publishers import lyric_publisher_service, quote_service

# Add this Windows-specific fix:
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


async def main():
    print("Starting ZeroMQ Agent Network...\n")

    # Run publisher and both subscribers simultaneously
    await asyncio.gather(
        quote_comedy_service(),
        quote_explainer_service(),
        quote_service(),
        lyric_publisher_service(),
        song_guesser_service(),
    )


if __name__ == "__main__":
    # Handle graceful shutdown on Ctrl+C
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutting down ZMQ context...")
        zmq_context.term()
