import os
import uuid
import warnings
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from env_loader import load_env
from google import genai
from google.genai import types, errors

# Suppress harmless SDK warnings
warnings.filterwarnings("ignore")

# Load environment variables
load_env()

# System Prompt defining the bot's persona and constraints
SYSTEM_PROMPT = """You are Nova, an upbeat, sharp, and encouraging software engineering mentor.
Your characteristics:
1. Role: Guide developers through writing clean code, understanding concepts, and debugging issues.
2. Tone: Friendly, concise, supportive, and practical. Avoid overly robotic greetings or fluff.
3. Behavior: Break down complex problems into digestible steps. Include concise code snippets when helpful.
4. Memory: You remember details shared earlier in the conversation (names, preferences, code snippets).
"""

DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
FALLBACK_MODEL = "gemini-3.5-flash-lite"
DEFAULT_MAX_CONTEXT = int(os.getenv("MAX_CONTEXT_MESSAGES", "10"))


class GeminiChatbot:
    """
    Manages multi-turn conversations with Google Gemini models,
    including context window sliding-window truncation and robust error handling.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = DEFAULT_MODEL,
        max_context_messages: int = DEFAULT_MAX_CONTEXT,
        system_instruction: str = SYSTEM_PROMPT,
    ):
        load_env()
        self.api_key = (api_key if api_key is not None else os.getenv("GEMINI_API_KEY", "")).strip()
        self.model_name = model_name
        self.max_context_messages = max_context_messages
        self.system_instruction = system_instruction
        self.client: Optional[genai.Client] = None

        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)

        # In-memory session store: conversation_id -> list of message dicts
        self.conversations: Dict[str, List[Dict[str, str]]] = {}

    def is_configured(self) -> bool:
        """Checks if the API client is configured with an API key."""
        return bool(self.api_key and self.client)

    def set_api_key(self, key: str) -> None:
        """Update or set the API key dynamically."""
        self.api_key = key.strip()
        self.client = genai.Client(api_key=self.api_key)

    def get_or_create_conversation(self, conversation_id: Optional[str] = None) -> str:
        """Returns existing conversation_id or generates a new one."""
        if not conversation_id or conversation_id not in self.conversations:
            new_id = conversation_id or str(uuid.uuid4())
            self.conversations[new_id] = []
            return new_id
        return conversation_id

    def get_history(self, conversation_id: str) -> List[Dict[str, str]]:
        """Retrieves raw history for a conversation."""
        return self.conversations.get(conversation_id, [])

    def clear_history(self, conversation_id: str) -> bool:
        """Clears messages for a conversation session."""
        if conversation_id in self.conversations:
            self.conversations[conversation_id] = []
            return True
        return False

    def _prepare_context(self, conversation_id: str) -> Tuple[List[types.Content], bool, int]:
        """
        Applies context window management (sliding window truncation).
        Returns:
            - contents: list of types.Content to send to Gemini
            - was_truncated: boolean indicating whether older messages were trimmed
            - context_size: count of messages included in current payload
        """
        history = self.conversations.get(conversation_id, [])
        total_messages = len(history)

        if total_messages <= self.max_context_messages:
            selected_history = list(history)
            was_truncated = False
        else:
            selected_history = history[-self.max_context_messages:]
            was_truncated = True

        # Gemini multi-turn content must start with a 'user' turn.
        while selected_history and selected_history[0]["role"] != "user":
            selected_history.pop(0)

        # Format into google.genai types.Content objects
        contents: List[types.Content] = []
        for msg in selected_history:
            contents.append(
                types.Content(
                    role=msg["role"],
                    parts=[types.Part.from_text(text=msg["text"])]
                )
            )

        return contents, was_truncated, len(contents)

    def send_message(self, message: str, conversation_id: Optional[str] = None) -> Dict:
        """
        Sends a user message, manages multi-turn history with context pruning,
        calls the Gemini model, and records the response.
        """
        conv_id = self.get_or_create_conversation(conversation_id)
        clean_text = message.strip()

        if not clean_text:
            return {
                "success": False,
                "error": "Message cannot be empty.",
                "conversation_id": conv_id,
            }

        if not self.is_configured():
            return {
                "success": False,
                "error": "Gemini API key is missing. Please set GEMINI_API_KEY in your .env file or environment.",
                "conversation_id": conv_id,
            }

        # 1. Append user message to full session history
        now = datetime.now().isoformat()
        self.conversations[conv_id].append({
            "role": "user",
            "text": clean_text,
            "timestamp": now,
        })

        # 2. Context window management: prepare truncated window
        contents, was_truncated, context_count = self._prepare_context(conv_id)

        # 3. Call Gemini API with system instruction & robust error handling
        config = types.GenerateContentConfig(
            system_instruction=self.system_instruction,
            max_output_tokens=1024,
            temperature=0.7,
        )

        try:
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=contents,
                    config=config,
                )
            except errors.APIError as api_err:
                # If model is deprecated (404) or overloaded (503), try fallback
                if self.model_name != FALLBACK_MODEL and (getattr(api_err, "code", None) in (404, 503) or "NOT_FOUND" in str(api_err)):
                    response = self.client.models.generate_content(
                        model=FALLBACK_MODEL,
                        contents=contents,
                        config=config,
                    )
                else:
                    raise api_err

            reply_text = response.text or "I heard you, but I didn't generate any text response."

            # 4. Save model response to session history
            self.conversations[conv_id].append({
                "role": "model",
                "text": reply_text,
                "timestamp": datetime.now().isoformat(),
            })

            return {
                "success": True,
                "reply": reply_text,
                "conversation_id": conv_id,
                "total_messages_stored": len(self.conversations[conv_id]),
                "context_messages_sent": context_count,
                "context_truncated": was_truncated,
            }

        except errors.APIError as e:
            error_message = self._format_api_error(e)
            return {
                "success": False,
                "error": error_message,
                "conversation_id": conv_id,
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "conversation_id": conv_id,
            }

    def _format_api_error(self, err: errors.APIError) -> str:
        """Translates low-level API errors into clear, actionable user messages."""
        msg = str(err)
        code = getattr(err, "code", None)

        if code == 400 or "API_KEY_INVALID" in msg:
            return "Invalid API Key. Please verify your GEMINI_API_KEY in the .env file."
        elif code == 403:
            return "Permission denied. Check that your API key has Gemini API access enabled."
        elif code == 429 or "RESOURCE_EXHAUSTED" in msg:
            return "Rate limit reached or quota exceeded. Please wait a few moments before trying again."
        elif code in (500, 503) or "UNAVAILABLE" in msg:
            return "Google Gemini service is temporarily unavailable. Please retry in a moment."
        else:
            return f"Gemini API Error ({code or 'Unknown'}): {err.message if hasattr(err, 'message') else msg}"
