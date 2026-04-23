import asyncio
import random
from agent_framework import Agent, tool
from agent_framework.openai import OpenAIChatCompletionClient


# 1. Define the Tool
@tool
def get_random_word_count() -> str:
    """Returns a random integer to determine how many words the sentence should have."""
    print("\n⚠️  [HITL Alert] Agent wants to use 'get_random_word_count'.")
    choice = input("Approve | Deny (y/n): ").strip().lower()

    if choice in ["y", "yes", "approve"]:
        count = random.randint(4, 12)
        print(f"✅ [Tool Execution] get_random_word_count returned: {count}")
        return str(count)
    else:
        print("❌ [Tool Execution] Access Denied by user.")
        return "System Error: The user denied permission to execute this tool. Apologize and ask for manual instructions."


async def main():
    client = OpenAIChatCompletionClient(model="gpt-4o-mini")

    # 2. Define the Agent with Strict Instructions
    sentence_agent = Agent(
        client=client,
        name="WordCountAgent",
        instructions=(
            "You are a precise sentence generator. When asked for a random sentence, "
            "you MUST first call the 'get_random_word_count' tool. "
            "Once the tool returns a number, you must generate a sentence containing "
            "EXACTLY that many words. Punctuation does not count as a word. "
            "Format your final output as: 'Word Count: [N] | Sentence: [Your sentence]'"
        ),
        tools=[get_random_word_count],
    )

    session = sentence_agent.create_session()

    while True:
        # 3. Execute the Request
        user_prompt = input("👤 User: ")

        # The agent will automatically pause, run the tool, read the result, and then reply
        response = await sentence_agent.run(user_prompt, session=session)

        print(f"\n🤖 {sentence_agent.name}: {response.text}")


if __name__ == "__main__":
    asyncio.run(main())
