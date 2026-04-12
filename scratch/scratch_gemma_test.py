import os
from dotenv import load_dotenv
load_dotenv()
import litellm

os.environ['LITELLM_LOG'] = 'DEBUG'

model = "ollama/gemma4:e4b" # Using the user's specific gemma model

try:
    response = litellm.completion(
        model=model,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say Hello"}
        ],
    )
    print("="*40)
    print("RESPONSE:", response.choices[0].message.content)
except Exception as e:
    print("="*40)
    print("ERROR:", e)
