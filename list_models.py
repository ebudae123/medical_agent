"""
List available Gemini models
"""
import google.generativeai as genai
from backend.config import get_settings

settings = get_settings()
genai.configure(api_key=settings.google_api_key)

print("[*] Listing available Gemini models:\n")

try:
    for model in genai.list_models():
        if 'generateContent' in model.supported_generation_methods:
            print(f"  - {model.name}")
            print(f"    Display name: {model.display_name}")
            print(f"    Description: {model.description[:100]}...")
            print()
except Exception as e:
    print(f"[-] Error: {e}")
