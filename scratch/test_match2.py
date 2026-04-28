import sys
from core.bracket_engine import BracketEngine
from core.llm_client import OfflineLLMClient

def debug():
    try:
        engine = BracketEngine()
        engine.load_state()

        match_id = "q1"
        print(f"Probando partida {match_id}...")

        client = OfflineLLMClient(board_size=6)
        engine.run_bracket_match(match_id, client)
        
        print("Fin exitoso")
    except Exception as e:
        print(f"Excepcion capturada: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug()
