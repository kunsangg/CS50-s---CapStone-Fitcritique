import os
import json
from anthropic import Anthropic
from duckduckgo_search import DDGS

# Initialize anthropic client
api_key = os.environ.get("ANTHROPIC_API_KEY")
client = Anthropic(api_key=api_key)

SYSTEM_PROMPT = """
You are FitCritic, a sharp, direct, knowledgeable fashion critic with the sensibility of a senior stylist at a premium editorial magazine. You analyze outfits described or shown to you and give honest, structured, actionable feedback.

Always respond ONLY in valid JSON with this exact structure:
{
  "fit_score": <integer 1-10>,
  "summary": "<2-3 sentence overall take>",
  "what_works": ["<specific observation>", ...],
  "what_doesnt": ["<specific observation>", ...],
  "suggestions": ["<actionable styling tip>", ...],
  "products": [
    { "name": "<product name>", "url": "<real URL if found via search>", "reason": "<why this piece>" }
  ]
}

Be direct. Do not be encouraging for the sake of it. If something doesn't work, say so clearly. Use fashion terminology accurately. Products should be real, specific, and shoppable. Use the web_search tool to find real products. Never break from JSON format.
"""

def perform_web_search(query):
    try:
        results = DDGS().text(query, max_results=3)
        return json.dumps(results)
    except Exception as e:
        return json.dumps({"error": str(e)})

def get_claude_response(user_text, image_base64=None, chat_history=None):
    """
    Calls Claude API with the given input and returns the structured JSON response.
    chat_history should be a list of dicts: [{'role': 'user', 'content': '...'}, ...]
    """
    messages = []
    
    if chat_history:
        for msg in chat_history:
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
            
    # Construct current message content
    current_content = []
    
    if image_base64:
        # Anthropic expects just the base64 string, without the data URL prefix
        if ";base64," in image_base64:
            media_type = image_base64.split(";")[0].split(":")[1]
            data = image_base64.split(";base64,")[1]
        else:
            media_type = "image/jpeg"
            data = image_base64
            
        current_content.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": media_type,
                "data": data
            }
        })
        
    if user_text:
        current_content.append({
            "type": "text",
            "text": user_text
        })
    elif not image_base64:
        # Fallback if both are empty
        current_content.append({"type": "text", "text": "What do you think of my outfit?"})
        
    messages.append({
        "role": "user",
        "content": current_content
    })
    
    tools = [
        {
            "name": "web_search",
            "description": "Searches the web for fashion products. Use this to find real shoppable links.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query, e.g. 'black leather chelsea boots men'"
                    }
                },
                "required": ["query"]
            }
        }
    ]

    try:
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2000,
            system=SYSTEM_PROMPT,
            messages=messages,
            tools=tools,
        )
        
        # Handle tool use if Claude decides to search
        if response.stop_reason == "tool_use":
            tool_use = next(block for block in response.content if block.type == "tool_use")
            tool_name = tool_use.name
            tool_input = tool_use.input
            
            if tool_name == "web_search":
                search_results = perform_web_search(tool_input["query"])
                
                # Append Claude's tool use to history
                messages.append({
                    "role": "assistant",
                    "content": response.content
                })
                
                # Append tool result
                messages.append({
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": tool_use.id,
                            "content": search_results
                        }
                    ]
                })
                
                # Call Claude again with the search results
                response = client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=2000,
                    system=SYSTEM_PROMPT,
                    messages=messages,
                    tools=tools,
                )
        
        # The final response should be text
        final_text = next((block.text for block in response.content if block.type == "text"), "{}")
        
        # Validate that it's JSON
        try:
            parsed_json = json.loads(final_text)
            return parsed_json
        except json.JSONDecodeError:
            # If Claude wraps it in markdown block, extract it
            if "```json" in final_text:
                json_str = final_text.split("```json")[1].split("```")[0].strip()
                return json.loads(json_str)
            return {"error": "Claude did not return valid JSON.", "raw_response": final_text}

    except Exception as e:
        print(f"Claude API Error: {e}")
        return {"error": str(e)}
