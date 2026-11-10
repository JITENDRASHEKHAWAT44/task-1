// Client-side chat logic with context management awareness and error handling
let conversationId = sessionStorage.getItem("nova_conversation_id") || "";
let turnCount = 0;
let maxContextMessages = 10;

const chatContainer = document.getElementById("chatContainer");
const emptyState = document.getElementById("emptyState");
const chatForm = document.getElementById("chatForm");
const userInput = document.getElementById("userInput");
const sendBtn = document.getElementById("sendBtn");
const newChatBtn = document.getElementById("newChatBtn");
const statusPill = document.getElementById("statusPill");
const statusLabel = document.getElementById("statusLabel");
const modelDisplay = document.getElementById("modelDisplay");
const turnCounter = document.getElementById("turnCounter");
const contextWindowDisplay = document.getElementById("contextWindowDisplay");
const truncatedBadge = document.getElementById("truncatedBadge");
const noticeBanner = document.getElementById("noticeBanner");
const noticeText = document.getElementById("noticeText");
const dismissNotice = document.getElementById("dismissNotice");

// Check backend status on page load
async function checkStatus() {
  try {
    const res = await fetch("/api/status");
    if (!res.ok) throw new Error("Backend not responding");
    const data = await res.json();

    modelDisplay.textContent = data.model || "gemini-2.5-flash";
    maxContextMessages = data.max_context_messages || 10;
    updateContextDisplay(0);

    if (data.status === "ready") {
      statusPill.className = "status-pill ready";
      statusLabel.textContent = "Connected";
    } else {
      statusPill.className = "status-pill warning";
      statusLabel.textContent = "API Key Missing";
      showNotice(
        "API Key not detected. Please add GEMINI_API_KEY to your .env file and restart the server.",
        "warning"
      );
    }
  } catch (err) {
    statusPill.className = "status-pill error";
    statusLabel.textContent = "Offline";
    showNotice("Cannot connect to backend server. Make sure it is running on port 8000.", "error");
  }
}

function showNotice(text, type = "error") {
  noticeText.textContent = text;
  noticeBanner.className = `notice-banner ${type === "info" ? "info" : ""}`;
  noticeBanner.style.display = "flex";
}

dismissNotice.addEventListener("click", () => {
  noticeBanner.style.display = "none";
});

function updateContextDisplay(totalMsgs, truncated = false) {
  const sentMsgs = Math.min(totalMsgs, maxContextMessages);
  contextWindowDisplay.textContent = `${sentMsgs} / ${maxContextMessages} msgs`;
  if (truncated) {
    truncatedBadge.style.display = "inline-block";
  } else {
    truncatedBadge.style.display = "none";
  }
}

// Auto-grow textarea
userInput.addEventListener("input", () => {
  userInput.style.height = "auto";
  userInput.style.height = Math.min(userInput.scrollHeight, 160) + "px";
});

// Handle Enter to submit (Shift+Enter for newline)
userInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    chatForm.requestSubmit();
  }
});

// Helper to escape HTML to prevent XSS
function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

// Simple markdown-to-html formatter for code blocks & inline code
function formatMessageText(text) {
  // Format code blocks ```code```
  const codeBlockRegex = /```([a-zA-Z0-9_-]*)\n([\s\S]*?)```/g;
  let formatted = text.replace(codeBlockRegex, (_, lang, code) => {
    return `<pre><code>${escapeHtml(code.trim())}</code></pre>`;
  });

  // Format inline `code`
  formatted = formatted.replace(/`([^`]+)`/g, (_, inline) => {
    return `<code>${escapeHtml(inline)}</code>`;
  });

  // Convert double newlines to paragraphs / linebreaks
  formatted = formatted.replace(/\n\n/g, "<br><br>");
  formatted = formatted.replace(/\n/g, "<br>");

  return formatted;
}

function appendMessage(role, text, isPending = false) {
  if (emptyState) {
    emptyState.style.display = "none";
  }

  const row = document.createElement("div");
  row.className = `message-row ${role}`;

  const avatar = document.createElement("div");
  avatar.className = "message-avatar";
  avatar.textContent = role === "user" ? "You" : "Nova";

  const bubble = document.createElement("div");
  bubble.className = "message-bubble";

  if (isPending) {
    bubble.id = "pendingBubble";
    bubble.innerHTML = `
      <div class="typing-dots">
        <span class="typing-dot"></span>
        <span class="typing-dot"></span>
        <span class="typing-dot"></span>
      </div>
    `;
  } else {
    bubble.innerHTML = formatMessageText(text);
  }

  row.appendChild(avatar);
  row.appendChild(bubble);
  chatContainer.appendChild(row);
  chatContainer.scrollTop = chatContainer.scrollHeight;

  return row;
}

// Submit message handler
chatForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const text = userInput.value.trim();
  if (!text) return;

  // Add user message
  appendMessage("user", text);
  userInput.value = "";
  userInput.style.height = "auto";
  userInput.disabled = true;
  sendBtn.disabled = true;

  // Add pending indicator
  const pendingRow = appendMessage("model", "", true);

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: text,
        conversation_id: conversationId || undefined,
      }),
    });

    const data = await res.json();
    pendingRow.remove();

    if (data.success) {
      conversationId = data.conversation_id;
      sessionStorage.setItem("nova_conversation_id", conversationId);

      turnCount += 1;
      turnCounter.textContent = turnCount;

      updateContextDisplay(data.total_messages_stored, data.context_truncated);
      appendMessage("model", data.reply);
    } else {
      appendMessage(
        "model",
        `⚠️ **Error:** ${data.error || "Unable to get response from Gemini."}`
      );
      showNotice(data.error || "API call failed", "error");
    }
  } catch (err) {
    pendingRow.remove();
    appendMessage(
      "model",
      "⚠️ **Network Error:** Failed to communicate with backend server. Check your connection."
    );
    showNotice("Network error: Server did not respond.", "error");
  } finally {
    userInput.disabled = false;
    sendBtn.disabled = false;
    userInput.focus();
    chatContainer.scrollTop = chatContainer.scrollHeight;
  }
});

// Prompt chips handler
document.querySelectorAll(".chip").forEach((chip) => {
  chip.addEventListener("click", () => {
    userInput.value = chip.getAttribute("data-prompt");
    chatForm.requestSubmit();
  });
});

// New Chat button
newChatBtn.addEventListener("click", async () => {
  if (conversationId) {
    try {
      await fetch(`/api/history/${conversationId}`, { method: "DELETE" });
    } catch (_) {}
  }

  sessionStorage.removeItem("nova_conversation_id");
  conversationId = "";
  turnCount = 0;
  turnCounter.textContent = "0";
  updateContextDisplay(0);

  // Clear messages from UI and restore empty state
  chatContainer.innerHTML = "";
  if (emptyState) {
    chatContainer.appendChild(emptyState);
    emptyState.style.display = "flex";
  }
  showNotice("Started a fresh conversation session.", "info");
  setTimeout(() => {
    noticeBanner.style.display = "none";
  }, 2500);
});

// Initialize on page load
checkStatus();
