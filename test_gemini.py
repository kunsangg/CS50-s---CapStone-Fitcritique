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
models = res.json().get("models", [])
for m in models:
    if "flash" in m["name"]:
        print(m["name"])


print("Calling Gemini...")
try:
    # We will modify get_fashion_critique to not crash, or just catch it.
    res = get_fashion_critique(history, image_base64, image_mime_type)
    print("Success:")
    print(json.dumps(res, indent=2))
except Exception as e:
    print("Error:", e)
