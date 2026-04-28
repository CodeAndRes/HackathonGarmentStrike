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
    def __init__(self, agents_dir: str = "torneo"):
        self.agents_dir = Path(agents_dir)
        self.all_agents = self._discover_agents()
        self.matches: Dict[str, BracketMatch] = {}
        self.state_file = Path("logs/bracket_state.json")
        self.is_running = False # Global lock for match execution
        
    def _discover_agents(self) -> List[AgentConfig]:
        agents = []
        if not self.agents_dir.exists():
            return agents
            
        for f in self.agents_dir.glob("*.md"):
            # Ignorar archivos .almacen.md
            if f.name.endswith(".almacen.md"):
                continue
                
            agent_name = f.stem
            almacen_path = self.agents_dir / f"{agent_name}.almacen.md"
            
            if almacen_path.exists():
                agents.append(AgentConfig(
                    name=agent_name, 
                    agent_md_path=f, 
                    almacen_path=almacen_path
                ))
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
            # Obtener configuraciones básicas
            base_a = self.get_match_config(match.team_a)
            base_b = self.get_match_config(match.team_b)
            
            # Crear copias locales para no contaminar otras rondas si modificamos el path
            from copy import copy
            config_a = copy(base_a)
            config_b = copy(base_b)
            
            # Determinar la fase para aplicar las reglas correctas
            phase = match_id[0] # 'q', 's', o 'f'
            
            # Selección adaptativa: busca archivos específicos de fase (.s.md, .f.md)
            for cfg in [config_a, config_b]:
                # Almacén: nombre.almacen.s.md
                phase_almacen = cfg.almacen_path.parent / f"{cfg.name}.almacen.{phase}.md"
                if phase_almacen.exists():
                    cfg.almacen_path = phase_almacen
                
                # Agente: nombre.s.md
                phase_agent = cfg.agent_md_path.parent / f"{cfg.name}.{phase}.md"
                if phase_agent.exists():
                    cfg.agent_md_path = phase_agent
            
            # Cargar settings para obtener las reglas de la ronda
            import yaml
            try:
                with open("settings.yaml", "r", encoding="utf-8") as f:
                    settings = yaml.safe_load(f) or {}
                    tournament_rules = settings.get("tournament", {}).get("rounds", {}).get(phase, {})
            except Exception:
                tournament_rules = {}

            board_size = tournament_rules.get("board_size", 10)
            max_turns = tournament_rules.get("max_turns", 50)
            ship_sizes = tournament_rules.get("ship_sizes", [5, 4, 3, 3, 2])
            
            # Actualizar el board_size del cliente para evitar coordenadas fuera de límites
            llm_client.board_size = board_size
            
            try:
                # Run the match using existing core logic
                record: MatchRecord = run_match(
                    config_a, config_b, llm_client,
                    visual=False, 
                    export_json=True, # This allows the dashboard to follow along
                    board_size=board_size,
                    max_turns=max_turns,
                    ship_sizes=ship_sizes
                )
                
                # Recargar la referencia por si load_state reemplazó los objetos en memoria
                current_match = self.matches.get(match_id)
                if current_match:
                    current_match.winner = record.winner if record.winner else "EMPATE"
                    current_match.status = "finished"
                    current_match.result = asdict(record)
                
                self._advance_tournament(match_id, record.winner if record.winner else "EMPATE")
            except Exception as match_exc:
                print(f"\n[CRITICAL ERROR] Match {match_id} crashed during run_match: {match_exc}")
                import traceback
                traceback.print_exc()
                # Marcar como error para no quedarse atascado en 'running'
                current_match = self.matches.get(match_id)
                if current_match:
                    current_match.status = "error"
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

    def validate_teams(self, phase: str = 'q') -> dict:
        """Valida todos los agentes participantes contra las reglas de una fase."""
        from core.validator import AgentValidator
        import yaml
        
        try:
            with open("settings.yaml", "r", encoding="utf-8") as f:
                settings = yaml.safe_load(f) or {}
                rules = settings.get("tournament", {}).get("rounds", {}).get(phase, {})
        except:
            rules = {}

        board_size = rules.get("board_size", 10)
        ship_sizes = rules.get("ship_sizes", [5, 4, 3, 3, 2])
        
        validator = AgentValidator(word_limit=500)
        results = {}
        
        # Filtrar agentes que participan en la fase actual
        active_teams = set()
        for mid, m in self.matches.items():
            if mid.startswith(phase):
                if m.team_a: active_teams.add(m.team_a)
                if m.team_b: active_teams.add(m.team_b)
        
        agents = [a for a in self._discover_agents() if a.name in active_teams]
        
        for agent in agents:
            # Aplicar lógica adaptativa para la validación de fase
            # Buscamos archivos específicos (.s.md, .f.md)
            phase_almacen = agent.almacen_path.parent / f"{agent.name}.almacen.{phase}.md"
            if phase_almacen.exists():
                agent.almacen_path = phase_almacen
            
            phase_agent = agent.agent_md_path.parent / f"{agent.name}.{phase}.md"
            if phase_agent.exists():
                agent.agent_md_path = phase_agent

            res = validator.validate(agent, board_size, ship_sizes)
            results[agent.name] = {
                "is_valid": res.is_valid,
                "errors": res.errors,
                "word_count": res.word_count,
                "ship_sizes": res.ship_sizes,
                "almacen_usado": agent.almacen_path.name # Añadido para que el usuario vea qué archivo se está validando
            }
        return results
