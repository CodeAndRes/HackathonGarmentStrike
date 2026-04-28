import asyncio
import sys
from core.bracket_engine import BracketEngine
from core.llm_client import OfflineLLMClient

engine = BracketEngine()
engine.load_state()

match_id = "q1"
print(f"Probando partida {match_id}...")

client = OfflineLLMClient(board_size=6)
engine.run_bracket_match(match_id, client)

engine.load_state()
m = engine.matches[match_id]
print(f"Estado final: {m.status}")
print(f"Ganador: {m.winner}")
