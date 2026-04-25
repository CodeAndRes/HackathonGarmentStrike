import os
import litellm
from dotenv import load_dotenv

def test_deepseek_chat_tokens():
    load_dotenv(override=True)
    messages = [
        {"role": "system", "content": "Battleship AI. 6x6 grid. Sink all ships. RULES: No re-shooting X/O cells. Valid: A-F, 1-6. JSON only. {\"coordenada\":\"E5\",\"razonamiento\":\"...\",\"estrategia_aplicada\":\"...\"}"},
        {"role": "user", "content": "Pick ONE valid coord (A-F, 1-6) not yet shot:"}
    ]
    
    print("Testing chat with max_tokens=120...")
    try:
        response = litellm.completion(model="deepseek/deepseek-chat", messages=messages, max_tokens=120)
        print("SUCCESS (chat 120):", repr(response.choices[0].message.content))
    except Exception as e:
        print("FAILED (chat 120):", type(e).__name__, "-", e)

if __name__ == "__main__":
    test_deepseek_chat_tokens()
