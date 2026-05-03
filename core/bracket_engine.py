import json
import random
import os
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict

from core.models import AgentConfig, MatchRecord
from core.tournament import run_match
from core.llm_client import LLMClient

@dataclass
class BracketMatch:
    match_id: str
    team_a: Optional[str]
    team_b: Optional[str]
    winner: Optional[str] = None
    status: str = "pending" # pending, running, finished, error
    result: Optional[dict] = None

class BracketEngine:
    """
    STRICT TOURNAMENT ENGINE
    Rules:
    1. Agents must be in subfolders: agentes/{TeamName}/
    2. Each subfolder must contain 'agent.md' and 'almacen.md'.
    3. Tournament state is strictly persisted in 'bracket_state.json'.
    """
    def __init__(self, tournament_dir: str):
        self.tournament_dir = Path(tournament_dir)
        self.agents_dir = self.tournament_dir / "agentes"
        self.state_file = self.tournament_dir / "bracket_state.json"
        self.matches: Dict[str, BracketMatch] = {}
        self.is_running = False 
        
        # Initial load
        self.all_agents = self._discover_agents()
        self.load_state()

    def _discover_agents(self) -> List[AgentConfig]:
        """STRICT DISCOVERY: Only accepts folder-based agents with agent.md and almacen.md."""
        agents = []
        if not self.agents_dir.exists():
            return agents
            
        for team_folder in self.agents_dir.iterdir():
            if not team_folder.is_dir():
                continue
                
            agent_md = team_folder / "agent.md"
            almacen_md = team_folder / "almacen.md"
            
            if agent_md.exists() and almacen_md.exists():
                agents.append(AgentConfig(
                    name=team_folder.name, 
                    agent_md_path=agent_md, 
                    almacen_path=almacen_md
                ))
        return agents

    def setup_tournament(self, count: int = 8, seed_agents: List[str] = None):
        """Initializes a clean tournament bracket."""
        self.all_agents = self._discover_agents()
        
        if seed_agents:
            # Filter to only use the requested seeds
            selected = [a for a in self.all_agents if a.name in seed_agents]
            # If not found all seeds, use placeholders for missing ones
            while len(selected) < count:
                placeholder_name = f"Placeholder_{len(selected)+1}"
                selected.append(AgentConfig(name=placeholder_name, agent_md_path=Path(""), almacen_path=Path("")))
        elif len(self.all_agents) < count:
            # Fill with placeholders if not enough agents
            selected = self.all_agents[:]
            while len(selected) < count:
                placeholder_name = f"Placeholder_{len(selected)+1}"
                selected.append(AgentConfig(name=placeholder_name, agent_md_path=Path(""), almacen_path=Path("")))
        else:
            selected = random.sample(self.all_agents, count)
        
        random.shuffle(selected)
        self.matches = {}

        def get_name(idx):
            return selected[idx].name

        if count == 8:
            self.matches.update({
                "q1": BracketMatch("q1", get_name(0), get_name(1)),
                "q2": BracketMatch("q2", get_name(2), get_name(3)),
                "q3": BracketMatch("q3", get_name(4), get_name(5)),
                "q4": BracketMatch("q4", get_name(6), get_name(7)),
                "s1": BracketMatch("s1", None, None),
                "s2": BracketMatch("s2", None, None),
                "f1": BracketMatch("f1", None, None)
            })
        elif count == 4:
            self.matches.update({
                "s1": BracketMatch("s1", get_name(0), get_name(1)),
                "s2": BracketMatch("s2", get_name(2), get_name(3)),
                "f1": BracketMatch("f1", None, None)
            })
        else:
            self.matches.update({
                "f1": BracketMatch("f1", get_name(0), get_name(1))
            })
            
        self.save_state()

    def save_state(self):
        state = {mid: asdict(m) for mid, m in self.matches.items()}
        self.tournament_dir.mkdir(exist_ok=True, parents=True)
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)

    def load_state(self):
        if self.state_file.exists():
            with open(self.state_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.matches = {mid: BracketMatch(**m) for mid, m in data.items()}
                self.sanitize_state()

    def sanitize_state(self):
        """Clean up stale 'running' states on startup."""
        changed = False
        for mid, match in self.matches.items():
            if match.status == "running":
                match.status = "pending"
                changed = True
        if changed:
            self.save_state()

    def get_agent_config(self, team_name: str) -> Optional[AgentConfig]:
        return next((a for a in self.all_agents if a.name == team_name), None)

    def run_bracket_match(self, match_id: str, llm_client: LLMClient):
        """STRICT EXECUTION: Locks the engine and runs a single match."""
        match = self.matches.get(match_id)
        if not match or not match.team_a or not match.team_b or match.status != "pending":
            return
        
        if self.is_running:
            return
        
        self.is_running = True
        match.status = "running"
        self.save_state()
        
        try:
            config_a = self.get_agent_config(match.team_a)
            config_b = self.get_agent_config(match.team_b)
            
            if not config_a or not config_b or not config_a.agent_md_path.exists():
                raise ValueError(f"Missing agent files for {match.team_a} or {match.team_b}")

            phase = match_id[0] # q, s, f
            
            # Phase-specific file resolution (STRICT)
            def resolve_phase_files(cfg: AgentConfig, phase: str):
                p_agent = cfg.agent_md_path.parent / f"agent.{phase}.md"
                p_almacen = cfg.almacen_path.parent / f"almacen.{phase}.md"
                if p_agent.exists(): cfg.agent_md_path = p_agent
                if p_almacen.exists(): cfg.almacen_path = p_almacen

            resolve_phase_files(config_a, phase)
            resolve_phase_files(config_b, phase)
            
            # Load rules from settings
            import yaml
            with open("settings.yaml", "r", encoding="utf-8") as f:
                settings = yaml.safe_load(f) or {}
                rules = settings.get("tournament", {}).get("rounds", {}).get(phase, {})

            board_size = rules.get("board_size", 10)
            max_turns = rules.get("max_turns", 50)
            ship_sizes = rules.get("ship_sizes", [5, 4, 3, 3, 2])
            
            llm_client.board_size = board_size
            
            record: MatchRecord = run_match(
                config_a, config_b, llm_client,
                visual=False, export_json=True,
                board_size=board_size, max_turns=max_turns, ship_sizes=ship_sizes,
                output_dir=self.tournament_dir
            )
            
            match.winner = record.winner if record.winner else "EMPATE"
            match.status = "finished"
            match.result = asdict(record)
            
            self._advance_tournament(match_id, match.winner)
            
        except Exception as e:
            print(f"Match {match_id} Error: {e}")
            match.status = "error"
        finally:
            self.is_running = False
            self.save_state()

    def _advance_tournament(self, match_id: str, winner: str):
        if winner == "EMPATE":
            winner = random.choice([self.matches[match_id].team_a, self.matches[match_id].team_b])
            self.matches[match_id].winner = winner

        advancements = {
            "q1": ("s1", "team_a"), "q2": ("s1", "team_b"),
            "q3": ("s2", "team_a"), "q4": ("s2", "team_b"),
            "s1": ("f1", "team_a"), "s2": ("f1", "team_b")
        }
        if match_id in advancements:
            next_id, slot = advancements[match_id]
            setattr(self.matches[next_id], slot, winner)

    def validate_teams(self, phase: str = 'q') -> dict:
        from core.validator import AgentValidator
        import yaml
        
        with open("settings.yaml", "r", encoding="utf-8") as f:
            rules = yaml.safe_load(f).get("tournament", {}).get("rounds", {}).get(phase, {})

        validator = AgentValidator()
        results = {}
        
        active_teams = set()
        for mid, m in self.matches.items():
            if mid.startswith(phase):
                if m.team_a: active_teams.add(m.team_a)
                if m.team_b: active_teams.add(m.team_b)
        
        for agent_name in active_teams:
            cfg = self.get_agent_config(agent_name)
            if not cfg: continue
            
            # Local copy for phase-specific validation
            from copy import copy
            v_cfg = copy(cfg)
            
            p_agent = v_cfg.agent_md_path.parent / f"agent.{phase}.md"
            p_almacen = v_cfg.almacen_path.parent / f"almacen.{phase}.md"
            if p_agent.exists(): v_cfg.agent_md_path = p_agent
            if p_almacen.exists(): v_cfg.almacen_path = p_almacen

            res = validator.validate(v_cfg, rules.get("board_size", 10), rules.get("ship_sizes", [5,4,3,3,2]))
            results[agent_name] = {
                "is_valid": res.is_valid,
                "errors": res.errors,
                "word_count": res.word_count,
                "ship_sizes": res.ship_sizes,
                "almacen_usado": v_cfg.almacen_path.name
            }
        return results
