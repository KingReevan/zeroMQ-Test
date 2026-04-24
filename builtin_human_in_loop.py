import asyncio
import random
from agent_framework import Agent, tool, FunctionInvocationContext, function_middleware
from settings import llm_client as client


# 1. The Tool is now 100% pure business logic.
@tool
def get_random_word_count() -> str:
    """Returns a random integer to determine how many words the sentence should have."""
    count = random.randint(4, 12)
    return str(count)


# 2. Use FUNCTION Middleware to intercept the exact moment a tool is called
@function_middleware
async def tool_approval_guard(context: FunctionInvocationContext, call_next):
    """Intercepts the tool execution after the LLM requests it."""

    print(
        f"\n⚠️  [Framework HITL] Agent is attempting to use tool: '{context.function.name}'."
    )
    choice = input("Approve | Deny (y/n): ").strip().lower()

    if choice not in ["y", "yes", "approve"]:
        print("❌ [Framework HITL] Execution Denied.")
        # We short-circuit the execution by overriding the result manually
        # and we DO NOT call call_next()
        context.result = "System Error: The user denied permission to execute this tool. Apologize and ask for manual instructions."
        return

    print("✅ [Framework HITL] Execution Approved.")
    # If approved, yield control back to actually execute the tool
    await call_next()


async def main():

    # 3. Attach the middleware to the Agent
    sentence_agent = Agent(
        client=client,
        name="WordCountAgent",
        instructions=(
            "You are a precise sentence generator. When asked for a random sentence, "
            "you MUST first call the 'get_random_word_count' tool. "
            "Once the tool returns a number, you must generate a sentence containing "
            "EXACTLY that many words. Punctuation does not count as a word. "
            "Format your final output as: 'Word Count: [N] | Sentence: [Your sentence]'. "
            "If the tool execution is denied, apologize and ask the user for a manual word count."
        ),
        tools=[get_random_word_count],
        middleware=[
            tool_approval_guard
        ],  # <--- The built-in interceptor is attached here!
    )

    # Creating the session synchronously (as we discovered earlier!)
    session = sentence_agent.create_session()

    while True:
        # 4. Execute the Request
        user_prompt = input("\n👤 User: ")

        if user_prompt.lower() in ["quit", "exit"]:
            break

        try:
            # The middleware will automatically pause execution when a tool is detected
            response = await sentence_agent.run(user_prompt, session=session)
            print(f"\n🤖 {sentence_agent.name}: {response.text}")
        except PermissionError as e:
            print(f"\n🤖 {sentence_agent.name}: Execution stopped. {e}")


if __name__ == "__main__":
    asyncio.run(main())
