import os
from dotenv import load_dotenv
load_dotenv()

import litellm

os.environ['LITELLM_LOG'] = 'DEBUG'

model = os.getenv("DEFAULT_MODEL")
if not model:
    model = "gemini/gemini-3-flash-preview"

response = litellm.completion(
    model=model,
    messages=[
        {"role": "system", "content": "eres un agente."},
        {"role": "user", "content": "di un numero random entre 1 y 100 y cuenta hasta 20."}
    ],
    max_tokens=300,
)
print("="*40)
print(response.choices[0].message.content)
