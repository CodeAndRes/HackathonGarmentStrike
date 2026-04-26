import asyncio
import json
import random
import threading
import time
import sys
import os
from pathlib import Path

# Añadir la raíz del proyecto al path para encontrar 'core'
sys.path.append(str(Path(__file__).parent.parent))

from core.api import app, state, start_api_server

def generate_mock_state():
    """Genera un estado de juego con todas las combinaciones posibles."""
    board_a = [["~"] * 10 for _ in range(10)]
    board_b = [["~"] * 10 for _ in range(10)]
    
    fleet_a = {}
    fleet_b = {}
    
    # --- EQUIPO ALPHA: MUESTRA DE ESTADOS ---
    # 1. Pedido Inicial (Vacío) - Sector A1
    board_a[0][0] = "#"; board_a[0][1] = "#"
    fleet_a["0,0"] = "ORD_1"; fleet_a["0,1"] = "ORD_1"

    # 2. Pedido a Medio Llenar (Hits) - Sector C3
    board_a[2][2] = "#"; board_a[2][3] = "X"
    fleet_a["2,2"] = "ORD_2"; fleet_a["2,3"] = "ORD_2"

    # 3. Pedido Completado (Sunk/Sealed) - Sector F6
    board_a[5][5] = "X"; board_a[5][6] = "X"
    fleet_a["5,5"] = "ORD_3"; fleet_a["5,6"] = "ORD_3"

    # 4. Fallos (Agua)
    board_a[1][5] = "O"; board_a[8][2] = "❔"

    # --- EQUIPO BETA: MUESTRA DE ATAQUE ---
    # 1. Pedido vertical a medio llenar (Sector B5)
    board_b[4][1] = "#"; board_b[5][1] = "X"; board_b[6][1] = "#"
    fleet_b["4,1"] = "ORD_B1"; fleet_b["5,1"] = "ORD_B1"; fleet_b["6,1"] = "ORD_B1"

    # 2. Pedido Horizontal COMPLETADO (Sunk) - Sector G2
    board_b[1][6] = "X"; board_b[1][7] = "X"
    fleet_b["1,6"] = "ORD_B2"; fleet_b["1,7"] = "ORD_B2"

    # 3. Pedido en "L" (Conexiones mixtas) - Sector D8
    board_b[7][3] = "#"; board_b[8][3] = "X"; board_b[8][4] = "#"
    fleet_b["7,3"] = "ORD_B3"; fleet_b["8,3"] = "ORD_B3"; fleet_b["8,4"] = "ORD_B3"

    # 4. Mezcla de fallos y escaneos
    for r in range(0, 3): board_b[r][8] = "O"
    board_b[9][9] = "❔"; board_b[0][9] = "O"

    return {
        "turn": random.randint(1, 100),
        "turn_agent": random.choice(["team_a", "team_b"]),
        "team_a": {
            "name": "AS_LOGISTICA",
            "pedidos_encajados": 1,
            "total_pedidos": 4,
            "prendas_encajadas": 5,
            "board": board_a,
            "fleet": fleet_a,
            "sunk_ships": ["ORD_3"]
        },
        "team_b": {
            "name": "BETA_STRIKE",
            "pedidos_encajados": 1,
            "total_pedidos": 4,
            "prendas_encajadas": 3,
            "board": board_b,
            "fleet": fleet_b,
            "sunk_ships": ["ORD_B2"]
        },
        "comms": [
            {"turn": 45, "agent": "B", "coord": "B6", "result": "HIT", "icon": "🎯", "reasoning": "Impacto confirmado en logística enemiga."},
            {"turn": 46, "agent": "A", "coord": "I1", "result": "MISS", "icon": "💦", "reasoning": "Sector vacío detectado."},
            {"turn": 47, "agent": "A", "coord": "F6", "result": "SUNK", "icon": "📦", "reasoning": "PEDIDO ORD_3 COMPLETADO."}
        ],
        "telemetry": {
            "team_a": {
                "strategy": "DEFENSA ELÁSTICA",
                "reasoning": "Priorizando el sellado de los pedidos más cercanos a completarse.",
                "cursor": "focus"
            },
            "team_b": {
                "strategy": "ATAQUE SISTEMÁTICO",
                "reasoning": "Barriendo cuadrantes B y C en busca de almacenes ocultos.",
                "cursor": "aiming",
                "target": "B5"
            }
        },
        "finished": False
    }

async def push_mock_data():
    """Bucle que envía datos cada 2 segundos."""
    print("[LOG] Enviando datos de prueba al Dashboard...")
    while True:
        mock_state = generate_mock_state()
        await state.broadcast(mock_state)
        await asyncio.sleep(2)

if __name__ == "__main__":
    # 1. Lanzamos el servidor en un hilo aparte
    server_thread = threading.Thread(target=start_api_server, kwargs={"port": 8000}, daemon=True)
    server_thread.start()
    
    # 2. Esperamos un poco a que el servidor arranque
    time.sleep(2)
    print("\n[OK] Servidor de depuracion listo en http://127.0.0.1:8000")
    
    # 3. Iniciamos el bucle de datos en el hilo principal
    asyncio.run(push_mock_data())
