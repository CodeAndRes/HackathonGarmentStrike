import os
from dotenv import load_dotenv
import litellm

def test_groq():
    load_dotenv(override=True)
    messages = [{"role": "user", "content": "Say hello"}]
    try:
        response = litellm.completion(model="groq/llama-3.1-8b-instant", messages=messages)
        print("Groq works:", response.choices[0].message.content)
    except Exception as e:
        print("Groq failed:", e)

if __name__ == "__main__":
    test_groq()
