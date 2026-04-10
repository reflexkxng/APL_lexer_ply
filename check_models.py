import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("Error: GEMINI_API_KEY not found in .env")
    exit(1)

genai.configure(api_key=api_key)

try:
    print("Listing available Gemini models...")
    models = genai.list_models()
    for m in models:
        if 'generateContent' in m.supported_generation_methods:
            print(f"- {m.name} (Supported methods: {m.supported_generation_methods})")
except Exception as e:
    print(f"\n[ERROR] Failed to list models: {e}")
    print("\nTroubleshooting tips:")
    print("1. Ensure your GEMINI_API_KEY in .env is valid.")
    print("2. Make sure google-generativeai is up to date (run: pip install --upgrade google-generativeai)")
    print("3. Check your internet connection.")
