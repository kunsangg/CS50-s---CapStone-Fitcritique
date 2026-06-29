import os
import sys
import requests
from django.conf import settings

# Add core path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fitcritic.settings")
import django
django.setup()

api_key = settings.GEMINI_API_KEY
url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
res = requests.get(url)
models = [m["name"] for m in res.json().get("models", []) if "flash" in m["name"]]

for model in models:
    url = f"https://generativelanguage.googleapis.com/v1beta/{model}:generateContent?key={api_key}"
    payload = {
        "contents": [{"role": "user", "parts": [{"text": "Hello"}]}],
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 10}
    }
    res = requests.post(url, json=payload)
    if res.status_code == 200:
        print(f"[OK] {model}")
    else:
        text = res.text
        if "limit: 0" in text:
            print(f"[FAIL] {model}: Limit is 0")
        elif "limit:" in text:
            # find what the limit is
            idx = text.find("limit: ")
            print(f"[FAIL] {model}: limit found: {text[idx:idx+15]}")
        else:
            print(f"[FAIL] {model}: {res.status_code}")


print("Calling Gemini...")
try:
    # We will modify get_fashion_critique to not crash, or just catch it.
    res = get_fashion_critique(history, image_base64, image_mime_type)
    print("Success:")
    print(json.dumps(res, indent=2))
except Exception as e:
    print("Error:", e)
