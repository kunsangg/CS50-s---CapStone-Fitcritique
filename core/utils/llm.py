import os
import json
import requests
from django.conf import settings

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"

SYSTEM_PROMPT = """
You are FitCritic, a sharp, direct, knowledgeable fashion critic 
with the sensibility of a senior stylist at a premium editorial 
magazine. You analyze outfits described or shown to you and give 
honest, structured, actionable feedback.

Always respond ONLY in valid JSON with this exact structure, 
no markdown, no backticks, no preamble:
{
  "fit_score": <integer 1-10>,
  "summary": "<2-3 sentence overall take>",
  "what_works": ["<specific observation>", ...],
  "what_doesnt": ["<specific observation>", ...],
  "suggestions": ["<actionable styling tip>", ...],
  "products": [
    { 
      "name": "<product name>", 
      "reason": "<why this piece>" 
    }
  ]
}

Be direct. Do not be encouraging for the sake of it. 
If something does not work, say so clearly. 
Use fashion terminology accurately. 
Never break from JSON format.
"""

def get_fashion_critique(conversation_history, image_base64=None, 
                         image_mime_type=None):
    """
    conversation_history: list of dicts [{"role": "user"/"model", 
                                          "parts": [{"text": "..."}]}]
    image_base64: optional base64 encoded image string
    image_mime_type: e.g. "image/jpeg" or "image/png"
    """
    
    api_key = settings.GEMINI_API_KEY
    url = f"{GEMINI_API_URL}?key={api_key}"
    
    # Build the contents array
    contents = []
    
    # Add system prompt as first user turn
    contents.append({
        "role": "user",
        "parts": [{"text": SYSTEM_PROMPT}]
    })
    contents.append({
        "role": "model", 
        "parts": [{"text": "Understood. I will respond only in the specified JSON format."}]
    })
    
    # Add conversation history
    for msg in conversation_history[:-1]:
        contents.append(msg)
    
    # Build the final user message (last in history)
    last_message = conversation_history[-1]
    final_parts = []
    
    # Add image if provided
    if image_base64 and image_mime_type:
        final_parts.append({
            "inline_data": {
                "mime_type": image_mime_type,
                "data": image_base64
            }
        })
    
    # Add text
    final_parts.append({"text": last_message["parts"][0]["text"]})
    
    contents.append({
        "role": "user",
        "parts": final_parts
    })
    
    payload = {
        "contents": contents,
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 1024,
        }
    }
    
    response = requests.post(url, json=payload)
    response.raise_for_status()
    
    data = response.json()
    raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
    
    # Clean up in case model wraps in backticks
    clean = raw_text.strip()
    if clean.startswith("```"):
        clean = clean.split("```")[1]
        if clean.startswith("json"):
            clean = clean[4:]
    clean = clean.strip()
    
    return json.loads(clean)
