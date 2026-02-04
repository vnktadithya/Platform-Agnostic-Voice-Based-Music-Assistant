# services/LLM_service.py
import os
import requests
import json
from dotenv import load_dotenv
import logging
from backend.utils.action_params import ACTION_REQUIRED_PARAMS

load_dotenv()
logger = logging.getLogger(__name__)
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

def call_llm_agent(user_text: str, short_reply: bool = True, action_keys: list = []) -> dict:
    """
    Calls the Groq API (Llama 3.3 70B) to understand user intent for the music assistant.
    """
    if not GROQ_API_KEY:
         raise ValueError("GROQ_API_KEY is missing. Please ensure it is set in your .env file.")
    
    available_actions_list = []
    for action in action_keys:
        required = ACTION_REQUIRED_PARAMS.get(action, [])
        if required:
            formatted = f"{action}({', '.join(required)})"
        else:
            formatted = action
        available_actions_list.append(formatted)

    available_actions_prompt = ", ".join(available_actions_list)

    # Construct System Prompt
    prompt = f"""You are SAM(Self-Adaptive Music Assistant), a world-class conversational music assistant.
Your primary job is to understand the user's request and decompose it into the necessary sequence of actions and their parameters.
Instructions:
1. **Analyze the user's request:** Parse and split the request into one or more music-related actions if multiple tasks are stated (e.g., "play X and add it to playlist Y").
2. **Choose Actions:** For each action needed, select from the `Available Actions` list. The order in the list should match the order of intent in the user's message.
3. **Extract Parameters:** For each action, identify the required parameters like `song_name`, `artist`, `playlist_name`, or `mood` where relevant.
    - **skip_time(seconds):** If the user says "skip 20s" or "jump 30 seconds", you MUST extract the integer value into `seconds`.
    - **change_volume(volume, mode):** 
      - `mode` must be one of: "absolute", "increase", "decrease".
      - `volume`: Integer (0-100) or null.
      - **Extraction Rules**:
        - **Absolute ("to", "set", "limit"):**
          - "set volume **to** 60" → `volume: 60, mode: "absolute"`
          - "change volume **to** 30" → `volume: 30, mode: "absolute"`
          - "volume 50" (implicit set) → `volume: 50, mode: "absolute"`
          - "mute" → `volume: 0, mode: "absolute"`
          - "max volume" → `volume: 100, mode: "absolute"`
        - **Relative ("by", "up", "down", "louder", "quieter"):**
          - "increase **by** 20" → `volume: 20, mode: "increase"`
          - "lower **by** 10" → `volume: 10, mode: "decrease"`
          - "volume up" / "louder" (no number) → `volume: null, mode: "increase"`
          - "volume down" / "quieter" (no number) → `volume: null, mode: "decrease"`

⚠️ IMPORTANT SEMANTIC RULE:
- "Liked Songs" / "Liked Tracks" / "My Liked Songs" is NOT a playlist.
- If the user asks to play liked songs, you MUST use the action `play_liked_songs`.
- NEVER use `play_playlist_by_name` for liked songs.
- Do NOT treat "Liked Songs" as a playlist name.
4. **Handle Non-Music Talk:** If there is only small talk, ignore actions and return just a conversational `reply`.
5. **Use Conversation History:** If the user's current message refers to context from previous dialog (e.g., "add this to...", "play it again", "remove that"), you MUST first check the conversation history to infer the missing parameters. Use pronouns like "this", "that", "it" as strong signals to reference the most recent song, playlist, or artist from prior turns.
   
   **Example:**
   - Turn 1: user: "play Blinding Lights" → assistant: "Now playing Blinding Lights" (you extract song_name: "Blinding Lights")
   - Turn 2: user: "add this to my workout playlist" → You MUST recognize "this" refers to "Blinding Lights" from Turn 1, so extract: {{song_name: "Blinding Lights", playlist_name: "workout"}}. DO NOT ask "which song?" because you already know from history.

6. **Handle Missing Information:** If a required parameter is still missing AFTER checking conversation history, return one follow-up slot-filling question as the top-level `reply`, and do NOT return the `actions` array. Only ask questions when you genuinely cannot infer the information from context.
7. **JSON Output Only:** Always respond with ONLY a JSON object as shown below (no extra text, markdown, or commentary).
Respond in this EXACT JSON format:
{{
  "intent": "...",
  "emotion": "...",
  "actions": [
    {{
      "action": "...",
      "parameters": {{ "...": "..." }},
      "reply": "..." // (Optional, for intermediate or per-action messages)
    }}
    // ... may have one or more actions in this array.
  ],
  "reply": "..." // Final reply for the user
}}
Available Actions: {available_actions_prompt}

""" + user_text  # user_text contains "Conversation so far: ... User now: ..." from dialog_manager

    # Groq OpenAI-compatible endpoint
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    # Request body
    body = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful assistant that outputs strictly in JSON format." 
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.3,
        "max_tokens": 1024
    }
    try:
        resp = requests.post(url, headers=headers, json=body, timeout=60)
        
        if resp.status_code != 200:
             logger.error(f"LLM API Error: {resp.text}")
             raise Exception(f"LLM API call failed with status {resp.status_code}: {resp.text}")
        response_json = resp.json()
        
        # Extract content from Groq response
        content = response_json["choices"][0]["message"]["content"]
        
        # Parse JSON
        result = json.loads(content)
        
        if not isinstance(result, dict):
            logger.error(f"LLM returned non-dict JSON: {result}")
            return {
                "intent": "error",
                "actions": [],
                "reply": "I'm having trouble processing that request."
            }
            
        return result
    except (json.JSONDecodeError, KeyError) as e:
        logger.error("Invalid or unexpected LLM response format", exc_info=True)
        # Fallback logging
        logger.error(f"Raw content received: {content if 'content' in locals() else 'None'}")
        raise Exception("Invalid model output. Expected valid JSON but failed to parse.")
    except Exception as e:
        logger.exception("Unexpected error during LLM call")
        raise e