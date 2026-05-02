from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List
from core.engine import Board, AlmacenParser

@dataclass
class AgentConfig:
    name: str
    agent_md_path: Path
    almacen_path: Path

    def load_agent_md(self) -> str:
        return self.agent_md_path.read_text(encoding="utf-8")

    def load_board(self, size: int = 10, ship_sizes: list[int] | None = None) -> Board:
        ships = AlmacenParser.parse(self.almacen_path, size=size, ship_sizes=ship_sizes)
        return Board(size=size, ships=ships, ship_sizes=ship_sizes)

@dataclass
class MatchRecord:
    agent_a: str
    agent_b: str
    winner: Optional[str]
    total_turns: int
    shots_a: int
    shots_b: int
    hits_a: int = 0
    hits_b: int = 0
    already_shot_a: int = 0   
    already_shot_b: int = 0   
    avg_latency_a: float = 0.0
    avg_latency_b: float = 0.0
    prompt_tokens_a: int = 0
    completion_tokens_a: int = 0
    prompt_tokens_b: int = 0
    completion_tokens_b: int = 0
    errors_a: int = 0
    errors_b: int = 0
    win_reason: str = "Aniquilación"
