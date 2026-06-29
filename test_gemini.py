import os
import sys
import json
import base64
import requests

# Add core path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fitcritic.settings")
import django
django.setup()

from core.utils.llm import get_fashion_critique
from django.conf import settings

image_url = "https://images.unsplash.com/photo-1768610285210-b476545015af?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w5ODg0MjR8MHwxfHJhbmRvbXx8fHx8fHx8fDE3ODI3NDE5NTB8&ixlib=rb-4.1.0&q=80&w=1080"
print("Fetching image...")
img_res = requests.get(image_url)
image_base64 = base64.b64encode(img_res.content).decode("utf-8")
image_mime_type = img_res.headers.get("Content-Type", "image/jpeg")

history = [
    {
        "role": "user",
        "parts": [{"text": "Critique this style: Woman in sparkling dress with red fabric at night"}]
    }
]

print("Calling Gemini...")
try:
    # We will modify get_fashion_critique to not crash, or just catch it.
    res = get_fashion_critique(history, image_base64, image_mime_type)
    print("Success:")
    print(json.dumps(res, indent=2))
except Exception as e:
    print("Error:", e)
