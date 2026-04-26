import json
import random
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict

from core.tournament import AgentConfig, run_match, MatchRecord
from core.llm_client import LLMClient

@dataclass
class BracketMatch:
    match_id: str
    team_a: Optional[str]
    team_b: Optional[str]
    winner: Optional[str] = None
    status: str = "pending" # pending, running, finished
    result: Optional[dict] = None

class BracketEngine:
    def __init__(self, agents_dir: str = "agentes"):
        self.agents_dir = Path(agents_dir)
        self.all_agents = self._discover_agents()
        self.matches: Dict[str, BracketMatch] = {}
        self.state_file = Path("logs/bracket_state.json")
        self.is_running = False # Global lock for match execution
        
    def _discover_agents(self) -> List[AgentConfig]:
        agents = []
        for d in self.agents_dir.iterdir():
            if d.is_dir():
                md = d / "agent.md"
                almacen = list(d.glob("almacen_*.md"))
                if md.exists() and almacen:
                    agents.append(AgentConfig(name=d.name, agent_md_path=md, almacen_path=almacen[0]))
        return agents

    def setup_tournament(self, seed_agents: List[str] = None):
        """Initializes the 8-team bracket."""
        if seed_agents:
            selected = [a for a in self.all_agents if a.name in seed_agents]
        else:
            selected = random.sample(self.all_agents, min(len(self.all_agents), 8))
        
        random.shuffle(selected)
        
        # Quarter Finals
        self.matches = {
            "q1": BracketMatch("q1", selected[0].name, selected[1].name),
            "q2": BracketMatch("q2", selected[2].name, selected[3].name),
            "q3": BracketMatch("q3", selected[4].name, selected[5].name),
            "q4": BracketMatch("q4", selected[6].name, selected[7].name),
            # Semis
            "s1": BracketMatch("s1", None, None),
            "s2": BracketMatch("s2", None, None),
            # Final
            "f1": BracketMatch("f1", None, None)
        }
        self.save_state()

    def save_state(self):
        state = {mid: asdict(m) for mid, m in self.matches.items()}
        self.state_file.parent.mkdir(exist_ok=True)
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)

    def load_state(self):
        if self.state_file.exists():
            with open(self.state_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.matches = {mid: BracketMatch(**m) for mid, m in data.items()}

    def get_match_config(self, team_name: str) -> AgentConfig:
        for a in self.all_agents:
            if a.name == team_name:
                return a
        return None

    def run_bracket_match(self, match_id: str, llm_client: LLMClient):
        match = self.matches.get(match_id)
        if not match or not match.team_a or not match.team_b or match.status == "finished":
            return
        
        if self.is_running:
            print(f"Match {match_id} ignored: another match is currently running.")
            return

        self.is_running = True
        match.status = "running"
        self.save_state()
        
        try:
            config_a = self.get_match_config(match.team_a)
            config_b = self.get_match_config(match.team_b)
            
            # Run the match using existing core logic
            record: MatchRecord = run_match(
                config_a, config_b, llm_client,
                visual=False, 
                export_json=True # This allows the dashboard to follow along
            )
            
            match.winner = record.winner if record.winner else "EMPATE"
            match.status = "finished"
            match.result = asdict(record)
            
            self._advance_tournament(match_id, match.winner)
        finally:
            self.is_running = False
            self.save_state()

    def _advance_tournament(self, match_id: str, winner: str):
        if winner == "EMPATE":
            # Simple tie-break logic for bracket: pick random
            winner = random.choice([self.matches[match_id].team_a, self.matches[match_id].team_b])
            self.matches[match_id].winner = winner

        if match_id == "q1": self.matches["s1"].team_a = winner
        elif match_id == "q2": self.matches["s1"].team_b = winner
        elif match_id == "q3": self.matches["s2"].team_a = winner
        elif match_id == "q4": self.matches["s2"].team_b = winner
        elif match_id == "s1": self.matches["f1"].team_a = winner
        elif match_id == "s2": self.matches["f1"].team_b = winner
