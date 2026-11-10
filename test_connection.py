"""
Minimal connection test script.
Run this to confirm your Gemini API key and connection work properly:
    python test_connection.py
"""

import os
import sys
from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("[ERROR] GEMINI_API_KEY is not set!")
    print("Please create a .env file with:")
    print("GEMINI_API_KEY=your_actual_key_here")
    sys.exit(1)

model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

print(f"Connecting to Google Gemini using model: {model_name}...")

try:
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=model_name,
        contents="Say hello in one short sentence and state your model name."
    )
    print("\n[SUCCESS] Response received from Gemini:")
    print(response.text)
except Exception as e:
    print(f"\n[ERROR] Connection failed: {e}")
    sys.exit(1)
