import os
from dotenv import load_dotenv
import litellm

def test_deepseek():
    load_dotenv(override=True)
    messages = [{"role": "user", "content": "Hola, ¿puedes leerme?"}]
    
    models = ["deepseek/deepseek-chat", "deepseek/deepseek-v4-flash"]
    
    for model in models:
        print(f"Testing model: {model}...")
        try:
            response = litellm.completion(model=model, messages=messages)
            print(f"SUCCESS ({model}):", response.choices[0].message.content)
        except Exception as e:
            print(f"FAILED ({model}):", type(e).__name__, "-", e)
        print("-" * 40)

if __name__ == "__main__":
    test_deepseek()
