# services/LLM_service.py
import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

def call_mistral_agent(user_text: str, voice_emotion: str = None, short_reply: bool = True, action_keys: list = []) -> dict:
    prompt = """You are a world-class conversational music assistant.
Your primary job is to understand the user's request and determine the appropriate action.

Instructions:
1.  **Analyze the user's request:** Understand what they want to do (e.g., play a song, create a playlist, get a recommendation).
2.  **Choose an Action:** If the request is a music-related command, you MUST choose exactly one action from the `Available Actions` list below.
3.  **Extract Parameters:** Identify any parameters like `song_name`, `artist`, `playlist_name`, or `mood`.
4.  **Handle Non-Music Talk:** If the user is just greeting, making small talk, or asking a non-music question, DO NOT return an `action`. Just provide a natural, conversational `reply`.
5.  **Handle Missing Information:** If a required parameter is missing (e.g., they ask to add a song to a playlist but don't name it), your `reply` should be a follow-up question asking for the missing detail.

Available Actions: """ + ", ".join(action_keys) + """

Respond in EXACTLY this JSON format. Do not add any extra text or explanations.
{
  "intent": "...",
  "emotion": "...",
  "action": "...",
  "parameters": { "...": "..." },
  "reply": "..."
}

User said: """ f'"{user_text}"'

    if voice_emotion:
        prompt += f'\nDetected voice emotion: {voice_emotion}'

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    body = {
        "model": "mistralai/mistral-7b-instruct",
        "messages": [{"role": "user", "content": prompt}]
    }

    resp = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=body)

    if resp.status_code != 200:
        raise Exception(f"LLM call error: {resp.text}")

    content = resp.json()["choices"][0]["message"]["content"]
    
    # Clean the response to ensure it's valid JSON
    try:
        # Find the start and end of the JSON object
        start = content.find('{')
        end = content.rfind('}') + 1
        if start != -1 and end != 0:
            json_str = content[start:end]
            return json.loads(json_str)
        else:
            raise ValueError("No JSON object found in the response")
    except (json.JSONDecodeError, ValueError) as e:
        print(f"LLM raw output was not valid JSON: {content}")
        raise Exception(f"Invalid model output. Expected valid JSON but got an error: {e}")