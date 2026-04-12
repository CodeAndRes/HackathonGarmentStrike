import os
import time
from dotenv import load_dotenv
load_dotenv()
import litellm

os.environ['LITELLM_LOG'] = 'DEBUG'

model = os.getenv("DEFAULT_MODEL")
if not model:
    model = "gemini/gemini-3-flash-preview"

my_name = "TestAlpha"
agent_md = "Estrategia: Disparar siempre a la columna A."
opponent_board_text = "CELDAS PROHIBIDAS (NO DISPARAR AQUÍ): Ninguna"

system_content = (
    f"Eres un estratega en 'Garment Strike'. Tablero 10x10 (A-J, 1-10).\n"
    f"ESTRATEGIA DEL EQUIPO {my_name}:\n{agent_md}\n\n"
    f"Responde SOLO con un JSON válido. Formato esperado:\n"
    f'{{"coordenada": "E5", "razonamiento": "analisis...", "estrategia_aplicada": "..."}}'
)

user_content = (
    f"ESTADO ACTUAL DEL TABLERO RIVAL:\n{opponent_board_text}\n\n"
    f"HISTORIAL DE LOS ULTIMOS MOVIMIENTOS:\n(Ningún movimiento previo)\n\n"
    f"Teniendo en cuenta el tablero y los movimientos previos (para NO repetirlos), ¿cuál es tu siguiente coordenada estratégica?"
)

messages = [
    {"role": "system", "content": system_content},
    {"role": "user", "content": user_content},
]

response = litellm.completion(
    model=model,
    messages=messages,
    max_tokens=300,
    temperature=0.2,
)
print("="*40)
print(response.choices[0].message.content)
