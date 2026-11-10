"""
Automated unit and integration tests for the Gemini Chatbot.
Run with:
    python test_suite.py
    or
    pytest test_suite.py
"""

from chatbot import GeminiChatbot, SYSTEM_PROMPT


def test_initialization():
    bot = GeminiChatbot(api_key="dummy_key", max_context_messages=6)
    assert bot.api_key == "dummy_key"
    assert bot.max_context_messages == 6
    assert bot.system_instruction == SYSTEM_PROMPT
    assert bot.is_configured() is True
    print("[PASS] test_initialization")


def test_missing_api_key_handling():
    bot = GeminiChatbot(api_key="")
    res = bot.send_message("Hello")
    assert res["success"] is False
    assert "Gemini API key is missing" in res["error"]
    print("[PASS] test_missing_api_key_handling")


def test_multi_turn_history_storage():
    bot = GeminiChatbot(api_key="dummy_key")
    conv_id = "test_conversation_123"

    # Simulate multi-turn conversation
    bot.conversations[conv_id] = [
        {"role": "user", "text": "My favorite language is Python.", "timestamp": ""},
        {"role": "model", "text": "Python is a great language! What do you like about it?", "timestamp": ""},
        {"role": "user", "text": "I like its readability.", "timestamp": ""},
    ]

    history = bot.get_history(conv_id)
    assert len(history) == 3
    assert history[0]["text"] == "My favorite language is Python."
    assert history[2]["text"] == "I like its readability."

    # Test clearing history
    bot.clear_history(conv_id)
    assert len(bot.get_history(conv_id)) == 0
    print("[PASS] test_multi_turn_history_storage")


def test_context_window_truncation():
    """Verifies that context is bounded and pruned when exceeding max_context_messages."""
    bot = GeminiChatbot(api_key="dummy_key", max_context_messages=4)
    conv_id = "test_context_conv"

    # Populate 8 messages (4 turns)
    bot.conversations[conv_id] = [
        {"role": "user", "text": "turn 1 user", "timestamp": ""},
        {"role": "model", "text": "turn 1 model", "timestamp": ""},
        {"role": "user", "text": "turn 2 user", "timestamp": ""},
        {"role": "model", "text": "turn 2 model", "timestamp": ""},
        {"role": "user", "text": "turn 3 user", "timestamp": ""},
        {"role": "model", "text": "turn 3 model", "timestamp": ""},
        {"role": "user", "text": "turn 4 user", "timestamp": ""},
        {"role": "model", "text": "turn 4 model", "timestamp": ""},
    ]

    contents, was_truncated, count = bot._prepare_context(conv_id)

    assert was_truncated is True
    assert count == 4
    # Make sure it retained the most recent 4 messages: turn 3 user, turn 3 model, turn 4 user, turn 4 model
    assert contents[0].parts[0].text == "turn 3 user"
    assert contents[0].role == "user"
    assert contents[1].parts[0].text == "turn 3 model"
    assert contents[2].parts[0].text == "turn 4 user"
    assert contents[3].parts[0].text == "turn 4 model"
    print("[PASS] test_context_window_truncation")


def test_context_window_preserves_first_user_role():
    """
    If truncation happens to slice right after a user message,
    the first item in window would be 'model'.
    Our logic must drop that 'model' turn so the window properly starts with 'user'.
    """
    bot = GeminiChatbot(api_key="dummy_key", max_context_messages=3)
    conv_id = "test_role_alignment"

    bot.conversations[conv_id] = [
        {"role": "user", "text": "m1", "timestamp": ""},
        {"role": "model", "text": "m2", "timestamp": ""},
        {"role": "user", "text": "m3", "timestamp": ""},
        {"role": "model", "text": "m4", "timestamp": ""},
    ]

    contents, was_truncated, count = bot._prepare_context(conv_id)
    assert was_truncated is True
    # The last 3 are [model m2, user m3, model m4]. Slicing drops model m2 so window starts with user m3.
    assert contents[0].role == "user"
    assert contents[0].parts[0].text == "m3"
    print("[PASS] test_context_window_preserves_first_user_role")


if __name__ == "__main__":
    print("Running Chatbot unit tests...")
    test_initialization()
    test_missing_api_key_handling()
    test_multi_turn_history_storage()
    test_context_window_truncation()
    test_context_window_preserves_first_user_role()
    print("\nAll 5 tests passed successfully! [OK]")
