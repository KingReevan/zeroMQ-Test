import asyncio
from zmq.asyncio import Context
from agent_framework.openai import OpenAIChatCompletionClient
from agent_framework import Agent, chat_middleware, ChatContext


@chat_middleware
async def token_cost_logger(context: ChatContext, call_next):
    """Intercepts the raw network call to log token usage and calculate cost."""

    print("🌐 [Network] Transmitting payload to API...")

    # 1. Yield control to the execution pipeline (this returns None)
    await call_next()

    # 2. Extract the response from the shared context object
    response = context.result

    # Safety check to ensure usage metadata exists
    if hasattr(response, "usage_details") and response.usage_details is not None:
        in_tokens = response.usage_details["input_token_count"]
        out_tokens = response.usage_details["output_token_count"]
        total_tokens = response.usage_details["total_token_count"]

        # GPT-4o-mini pricing
        input_cost = (in_tokens / 1_000_000) * 0.150
        output_cost = (out_tokens / 1_000_000) * 0.600
        total_cost = input_cost + output_cost

        print(
            f"📊 [Token Usage] Input: {in_tokens} | Output: {out_tokens} | Total: {total_tokens}"
        )
        print(f"💸 [Estimated Cost] ${total_cost:.6f}")
    else:
        print("⚠️ [Network] No token usage data returned from the API.")

    # 3. No return statement! The framework automatically grabs context.result when the chain finishes.


async def main():
    # 2. Attach the middleware to the CLIENT (Not the Agent!)
    client = OpenAIChatCompletionClient(
        model="gpt-4o-mini",
        middleware=[token_cost_logger],  # <--- Network-level interceptor attached here
    )

    # 3. Create the Agent using the intercepted client
    agent = Agent(
        client=client,
        name="CostAwareAgent",
        instructions="You are a highly concise assistant. Limit answers to one sentence.",
    )

    user_prompt = "Explain how a ZeroMQ ROUTER socket works."
    print(f"👤 User: {user_prompt}\n")

    # 4. Run the Agent
    response = await agent.run(user_prompt)

    print(f"\n🤖 {agent.name}: {response.text}")


llm_client = OpenAIChatCompletionClient(
    model="gpt-4o-mini", middleware=[token_cost_logger]
)

# We use a single shared ZMQ context for the application
zmq_context = Context()

if __name__ == "__main__":
    asyncio.run(main())
