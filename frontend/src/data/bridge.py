import json
from pathlib import Path

# Configuración de Integración
INTEGRATION_CONFIG = {
    "live_mode": True,  
    "state_path": Path("../logs/game_state.json"),
}

def get_game_state():
    """Definición maestra de barcos y estados."""
    
    if INTEGRATION_CONFIG["live_mode"] and INTEGRATION_CONFIG["state_path"].exists():
        try:
            with open(INTEGRATION_CONFIG["state_path"], "r", encoding="utf-8") as f:
                data = json.load(f)
                
                # Convertir las claves de string "r,c" a tuplas (r,c) para la compatibilidad con el dashboard
                for team in ["team_a", "team_b"]:
                    if team in data and "fleet" in data[team]:
                        new_fleet = {}
                        for coord_str, ship_id in data[team]["fleet"].items():
                            r, c = map(int, coord_str.split(","))
                            new_fleet[(r, c)] = ship_id
                        data[team]["fleet"] = new_fleet
                        
                return data
        except Exception:
            pass # Fallback silencioso al mock si el JSON está corrupto/bloqueado
            
    def create_fleet(ship_definitions):
        fleet = {}
        for start_coord, size, direction, ship_id in ship_definitions:
            r, c = start_coord
            for i in range(size):
                fleet[(r + (i if direction == "V" else 0), c + (i if direction == "H" else 0))] = ship_id
        return fleet

    # 💠 ALPHA FLEET DEFINITION
    fleet_a = create_fleet([
        ((2, 2), 3, "H", "ALPHA_S1"), # 3C-E
        ((4, 1), 2, "H", "ALPHA_S2"), # 5B-C
        ((6, 3), 3, "H", "ALPHA_S3"), # 7D-F (Pegado a A2)
        ((4, 6), 3, "V", "ALPHA_S4"), # G5-7 (Pegado a A1)
    ])

    # 💠 BETA FLEET DEFINITION
    fleet_b = create_fleet([
        ((1, 1), 2, "H", "BETA_S1"),  # 2B-C (X-X)
        ((3, 4), 4, "H", "BETA_S2"),  # 4E-H (###X)
        ((6, 0), 2, "H", "BETA_S3"),  # 7A-B (##)
        ((6, 4), 2, "V", "BETA_S4"),  # E7-8 (X-X)
    ])
    
    return {
        "turn": 14,
        "team_a": {
            "name": "ALPHA CORE",
            "pedidos_encajados": 3,
            "total_pedidos": 5,
            "prendas_encajadas": 12,
            "fleet": fleet_a,
            "board": [
                ["~", "~", "~", "~", "~", "~", "~", "~", "~", "~"],
                ["~", "O", "~", "~", "~", "~", "~", "~", "~", "~"],
                ["~", "~", "#", "#", "#", "~", "~", "~", "~", "~"],
                ["~", "~", "~", "~", "~", "~", "O", "~", "~", "~"],
                ["~", "#", "#", "~", "~", "~", "X", "~", "~", "~"],
                ["~", "~", "~", "~", "~", "~", "X", "~", "~", "~"],
                ["~", "~", "~", "X", "#", "#", "X", "~", "~", "~"],
                ["~", "~", "~", "~", "~", "~", "~", "~", "~", "O"],
                ["~", "~", "~", "~", "~", "~", "~", "~", "~", "~"],
                ["~", "~", "~", "~", "~", "~", "~", "~", "~", "~"]
             ]
        },
        "team_b": {
            "name": "BETA STRIKE",
            "pedidos_encajados": 2,
            "total_pedidos": 5,
            "prendas_encajadas": 9,
            "fleet": fleet_b,
            "board": [
                ["~", "~", "~", "~", "~", "~", "~", "~", "~", "~"],
                ["~", "X", "X", "~", "~", "~", "O", "~", "~", "~"],
                ["~", "~", "~", "~", "~", "~", "~", "~", "~", "~"],
                ["~", "~", "~", "~", "#", "X", "#", "X", "~", "~"],
                ["~", "O", "~", "~", "~", "~", "~", "~", "~", "~"],
                ["~", "~", "~", "~", "~", "~", "~", "~", "~", "~"],
                ["#", "#", "~", "~", "X", "O", "~", "~", "~", "~"],
                ["~", "~", "~", "~", "X", "~", "~", "~", "~", "~"],
                ["~", "~", "~", "~", "~", "~", "~", "~", "~", "~"],
                ["~", "~", "~", "~", "~", "~", "~", "~", "O", "~"]
            ]
        },
        "comms": [
            {"turn": 14, "agent": "ALPHA CORE", "coord": "G7", "result": "HIT", "icon": "📦", "reasoning": "Detected pattern in G-Sector."},
            {"turn": 13, "agent": "BETA STRIKE", "coord": "D2", "result": "MISS", "icon": "❔", "reasoning": "Random re-routing to obscure strategy."},
        ],
        "telemetry": {
            "team_a": {
                "strategy": "Contiguous Pattern Strike. Deploying systematic cross-sector scan to maximize hit probability in shortest timeframe.",
                "reasoning": "Analyzing high probability clusters in Sector Charlie. Executing strike on G7 based on heat-map distribution."
            },
            "team_b": {
                "strategy": "Randomized Evasion and Asymmetric Repositioning. Confusing the opponent by ignoring standard distribution paths.",
                "reasoning": "Detected strike pattern in Sector D. Re-routing shipments to Sector J to minimize log-jam risk."
            }
        }
    }
