#!/usr/bin/env python3
"""
profile_engine.py - Perfila el motor de juego sin cuellos de botella de red.
"""
import cProfile
import pstats
from pathlib import Path
from core.tournament import AgentConfig, run_match
from core.llm_client import AgentMove
import random

class MockLLMClient:
    def __init__(self):
        self.quick_mode = True
        self.cols = list("ABCDEFGHIJ")

    def get_move(self, *args, **kwargs) -> AgentMove:
        col = random.choice(self.cols)
        row = random.randint(1, 10)
        coord = f"{col}{row}"
        return AgentMove(
            coordenada=coord,
            razonamiento="Mock move",
            estrategia_aplicada="Mock",
            latency_ms=0.5
        )

def main():
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
    mock_client = MockLLMClient()
    
    profiler = cProfile.Profile()
    profiler.enable()
    
    # Run 100 matches to collect solid profiling data
    for _ in range(100):
        run_match(config_a, config_b, mock_client, visual=False)
        
    profiler.disable()
    
    print("\n--- Top 20 funciones que consumen más CPU en el motor ---")
    stats = pstats.Stats(profiler).sort_stats('tottime')
    stats.print_stats(20)

if __name__ == "__main__":
    main()
