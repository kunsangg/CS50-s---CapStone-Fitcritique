import os
import json
import requests
import time
from django.conf import settings

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"

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
Never use apostrophes or single quotes anywhere in your JSON response. Use only double quotes for strings. Escape any special characters properly.
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
            "inlineData": {
                "mimeType": image_mime_type,
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
            "responseMimeType": "application/json"
        }
    }
    
    max_retries = 3
    for attempt in range(max_retries):
        response = requests.post(url, json=payload)
        print("STATUS:", response.status_code)
        print("RESPONSE:", response.text)
        
        if response.status_code in [429, 500, 502, 503, 504]:
            wait = 2 ** attempt  # 1s, 2s, 4s
            time.sleep(wait)
            continue
            
        try:
            response.raise_for_status()
        except Exception as e:
            error_msg = str(e).replace(api_key, "HIDDEN_KEY")
            raise Exception(f"Gemini API Error: {error_msg}")
            
        break
    else:
        raise Exception("Gemini API is temporarily unavailable. Please try again.")
    
    data = response.json()
    raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
    
    clean = raw_text.strip()
    
    # Remove markdown fences
    if "```" in clean:
        clean = clean.replace("```json", "").replace("```", "").strip()
    
    # Extract just the JSON object
    start = clean.find("{")
    end = clean.rfind("}") + 1
    if start == -1 or end == 0:
        raise ValueError("No JSON found")
    clean = clean[start:end]
    
    # Fix common Gemini JSON issues:
    # Replace smart quotes with regular double quotes
    clean = clean.replace("\u201c", '"').replace("\u201d", '"')
    clean = clean.replace("\u2018", "'").replace("\u2019", "'")
    
    try:
        return json.loads(clean)
    except json.JSONDecodeError:
        # Last resort: use ast.literal_eval
        try:
            import ast
            return ast.literal_eval(clean)
        except Exception:
            return {
                "fit_score": 0,
                "summary": "Unable to parse response. Please try again with more outfit details.",
                "what_works": [],
                "what_doesnt": [],
                "suggestions": ["Describe specific pieces, colors, and the occasion."],
                "products": []
            }
