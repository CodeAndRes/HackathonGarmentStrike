#!/usr/bin/env python3
"""
verbose_match.py - Partida con salida de texto en VIVO
"""
import sys
from pathlib import Path
from core.llm_client import LLMClient
from core.engine import Game, AlmacenParser
from core.tournament import AgentConfig

print("[MATCH] Alpha vs Beta - Modo Verbose (texto en vivo)")
print()

# Load configs
config_a = AgentConfig(
    name="Alpha",
    agent_md_path=Path("agentes/ejemplo/agent.md"),
    almacen_path=Path("agentes/ejemplo/almacen_equipo_ejemplo.md"),
)
config_b = AgentConfig(
    name="Beta",
    agent_md_path=Path("agentes/ejemplo/agent.md"),
    almacen_path=Path("agentes/ejemplo/almacen_equipo_ejemplo2.md"),
)

board_a = config_a.load_board()
board_b = config_b.load_board()
agent_md_a = config_a.load_agent_md()
agent_md_b = config_b.load_agent_md()

game = Game("Alpha", board_a, "Beta", board_b)
llm_client = LLMClient(model="ollama/phi3:mini", max_retries=1, quick_mode=True)
agent_mds = {"Alpha": agent_md_a, "Beta": agent_md_b}
wasted = {"Alpha": 0, "Beta": 0}
move_log = []

turn = 0
max_turns = 120

print(f"[Inicio de la partida - Modelo: Phi3 Mini (Ollama)]\n")
sys.stdout.flush()

while True:
    turn += 1
    finished, winner = game.is_over()
    if finished:
        break
    if turn > max_turns:
        print(f"[MAX TURNS] Alcanzado limite de 120 turnos")
        break

    current = game.current_agent
    opponent = game.opponent
    opponent_board = game.agents[opponent]  # tablero del rival que estamos atacando
    
    print(f"[T{turn:>3}] {current:>5} pensando...", end=" ", flush=True)
    sys.stdout.flush()
    
    if llm_client.quick_mode:
        opponent_board_text = opponent_board.grid_text_minimal()
    else:
        opponent_board_text = opponent_board.grid_text(reveal_ships=False)
    move_history = []  # Simplificado
    
    try:
        agent_move = llm_client.get_move(
            agent_md=agent_mds[current],
            opponent_board_text=opponent_board_text,
            move_history=move_history,
            my_name=current,
            opponent_name=opponent,
        )
        coord = agent_move.coordenada
        razonamiento = agent_move.razonamiento
        estrategia = agent_move.estrategia_aplicada
        latencia = agent_move.latency_ms
    except Exception as e:
        print(f"ERROR: {e}")
        sys.stdout.flush()
        break
    
    # Apply move
    col = coord[0]
    row = int(coord[1:])
    result = game.apply_move(col, row, razonamiento, estrategia)
    
    # Log
    move_log.append({
        "turn": turn,
        "agent": current,
        "coord": coord,
        "result": result
    })
    
    # Print turn result
    status = result.upper()
    lat_str = f"{latencia/1000.0:.2f}s" if latencia else "N/A"
    print(f"-> {coord:>2}  | {status:<8} | ⏱ {lat_str}")
    sys.stdout.flush()
    
    # Check if hit/sunk to decide turn switch
    if result not in ("hit", "sunk"):
        game.switch_turn()

print()
print("=" * 50)
print("[RESULTADO FINAL]")
print("=" * 50)
finished, winner = game.is_over()
print(f"Ganador:      {winner or 'EMPATE'}")
print(f"Turnos:       {turn}")
print(f"Total movimientos: {len(move_log)}")
print("=" * 50)
sys.stdout.flush()
