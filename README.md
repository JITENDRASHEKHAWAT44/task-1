# Nova — Gemini Multi-Turn AI Coding Mentor 🤖

A simple, robust, production-grade chatbot backed by the **Google Gemini API** (`google-genai` SDK) featuring **context window management**, multi-turn memory persistence, persona customization via system prompt, comprehensive error handling, a REST API, and both Web and CLI interfaces.

---

## 🎯 Requirements Met

| Requirement | Implementation Detail | Status |
| :--- | :--- | :--- |
| **Backend Endpoint** | FastAPI server (`/api/chat`, `/api/history/{id}`, `/api/status`) | ✅ Complete |
| **Multi-turn History** | Session-based memory tracking conversation history per user/session | ✅ Complete |
| **Context Management** | Sliding-window truncation (retains last $N$ messages, ensures turn starts with `user`) | ✅ Complete |
| **System Prompt Persona** | Persona: **Nova**, an encouraging, sharp coding mentor | ✅ Complete |
| **Error Handling** | Catches missing keys, HTTP 429 (rate limits), 403 (perms), network timeouts | ✅ Complete |
| **Secure Key Handling** | Loaded via `python-dotenv` from `.env`; `.env` protected in `.gitignore` | ✅ Complete |
| **UI & CLI Interfaces** | Polished responsive Web UI (`static/`) + Interactive Terminal CLI (`cli.py`) | ✅ Complete |

---

## 📁 Project Structure

```
├── .env.example            # Environment variables template (API keys, model name)
├── .gitignore              # Protects secrets (.env) and Python artifacts
├── requirements.txt        # Dependencies (google-genai, fastapi, uvicorn, python-dotenv)
├── chatbot.py              # Core Gemini client, context window manager & persona
├── app.py                  # FastAPI backend and static web server
├── cli.py                  # Interactive terminal interface
├── test_connection.py      # Quick 1-message connection tester
├── test_suite.py           # Automated unit tests for context management and history
├── static/
│   ├── index.html          # Polished single-page chat interface
│   ├── style.css           # Clean, accessible styling (WCAG AA contrast)
│   └── script.js           # Client-side chat loop, stats counter, error banners
└── README.md               # Documentation and submission guide
```

---

## 🚀 Quickstart Guide

### 1. Prerequisites
- Python 3.10+ installed
- Free Gemini API Key from [Google AI Studio](https://aistudio.google.com/app/apikey)

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Your Environment Variable
Copy the `.env.example` file to `.env`:
```bash
# On Windows PowerShell:
Copy-Item .env.example .env

# On Mac/Linux:
cp .env.example .env
```

Open `.env` and insert your Gemini API Key:
```env
GEMINI_API_KEY=AIzaSy...your_actual_key_here
GEMINI_MODEL=gemini-2.5-flash
MAX_CONTEXT_MESSAGES=10
```

> **Security Note:** `.env` is listed in `.gitignore` and will never be committed to Git.

---

## 🧪 Testing Your Connection

### Step 1: Verify API Key Connection
Run the single-message test script:
```bash
python test_connection.py
```
If your key is valid, it prints a one-sentence reply from Gemini.

### Step 2: Run Automated Unit Tests
```bash
python test_suite.py
```
This tests initialization, missing API key handling, multi-turn history retention, and context truncation logic.

---

## 💬 Running the Chatbot

You have two ways to interact with Nova:

### Option A: Modern Web UI (Recommended)
Start the FastAPI server:
```bash
python app.py
```
Open your browser and navigate to:
```
http://127.0.0.1:8000
```
- Real-time conversation turns counter.
- Live context window monitor (`X / 10 msgs`).
- Visual indicator when sliding-window context truncation activates.
- "New Chat" button to reset the session.

### Option B: Terminal CLI
Run directly in your command line:
```bash
python cli.py
```
Special commands in CLI:
- `clear` or `new`: Starts a new session.
- `context`: Displays current context window statistics.
- `exit` or `quit`: Exits the chatbot.

---

## 🧠 Context Window Management Strategy

LLMs have token limits, and sending infinite message history increases latency and cost. This project implements a **Sliding-Window Truncation Strategy** (`chatbot.py`):

1. **Configurable Window**: Controlled by `MAX_CONTEXT_MESSAGES` (default `10` messages = 5 conversation turns).
2. **Preserves the System Prompt**: The persona prompt is passed via Gemini's dedicated `system_instruction` config, guaranteeing that pruning older chat messages never erases Nova's identity or guidelines.
3. **Alternating Turn Order Integrity**: If truncation cuts off at an assistant response, the algorithm automatically trims until the window starts with a `user` message, preventing Gemini API role-ordering validation errors.
4. **Metadata Reporting**: The backend endpoint returns `context_messages_sent` and `context_truncated: bool`, allowing the frontend and CLI to inform the user when older messages are pruned.

---

## 🎭 System Prompt & Persona

The bot uses the **Nova** persona configured in `chatbot.py`:
- **Role**: Software engineering mentor.
- **Tone**: Friendly, upbeat, encouraging, and concise.
- **Rules**: Explains concepts clearly, includes small code snippets where relevant, and remembers user details throughout multi-turn chats.

---

## 🛡️ Error Handling

The application anticipates and handles failures gracefully:
- **Missing API Key**: Catches unconfigured keys before calling the API and returns an actionable instruction to set `GEMINI_API_KEY` in `.env`.
- **Rate Limit (HTTP 429 / RESOURCE_EXHAUSTED)**: Informs user that quota was reached and to wait a moment.
- **Invalid Key (HTTP 400/403)**: Informs user that authentication failed.
- **Network / Timeout / Service Outage**: Catches exceptions and surfaces an error banner without breaking the frontend or CLI.

---

## 📋 5-Turn Verification Walkthrough

Before submitting, verify multi-turn context retention with this test flow:

| Turn | You Say | Expected Behavior |
| :--- | :--- | :--- |
| **Turn 1** | "Hi! My name is Jordan and I am learning Python." | Nova greets Jordan and welcomes him to Python. |
| **Turn 2** | "I want to build a simple calculator function." | Nova provides a clean Python calculator example. |
| **Turn 3** | "Can you modify it to also support division?" | Nova updates the previous calculator code (context reference). |
| **Turn 4** | "What was my name and what language are we using?" | Nova responds with **Jordan** and **Python** (demonstrating multi-turn memory). |
| **Turn 5** | "Give me one best practice for handling division by zero in that function." | Nova references `ZeroDivisionError` specifically for the function discussed. |

---

## 🌐 Free Cloud Deployment (Render / Railway)

### Option 1: Deploy on Render (Recommended, Free)
1. Push your repository to **GitHub**.
2. Go to [Render.com](https://render.com) and create a free account.
3. Click **New +** -> **Web Service** -> Connect your GitHub repo.
4. Render will auto-detect Python and the included `render.yaml` / `Procfile`:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app:app --host 0.0.0.0 --port $PORT`
5. In the **Environment Variables** section, add:
   - `GEMINI_API_KEY`: *(paste your real Google AI Studio key)*
   - `GEMINI_MODEL`: `gemini-3.5-flash-lite`
6. Click **Deploy Web Service**. In ~2 minutes, your live public chatbot URL will be active!

---

## 📤 Git Submission Steps

```bash
# 1. Initialize git
git init

# 2. Verify .env is ignored (crucial!)
git status
# Make sure .env is NOT listed under untracked files

# 3. Stage and commit files
git add .
git commit -m "feat: complete Gemini multi-turn chatbot with context window management"

# 4. Push to your public GitHub repo
git branch -M main
git remote add origin https://github.com/<your-username>/<your-repo-name>.git
git push -u origin main
```
