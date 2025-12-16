#!/usr/bin/env python
"""Debug script untuk test API Gemini secara verbose"""
import os
import sys
from pathlib import Path

# Load .env
env_path = Path(__file__).with_name('.env')
if env_path.exists():
    for line in env_path.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if '=' in line:
            k, v = line.split('=', 1)
            k = k.strip()
            v = v.strip().strip('"').strip("'")
            if k not in os.environ:
                os.environ[k] = v

GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')
print(f"[DEBUG] API_KEY loaded: {bool(GOOGLE_API_KEY)}")
if GOOGLE_API_KEY:
    print(f"[DEBUG] API_KEY starts with: {GOOGLE_API_KEY[:20]}...")

# Try import
try:
    import google.generativeai as genai
    print("[DEBUG] google.generativeai imported OK")
except Exception as e:
    print(f"[ERROR] Failed to import google.generativeai: {e}")
    sys.exit(1)

# Configure
if GOOGLE_API_KEY:
    try:
        genai.configure(api_key=GOOGLE_API_KEY)
        print("[DEBUG] genai.configure() OK")
    except Exception as e:
        print(f"[WARN] genai.configure() error (may be OK on newer versions): {e}")

# Try GenerativeModel with each model name
models_to_try = [
    'models/gemini-flash-latest',
    'models/gemini-2.5-flash',
    'models/gemini-2.5-pro',
    'models/gemini-3-pro-preview',
]

for model_name in models_to_try:
    print(f"\n[TEST] Trying model: {model_name}")
    try:
        model = genai.GenerativeModel(model_name)
        print(f"  ✓ GenerativeModel({model_name}) created OK")
        
        # Try generate_content with short prompt
        prompt = "Apa itu Buffalo Chicken Pizza? Jawab singkat."
        response = model.generate_content(prompt)
        
        if hasattr(response, 'text') and response.text:
            print(f"  ✓ generate_content() SUCCESS")
            print(f"  Response (first 100 chars): {response.text[:100]}...")
        else:
            print(f"  ✗ generate_content() returned but no text: {response}")
    except Exception as e:
        print(f"  ✗ ERROR: {type(e).__name__}: {e}")

print("\n[DEBUG] Test completed.")
