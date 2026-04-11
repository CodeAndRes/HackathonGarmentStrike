#!/usr/bin/env python3
"""
quick_match.py - Match simple sin Unicode para Windows
"""
import sys
from pathlib import Path
from core.llm_client import LLMClient
from core.tournament import AgentConfig, run_match

print("[MATCH] Iniciando Equipo Alpha vs Equipo Beta...")
print("[INFO] Modelo: ollama/llama3:latest (puede tardar 3-5 minutos)")
print()

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

llm_client = LLMClient(model="ollama/llama3:latest")
match = run_match(config_a, config_b, llm_client, visual=True)

print()
print("=" * 50)
print("[RESULTADO]")
print("=" * 50)
print(f"Ganador:      {match.winner or 'EMPATE'}")
print(f"Turnos:       {match.total_turns}")
print(f"Disparos Alpha: {match.shots_a}")
print(f"Disparos Beta:  {match.shots_b}")
print("=" * 50)
