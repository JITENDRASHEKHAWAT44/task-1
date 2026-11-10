"""
Minimal connection test script.
Run this to confirm your Gemini API key and connection work properly:
    python test_connection.py
"""

import os
import sys
import warnings
from env_loader import load_env

# Suppress harmless SDK warnings
warnings.filterwarnings("ignore")

# Load variables from .env
load_env()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("[ERROR] GEMINI_API_KEY is not set!")
    print("Please ensure your .env file contains:")
    print("GEMINI_API_KEY=your_actual_key_here")
    sys.exit(1)

model_name = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")

print(f"Connecting to Google Gemini using model: {model_name}...")

try:
    from google import genai
    client = genai.Client(api_key=api_key)

    response = client.models.generate_content(
        model=model_name,
        contents="Say hello in one short sentence and state your model name."
    )
    print("\n[SUCCESS] Response received from Gemini:")
    print(response.text.strip())
except ImportError:
    print("[ERROR] google-genai is not installed in the currently running Python.")
    print("Run: & 'C:\\Program Files\\Python312\\python.exe' -m pip install -r requirements.txt")
    sys.exit(1)
except Exception as e:
    # If the chosen model is experiencing demand spikes or retired, try fallback
    fallback_model = "gemini-3.5-flash-lite"
    if model_name != fallback_model:
        try:
            print(f"Model {model_name} returned an issue. Retrying with fallback: {fallback_model}...")
            response = client.models.generate_content(
                model=fallback_model,
                contents="Say hello in one short sentence."
            )
            print(f"\n[SUCCESS] Response received using fallback {fallback_model}:")
            print(response.text.strip())
            sys.exit(0)
        except Exception:
            pass
    print(f"\n[ERROR] Connection failed: {e}")
    sys.exit(1)
