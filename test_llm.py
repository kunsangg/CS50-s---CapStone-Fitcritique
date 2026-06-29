import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fitcritic.settings')
django.setup()

from core.utils.llm import get_fashion_critique

history = [
    {
        "role": "user",
        "parts": [{"text": "blue jeans and white shirt"}]
    }
]

print("Calling get_fashion_critique...")
try:
    critique = get_fashion_critique(history)
    print("SUCCESS! Parsed JSON:")
    print(critique)
except Exception as e:
    print("Error:", e)
