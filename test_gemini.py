"""
Test script to verify Gemini API is working with the new model
"""
import google.generativeai as genai
from backend.config import get_settings

settings = get_settings()

print(f"[*] Testing Gemini API...")
print(f"API Key configured: {settings.google_api_key[:20]}...")
print(f"Model: {settings.gemini_model}\n")

try:
    genai.configure(api_key=settings.google_api_key)
    model = genai.GenerativeModel(settings.gemini_model)
    
    print("[*] Sending test prompt...")
    response = model.generate_content("Say 'Hello, API is working!' in one sentence.")
    
    print(f"[+] Success! Response: {response.text}")
    
except Exception as e:
    print(f"[-] Error: {type(e).__name__}")
    print(f"Message: {str(e)}")
