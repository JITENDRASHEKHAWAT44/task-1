"""
Interactive Command Line Interface (CLI) for the Gemini Chatbot.
Run with:
    python cli.py
"""

import sys
import os
from chatbot import GeminiChatbot, DEFAULT_MODEL, DEFAULT_MAX_CONTEXT


def print_banner():
    print("=" * 60)
    print("NOVA -- Your Gemini AI Coding Mentor")
    print(f"Model: {DEFAULT_MODEL} | Sliding Context Window: {DEFAULT_MAX_CONTEXT} messages")
    print("Commands:")
    print("  'clear' or 'new'  - Start a new conversation session")
    print("  'context'         - View current context window stats")
    print("  'exit' or 'quit'   - End chat")
    print("=" * 60)
    print()


def main():
    bot = GeminiChatbot()

    if not bot.is_configured():
        print("[WARNING] GEMINI_API_KEY environment variable is not set.")
        key_input = input("Enter your Gemini API key (or press Enter to exit): ").strip()
        if not key_input:
            print("No API key provided. Exiting.")
            sys.exit(1)
        bot.set_api_key(key_input)

    print_banner()
    conversation_id = bot.get_or_create_conversation()

    while True:
        try:
            user_input = input("\nYou > ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            break

        if not user_input:
            continue

        cmd = user_input.lower()
        if cmd in ("exit", "quit", "q"):
            print("Nova > Goodbye! Happy coding!")
            break

        if cmd in ("clear", "new", "reset"):
            conversation_id = bot.get_or_create_conversation()
            bot.clear_history(conversation_id)
            print("\n[System] Conversation reset. Starting fresh session!")
            continue

        if cmd == "context":
            history = bot.get_history(conversation_id)
            print(f"\n[Context Stats]")
            print(f"  Total messages stored: {len(history)}")
            print(f"  Context limit: {bot.max_context_messages}")
            print(f"  Messages sent to Gemini: {min(len(history), bot.max_context_messages)}")
            continue

        print("\nNova is thinking...", end="\r", flush=True)

        result = bot.send_message(user_input, conversation_id=conversation_id)

        # Clear 'thinking' indicator
        print(" " * 25, end="\r", flush=True)

        if result.get("success"):
            print(f"Nova > {result['reply']}")
            if result.get("context_truncated"):
                print(
                    f"\n  [Context Notice: Conversation is long. Older messages were pruned "
                    f"to keep the latest {result['context_messages_sent']} messages in context.]"
                )
        else:
            print(f"\n[Error] {result.get('error', 'Unknown error occurred.')}")


if __name__ == "__main__":
    main()
