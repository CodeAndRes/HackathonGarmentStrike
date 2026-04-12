import os
from dotenv import load_dotenv
load_dotenv()
from core.llm_client import LLMClient

# Ensure UTF-8 for windows console print simulation
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

client = LLMClient(model="ollama/gemma4:e4b", max_retries=1)
client.max_tokens = None # Overwrite for test

system_content = "You are playing Battleship. Grid is 10x10. Respond ONLY with JSON: {'coordenada': 'A1', 'razonamiento': '...', 'estrategia_aplicada': '...'}"
user_content = "OPPONENT BOARD STATE: CELDAS PROHIBIDAS: A1, B2\nYOUR PREVIOUS SHOTS: None\nTarget?"

try:
    messages = [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_content}
    ]
    # We call build_messages normally to get real structure
    move = client.get_move(
        agent_md="Strategy: Random shot.",
        opponent_board_text="Grid empty.",
        move_history=[],
        my_name="Alpha",
        opponent_name="Beta"
    )
    print("SUCCESS:", move.coordenada)
except Exception as e:
    print("FAILED:", e)
