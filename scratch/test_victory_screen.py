import json
from pathlib import Path

def trigger_test_victory():
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    dummy_state = {
        "turn": 42,
        "finished": True,
        "winner": "AS_LOGISTICA",
        "team_a": {
            "name": "AS_LOGISTICA",
            "pedidos_encajados": 4,
            "total_pedidos": 4,
            "prendas_encajadas": 12,
            "board": []
        },
        "team_b": {
            "name": "EJEMPLO",
            "pedidos_encajados": 2,
            "total_pedidos": 4,
            "prendas_encajadas": 8,
            "board": []
        },
        "comms": [],
        "telemetry": {
            "team_a": {"strategy": "Finalizada", "reasoning": "Victoria por aniquilación"},
            "team_b": {"strategy": "Finalizada", "reasoning": "Derrota táctica"}
        }
    }
    
    with open(log_dir / "game_state.json", "w", encoding="utf-8") as f:
        json.dump(dummy_state, f, indent=4, ensure_ascii=False)
    
    print("✅ Estado de VICTORIA inyectado en logs/game_state.json")
    print("Refresca el dashboard para ver la pantalla de fin de partida.")

if __name__ == "__main__":
    trigger_test_victory()
