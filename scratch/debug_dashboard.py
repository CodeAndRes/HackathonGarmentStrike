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
    """Genera un estado de juego falso para probar el diseño."""
    # Un tablero de 10x10 con algunos barcos
    board_a = [["~"] * 10 for _ in range(10)]
    board_b = [["~"] * 10 for _ in range(10)]
    
    fleet_a = {}
    # Barco horizontal en 2,2
    for c in range(2, 5):
        board_a[2][c] = "#"
        fleet_a[f"2,{c}"] = "ORDER_1"
    # Barco vertical en 5,5
    for r in range(5, 8):
        board_a[r][5] = "X"
        fleet_a[f"{r},5"] = "ORDER_2"

    return {
        "turn": random.randint(1, 50),
        "turn_agent": random.choice(["team_a", "team_b"]),
        "team_a": {
            "name": "Alpha-Test",
            "pedidos_encajados": 1,
            "total_pedidos": 5,
            "prendas_encajadas": 12,
            "board": board_a,
            "fleet": fleet_a,
            "sunk_ships": ["ORDER_2"]
        },
        "team_b": {
            "name": "Beta-Mock",
            "pedidos_encajados": 2,
            "total_pedidos": 5,
            "prendas_encajadas": 18,
            "board": board_b,
            "fleet": {},
            "sunk_ships": []
        },
        "comms": [
            {"turn": 1, "agent": "A", "coord": "C3", "result": "HIT", "icon": "🎯", "reasoning": "Detectada debilidad en sector C3."},
            {"turn": 2, "agent": "B", "coord": "E5", "result": "MISS", "icon": "💦", "reasoning": "Escaneo fallido en cuadrante E5."},
            {"turn": 3, "agent": "A", "coord": "F5", "result": "SUNK", "icon": "📦", "reasoning": "Pedido ORDER_2 completado y sellado."}
        ],
        "telemetry": {
            "team_a": {
                "strategy": "OPTIMIZACIÓN DE CARGA",
                "reasoning": "Analizando patrones de distribución para maximizar el sellado de cajas en el sector norte.",
                "cursor": "aiming",
                "target": "B2"
            },
            "team_b": {
                "strategy": "BÚSQUEDA AGRESIVA",
                "reasoning": "El oponente ha sellado una caja. Priorizando interrupción de logística en zona central.",
                "cursor": "idle"
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
