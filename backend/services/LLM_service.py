# services/LLM_service.py
import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

# --- CHANGE 1: Use GEMINI_API_KEY instead of OPENROUTER_API_KEY ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# --- Renamed function for clarity ---
def call_gemini_agent(user_text: str, voice_emotion: str = None, short_reply: bool = True, action_keys: list = []) -> dict:
    """
    Calls the Gemini API to understand user intent for the music assistant.
    """
    # The prompt is slightly tweaked for better performance with Gemini
    prompt = """You are a world-class conversational music assistant.
Your primary job is to understand the user's request and decompose it into the necessary sequence of actions and their parameters.

Instructions:
1. **Analyze the user's request:** Parse and split the request into one or more music-related actions if multiple tasks are stated (e.g., "play X and add it to playlist Y").
2. **Choose Actions:** For each action needed, select from the `Available Actions` list. The order in the list should match the order of intent in the user's message.
3. **Extract Parameters:** For each action, identify the required parameters like `song_name`, `artist`, `playlist_name`, or `mood` where relevant.
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


    if voice_emotion:
        prompt += f'\nDetected voice emotion: {voice_emotion}'

    # --- CHANGE 2: API endpoint and headers for Gemini ---
    # This is the CORRECT line
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"

    headers = {
        "Content-Type": "application/json"
    }

    # --- CHANGE 3: Request body format for Gemini ---
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
        resp.raise_for_status() # This will raise an HTTPError for bad responses (4xx or 5xx)

        # --- CHANGE 4: How the response content is parsed ---
        # The raw text is located in a different path in the Gemini response
        response_json = resp.json()
        
        # Check for content and parts before accessing them
        if not response_json.get("candidates") or not response_json["candidates"][0].get("content") or not response_json["candidates"][0]["content"].get("parts"):
            raise ValueError(f"Unexpected API response structure: {response_json}")
            
        content = response_json["candidates"][0]["content"]["parts"][0]["text"]
        
        # The JSON cleaning logic from your original code is still a good fallback,
        # but with Gemini's `responseMimeType`, it often returns perfect JSON directly.
        return json.loads(content)

    except requests.exceptions.HTTPError as http_err:
        # More specific error for API call failures
        print(f"HTTP error occurred: {http_err}")
        print(f"Response body: {resp.text}")
        raise Exception(f"LLM API call failed with status {resp.status_code}")
    except (json.JSONDecodeError, ValueError, KeyError) as e:
        # Catches errors from parsing the JSON or if the response structure is wrong
        print(f"LLM raw output was not valid or as expected. Error: {e}")
        # It's helpful to log what the model actually returned for debugging
        if 'resp' in locals():
            print(f"Raw response from API: {resp.text}")
        raise Exception("Invalid model output. Expected valid JSON but failed to parse.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        raise