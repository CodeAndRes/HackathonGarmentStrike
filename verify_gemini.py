
import os
import time
from dotenv import load_dotenv
from core.llm_client import LLMClient

load_dotenv()

def verify():
    print(f"[*] Verificando integracion con: {os.getenv('DEFAULT_MODEL')}")
    client = LLMClient(model=os.getenv("DEFAULT_MODEL"))
    
    agent_md = "Estrategia: Disparar siempre a la columna A."
    board_text = "CELDAS PROHIBIDAS (NO DISPARAR AQUÍ): Ninguna"
    
    print("[*] Enviando peticion a Gemini (esto tardara 5s por el sleep)...")
    try:
        move = client.get_move(
            agent_md=agent_md,
            opponent_board_text=board_text,
            move_history=[],
            my_name="TestAlpha",
            opponent_name="TestBeta"
        )
        print("SUCCESS!")
        print(f"   Coordenada: {move.coordenada}")
        print(f"   Razonamiento: {move.razonamiento}")
        print(f"   Estrategia: {move.estrategia_aplicada}")
    except Exception as e:
        print(f"FAILURE: {e}")

if __name__ == "__main__":
    verify()
