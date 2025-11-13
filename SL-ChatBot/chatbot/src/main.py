"""Chatbot Main Entry Point."""
import asyncio
from typing import Optional
from handler import ChatHandler


class QuantAdvisorBot:
    """Quant Investment Advisor Chatbot."""

    def __init__(self, config_path: str = "config.yaml"):
        self.handler = ChatHandler(config_path)

    async def chat(self, message: str, session_id: Optional[str] = None) -> dict:
        """Process user message and return response.

        Args:
            message: User input message
            session_id: Optional session ID for conversation history

        Returns:
            Response dictionary with answer and metadata
        """
        return await self.handler.handle(message, session_id)

    async def recommend_strategy(self, user_profile: dict) -> dict:
        """Recommend investment strategy based on user profile.

        Args:
            user_profile: User investment profile
                - risk_tolerance: low/medium/high
                - investment_horizon: short/medium/long
                - preferred_style: value/growth/quality/momentum/dividend

        Returns:
            Strategy recommendation with conditions
        """
        return await self.handler.recommend(user_profile)


async def main():
    """Interactive CLI for testing."""
    bot = QuantAdvisorBot()

    print("Quant Advisor Chatbot")
    print("=" * 50)
    print("Type 'quit' to exit\n")

    session_id = "cli_session"

    while True:
        try:
            user_input = input("You: ").strip()

            if not user_input:
                continue

            if user_input.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break

            # Get response
            response = await bot.chat(user_input, session_id)

            print(f"\nBot: {response['answer']}\n")

            # Show conditions if available
            if 'conditions' in response:
                print("Recommended Conditions:")
                print(response['conditions'])
                print()

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
