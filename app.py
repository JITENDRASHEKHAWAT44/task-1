import os
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from chatbot import GeminiChatbot, DEFAULT_MODEL, DEFAULT_MAX_CONTEXT

app = FastAPI(
    title="Gemini Multi-Turn Chatbot API",
    description="Backend API with context window management and persona support",
    version="1.0.0",
)

bot = GeminiChatbot()

# Mount static files directory
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(STATIC_DIR):
    os.makedirs(STATIC_DIR, exist_ok=True)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="User prompt or question")
    conversation_id: Optional[str] = Field(
        None, description="Unique conversation session ID for multi-turn history"
    )


class ChatResponse(BaseModel):
    success: bool
    reply: Optional[str] = None
    error: Optional[str] = None
    conversation_id: str
    total_messages_stored: Optional[int] = 0
    context_messages_sent: Optional[int] = 0
    context_truncated: Optional[bool] = False


@app.get("/")
def serve_index():
    """Serves the front-end chat interface."""
    index_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "Chatbot backend is running. Create static/index.html to view UI."}


@app.get("/api/status")
def get_status():
    """Returns bot status, model name, and context limits."""
    return {
        "status": "ready" if bot.is_configured() else "api_key_missing",
        "model": bot.model_name,
        "max_context_messages": bot.max_context_messages,
        "active_conversations": len(bot.conversations),
    }


@app.post("/api/chat", response_model=ChatResponse)
def chat_endpoint(payload: ChatRequest):
    """
    Main chat endpoint.
    Maintains multi-turn history and sends pruned context window to Gemini API.
    """
    result = bot.send_message(
        message=payload.message,
        conversation_id=payload.conversation_id,
    )

    if not result.get("success"):
        return ChatResponse(
            success=False,
            error=result.get("error", "Failed to process message."),
            conversation_id=result.get("conversation_id", payload.conversation_id or ""),
        )

    return ChatResponse(
        success=True,
        reply=result["reply"],
        conversation_id=result["conversation_id"],
        total_messages_stored=result.get("total_messages_stored", 0),
        context_messages_sent=result.get("context_messages_sent", 0),
        context_truncated=result.get("context_truncated", False),
    )


@app.get("/api/history/{conversation_id}")
def get_conversation_history(conversation_id: str):
    """Retrieves full conversation history for a given session."""
    history = bot.get_history(conversation_id)
    return {
        "conversation_id": conversation_id,
        "message_count": len(history),
        "messages": history,
    }


@app.delete("/api/history/{conversation_id}")
def reset_conversation(conversation_id: str):
    """Resets/clears the history for a given session."""
    success = bot.clear_history(conversation_id)
    return {
        "success": success,
        "conversation_id": conversation_id,
        "message": "Conversation history cleared." if success else "Session not found.",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
