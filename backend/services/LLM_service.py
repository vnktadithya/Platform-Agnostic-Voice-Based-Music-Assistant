# services/LLM_service.py
import os
import requests
import json
from dotenv import load_dotenv
import logging

load_dotenv()
logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def call_gemini_agent(user_text: str, short_reply: bool = True, action_keys: list = []) -> dict:
    """
    Calls the Gemini API to understand user intent for the music assistant.
    """
    prompt = """You are Sam, a world-class conversational music assistant.
Your primary job is to understand the user's request and decompose it into the necessary sequence of actions and their parameters.

Instructions:
1. **Analyze the user's request:** Parse and split the request into one or more music-related actions if multiple tasks are stated (e.g., "play X and add it to playlist Y").
2. **Choose Actions:** For each action needed, select from the `Available Actions` list. The order in the list should match the order of intent in the user's message.
3. **Extract Parameters:** For each action, identify the required parameters like `song_name`, `artist`, `playlist_name`, or `mood` where relevant.
⚠️ IMPORTANT SEMANTIC RULE:
- "Liked Songs" / "Liked Tracks" / "My Liked Songs" is NOT a playlist.
- If the user asks to play liked songs, you MUST use the action `play_liked_songs`.
- NEVER use `play_playlist_by_name` for liked songs.
- Do NOT treat "Liked Songs" as a playlist name.
4. **Handle Non-Music Talk:** If there is only small talk, ignore actions and return just a conversational `reply`.
5. **Handle Missing Information:** If any required parameter is missing for any action, return one follow-up slot-filling question as the top-level `reply`, and do NOT return the `actions` array.
6. **Use Conversation History:** If the user's current message refers to context from previous dialog, infer those as parameters for the respective action(s).
7. **JSON Output Only:** Always respond with ONLY a JSON object as shown below (no extra text, markdown, or commentary).

Respond in this EXACT JSON format:
{
  "intent": "...",
  "emotion": "...",
  "actions": [
    {
      "action": "...",
      "parameters": { "...": "..." },
      "reply": "..." // (Optional, for intermediate or per-action messages)
    }
    // ... may have one or more actions in this array.
  ],
  "reply": "..." // Final reply for the user
}

Available Actions: """ + ", ".join(action_keys) + """

User said: """ f'"{user_text}"'


    # API endpoint and headers for Gemini
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"

    headers = {
        "Content-Type": "application/json"
    }

    # Request body format for Gemini 
    body = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ],
        # Added generation and safety settings for more reliable JSON output
        "generationConfig": {
            "responseMimeType": "application/json", # Highly recommended for forcing JSON output
            "temperature": 0.5,
        },
        "safetySettings": [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
        ]
    }

    try:
        resp = requests.post(url, headers=headers, json=body, timeout=60)
        resp.raise_for_status() 

        response_json = resp.json()
        
        # Check for content and parts before accessing them
        if not response_json.get("candidates") or not response_json["candidates"][0].get("content") or not response_json["candidates"][0]["content"].get("parts"):
            raise ValueError(f"Unexpected API response structure: {response_json}")
            
        content = response_json["candidates"][0]["content"]["parts"][0]["text"]
        
        return json.loads(content)

    except requests.exceptions.HTTPError as http_err:
        logger.error("LLM API HTTP error", exc_info=True)
        raise Exception(f"LLM API call failed with status {resp.status_code}")
    
    except (json.JSONDecodeError, ValueError, KeyError) as e:
        logger.error("Invalid or unexpected LLM response format", exc_info=True)
        raise Exception("Invalid model output. Expected valid JSON but failed to parse.")

    except Exception:
        logger.exception("Unexpected error during LLM call")
        raise
