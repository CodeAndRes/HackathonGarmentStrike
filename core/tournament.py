"""
core/tournament.py
──────────────────
Tournament Runner: discovers agents, plays Round Robin, writes results.

Key responsibilities:
  · discover_agents()  – scan /agentes folder for team configs.
  · run_match()        – play one full game, enforcing the HIT → repeat-turn rule.
  · run_tournament()   – pair all agents, aggregate standings, save JSON report.

Reviewer Agent – The Golden Rule is enforced in run_match():
    result in ("hit", "sunk")  →  game.switch_turn() is NOT called.
    result == "miss"           →  game.switch_turn() IS called.
    result == "already_shot"   →  counted as a wasted shot, turn switches.
"""
from __future__ import annotations

import json
import random
import time
import requests
from dataclasses import asdict, dataclass, field
from itertools import combinations
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.progress import track
from rich.rule import Rule
from rich.table import Table

from core.engine import AlmacenParser, Board, Game, LOGISTICS_MAP, MoveRecord
from core.llm_client import AgentMove, LLMClient, MoveHistoryEntry
from core.visualizer import GameDashboard

console = Console()


# ── Agent config ──────────────────────────────────────────────────────────────


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


# ── Match / tournament records ────────────────────────────────────────────────


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
    already_shot_a: int = 0   # wasted shots by A
    already_shot_b: int = 0   # wasted shots by B
    avg_latency_a: float = 0.0
    avg_latency_b: float = 0.0
    prompt_tokens_a: int = 0
    completion_tokens_a: int = 0
    prompt_tokens_b: int = 0
    completion_tokens_b: int = 0
    errors_a: int = 0
    errors_b: int = 0
    win_reason: str = "Aniquilación"



@dataclass
class TournamentReport:
    matches: list[MatchRecord] = field(default_factory=list)
    standings: dict[str, dict] = field(default_factory=dict)

    def _ensure_entry(self, name: str) -> None:
        if name not in self.standings:
            self.standings[name] = {
                "wins": 0,
                "losses": 0,
                "draws": 0,
                "total_shots": 0,
                "total_hits": 0,
                "wasted_shots": 0,
                "total_latency": 0.0,
                "latency_count": 0,
                "total_prompt_tokens": 0,
                "total_completion_tokens": 0,
                "total_errors": 0,
            }

    def update_standings(self, match: MatchRecord) -> None:
        self._ensure_entry(match.agent_a)
        self._ensure_entry(match.agent_b)
        if match.winner == match.agent_a:
            self.standings[match.agent_a]["wins"] += 1
            self.standings[match.agent_b]["losses"] += 1
        elif match.winner == match.agent_b:
            self.standings[match.agent_b]["wins"] += 1
            self.standings[match.agent_a]["losses"] += 1
        else:
            self.standings[match.agent_a]["draws"] += 1
            self.standings[match.agent_b]["draws"] += 1
            
        # Aggregate shots and hits
        for agent, shots, hits, wasted, lat, pt, ct, err in [
            (match.agent_a, match.shots_a, match.hits_a, match.already_shot_a, 
             match.avg_latency_a, match.prompt_tokens_a, match.completion_tokens_a, match.errors_a),
            (match.agent_b, match.shots_b, match.hits_b, match.already_shot_b, 
             match.avg_latency_b, match.prompt_tokens_b, match.completion_tokens_b, match.errors_b),
        ]:
            s = self.standings[agent]
            s["total_shots"] += shots
            s["total_hits"] += hits
            s["wasted_shots"] += wasted
            s["total_prompt_tokens"] += pt
            s["total_completion_tokens"] += ct
            s["total_errors"] += err
            if lat > 0:
                s["total_latency"] += lat
                s["latency_count"] += 1


# ── History helpers ───────────────────────────────────────────────────────────


def _build_history(move_log, last_n: int = 10) -> list[MoveHistoryEntry]:
    return [
        MoveHistoryEntry(
            turno=r.turn,
            agente=r.agent_name,
            coordenada=r.coordinate,
            resultado=r.result,
            razonamiento=r.razonamiento or None,
        )
        for r in move_log[-last_n:]
    ]


# ── Single match ──────────────────────────────────────────────────────────────


def run_match(
    config_a: AgentConfig,
    config_b: AgentConfig,
    llm_client: LLMClient | dict[str, LLMClient],
    visual: bool = True,
    ui_sleep: float = 1.0,
    board_size: int = 10,
    max_turns: int = 50,
    ship_sizes: list[int] | None = None,
    export_json: bool = False,
) -> MatchRecord:
    """
    Play one full match.

    Reviewer Agent note on the Golden Rule:
        After apply_move() returns 'hit' or 'sunk', switch_turn() is NOT called.
        The same agent fires again in the next loop iteration.
    """
    board_a = config_a.load_board(size=board_size, ship_sizes=ship_sizes)
    board_b = config_b.load_board(size=board_size, ship_sizes=ship_sizes)
    agent_md_a = config_a.load_agent_md()
    agent_md_b = config_b.load_agent_md()

    game = Game(config_a.name, board_a, config_b.name, board_b)
    
    # If exporting JSON, we might want to disable visual dashboard if specified
    # but the prompt says "Visualización Táctica suprime log visual del tablero ascii"
    # dashboard = GameDashboard(...) if visual else None
    
    dashboard = GameDashboard(config_a.name, config_b.name) if (visual and not export_json) else None
    agent_mds = {config_a.name: agent_md_a, config_b.name: agent_md_b}
    wasted: dict[str, int] = {config_a.name: 0, config_b.name: 0}
    hits_count: dict[str, int] = {config_a.name: 0, config_b.name: 0}
    lats: dict[str, list[float]] = {config_a.name: [], config_b.name: []}
    tokens: dict[str, dict] = {
        config_a.name: {"p": 0, "c": 0},
        config_b.name: {"p": 0, "c": 0}
    }
    api_errors: dict[str, int] = {config_a.name: 0, config_b.name: 0}

    # Support mixed models: single client or per-team dict
    if isinstance(llm_client, dict):
        llm_clients = llm_client
    else:
        llm_clients = {config_a.name: llm_client, config_b.name: llm_client}

    # Use a unique log file for this match in the reports folder
    Path("reports").mkdir(exist_ok=True)
    log_file = Path(f"reports/turns_{config_a.name}_vs_{config_b.name}.log")
    if log_file.exists():
        log_file.unlink()

    debug_file = Path("logs/llm_debug.log")
    if debug_file.exists():
        debug_file.unlink()

    if dashboard:
        dashboard.start()
        dashboard.render(
            board_a=board_a,
            board_b=board_b,
            move_log=game.move_log,
            current_agent=config_a.name,
            last_strategy="Iniciando...",
            last_reasoning="Estableciendo conexión con el LLM para el primer turno...",
        )
    
    if export_json:
        # Reset inicial para que la web limpie la pantalla de victoria anterior
        _write_game_state(game, finished=False)

    timeout_winner = None
    final_reason = "Aniquilación"
    try:
        while True:
            finished, winner = game.is_over()
            if finished:
                break
            
            # OPTIMIZATION LIMIT
            if game.turn_count >= max_turns:
                with log_file.open("a", encoding="utf-8") as f:
                    f.write(f"\n[SISTEMA] Límite de {max_turns} turnos alcanzado. Aplicando desempate por puntos.\n")
                
                # Winner evaluation logic on timeout
                # 1. Sunk ships (pedidos encajados) — who sank more enemy ships
                sunk_a = sum(1 for s in board_b.ships if s.is_sunk)  # A sank on B's board
                sunk_b = sum(1 for s in board_a.ships if s.is_sunk)  # B sank on A's board
                
                # 2. Total hits on enemy (prendas encajadas)
                hits_by_a = sum(1 for r in board_b.shots_received.values() if r in ("hit", "sunk"))
                hits_by_b = sum(1 for r in board_a.shots_received.values() if r in ("hit", "sunk"))
                
                # 3. Hits received on OWN board (less is better — defensive metric)
                dmg_to_a = sum(1 for r in board_a.shots_received.values() if r in ("hit", "sunk"))
                dmg_to_b = sum(1 for r in board_b.shots_received.values() if r in ("hit", "sunk"))

                if sunk_a > sunk_b:
                    timeout_winner = config_a.name
                    reason = "PUNTOS"
                elif sunk_b > sunk_a:
                    timeout_winner = config_b.name
                    reason = "PUNTOS"
                elif hits_by_a > hits_by_b:
                    timeout_winner = config_a.name
                    reason = "HITS"
                elif hits_by_b > hits_by_a:
                    timeout_winner = config_b.name
                    reason = "HITS"
                elif dmg_to_a < dmg_to_b:
                    timeout_winner = config_a.name
                    reason = "DEFENSA"
                elif dmg_to_b < dmg_to_a:
                    timeout_winner = config_b.name
                    reason = "DEFENSA"
                else:
                    timeout_winner = None
                    reason = "EMPATE ABSOLUTO"
                
                if timeout_winner:
                   with log_file.open("a", encoding="utf-8") as f:
                       f.write(f"[SISTEMA] Victoria concedida a {timeout_winner} por {reason}.\n")
                   final_reason = f"Límite de turnos ({reason})"
                else:
                   with log_file.open("a", encoding="utf-8") as f:
                       f.write(f"[SISTEMA] {reason}: Nadie consigue ventaja.\n")
                   final_reason = f"Límite de turnos ({reason})"
                break

            current = game.current_agent
            opponent = game.opponent
            target_board = game.agents[current]   # board being attacked

            # Ask the LLM for a move
            active_client = llm_clients[current]

            # Feedback visual de "Pensando..." en el Dashboard
            if dashboard:
                # Inyectamos un registro temporal de pensamiento para la telemetría
                thinking_record = MoveRecord(
                    turn=game.turn_count + 1,
                    agent_name=current,
                    coordinate="??",
                    result="thinking",
                    razonamiento="Analizando vulnerabilidades en la cadena de suministro...",
                    estrategia_aplicada="PROCESANDO..."
                )
                game.move_log.append(thinking_record)
                _write_game_state(game)
                game.move_log.pop() # Limpiamos para no ensuciar el log real

            board_text = (
                target_board.grid_text_minimal()
                if active_client.quick_mode
                else target_board.grid_text(reveal_ships=False)
            )
            forbidden_set = {f"{c}{r}" for c, r in target_board.shots_received.keys()}

            # Reset telemetría del equipo activo antes de pedir el movimiento
            if export_json:
                _write_game_state(game, override_telemetry={current: {"strategy": "", "reasoning": "", "cursor": None}})

            try:
                move: AgentMove = active_client.get_move(
                    agent_md=agent_mds[current],
                    opponent_board_text=board_text,
                    move_history=_build_history(game.move_log),
                    my_name=current,
                    opponent_name=opponent,
                    forbidden_coords=forbidden_set,
                )
                col = move.coordenada[0]
                row = int(move.coordenada[1:])
                
                razon = move.razonamiento
                estrategia = move.estrategia_aplicada
                lat = move.latency_ms
                
                # Accumulate tokens
                tokens[current]["p"] += move.prompt_tokens
                tokens[current]["c"] += move.completion_tokens

                # Emitir telemetría pre-disparo (el frontend anima a su ritmo)
                if export_json:
                    _write_game_state(game, override_telemetry={current: {
                        "strategy": estrategia,
                        "reasoning": razon,
                        "cursor": "aiming",
                        "target": move.coordenada
                    }})

            except Exception as e:
                api_errors[current] += 1
                error_msg = f"LLM Error: {str(e)}"
                libres = []
                for c in target_board.cols:
                    for r in target_board.rows:
                        cand = f"{c}{r}"
                        if cand not in forbidden_set:
                            libres.append(cand)
                
                libre = random.choice(libres) if libres else f"{target_board.cols[0]}1"
                col, row = libre[0], int(libre[1:])
                razon = f"SISTEMA: Fallback por error crítico de API. Detalle: {error_msg}"
                estrategia = "EMERGENCY FALLBACK"
                lat = 0.0

            if lat > 0:
                lats[current].append(lat)

            # Ejecutar el movimiento UNA SOLA VEZ
            result = game.apply_move(col, row, razon, estrategia)
            if result in ("hit", "sunk"):
                hits_count[current] += 1

            if export_json:
                _write_game_state(game)
            
            # Pausa para que el dashboard web pueda renderizar la animación
            if export_json:
                time.sleep(ui_sleep)

            if result == "already_shot":
                wasted[current] += 1

            with log_file.open("a", encoding="utf-8") as f:
                lat_str = f" {lat/1000.0:.2f}s" if lat else ""
                log_res = LOGISTICS_MAP.get(result, result.upper())
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                model_name = getattr(active_client, "model", "unknown")
                f.write(f"[{timestamp}] [{model_name}] [T {game.turn_count:>3}] {current:<15} -> {col}{row:<3} | {log_res:<16} | lat:{lat_str}\n")
                if "SISTEMA" in razon:
                    f.write(f"           ↳ (AVISO: El LLM falló. Se usó tiro forzado para continuar)\n")
                elif result == "already_shot":
                    f.write(f"           ↳ (Error: AI intentó disparar donde ya había disparado)\n")

            # Refresh dashboard after every shot
            if dashboard:
                dashboard.render(
                    board_a=board_a,
                    board_b=board_b,
                    move_log=game.move_log,
                    current_agent=current,
                    last_strategy=estrategia,
                    last_reasoning=razon,
                )
                time.sleep(ui_sleep)

            if result not in ("hit", "sunk"):
                game.switch_turn()
    finally:
        # Determine winner (Natural or Tiebreaker)
        finished, natural_winner = game.is_over()
        
        hits_a = hits_count[config_a.name]
        hits_b = hits_count[config_b.name]
        if hits_a > hits_b:
            timeout_winner = config_a.name
            final_reason = "Mayor número de aciertos (timeout)"
        elif hits_b > hits_a:
            timeout_winner = config_b.name
            final_reason = "Mayor número de aciertos (timeout)"
        else:
            timeout_winner = "EMPATE"
            final_reason = "Igualdad de aciertos (timeout)"

        winner = natural_winner if finished else timeout_winner
        if finished:
            final_reason = f"Victoria por eliminación"

        if dashboard:
            dashboard.stop()
        if export_json:
            # Final write to ensure the dashboard sees the 'finished' state
            _write_game_state(game, finished=True, winner=winner)
            
    if dashboard:
        dashboard.print_winner(winner, game.turn_count)

    def _avg(lst): return sum(lst)/len(lst) if lst else 0.0

    return MatchRecord(
        agent_a=config_a.name,
        agent_b=config_b.name,
        winner=winner,
        total_turns=game.turn_count,
        shots_a=game.shots_fired[config_a.name],
        shots_b=game.shots_fired[config_b.name],
        hits_a=hits_count[config_a.name],
        hits_b=hits_count[config_b.name],
        already_shot_a=wasted[config_a.name],
        already_shot_b=wasted[config_b.name],
        avg_latency_a=_avg(lats[config_a.name]),
        avg_latency_b=_avg(lats[config_b.name]),
        prompt_tokens_a=tokens[config_a.name]["p"],
        completion_tokens_a=tokens[config_a.name]["c"],
        prompt_tokens_b=tokens[config_b.name]["p"],
        completion_tokens_b=tokens[config_b.name]["c"],
        errors_a=api_errors[config_a.name],
        errors_b=api_errors[config_b.name],
        win_reason=final_reason,
    )


def serialize_game_state(game: Game, finished: bool = None, winner: str = None, override_telemetry: dict = None) -> dict:
    """
    Export current game state into the schema required by the external tactical dashboard.
    """
    def _serialize_team(name: str) -> dict:
        board = game.boards[name]
        fleet = {}
        for ship in board.ships:
            for col, row in ship.cells:
                # Convert to indices (F,C)
                ri = row - 1
                ci = board.cols.index(col)
                fleet[f"{ri},{ci}"] = ship.order_id
        
        return {
            "name": name,
            "pedidos_encajados": sum(1 for s in board.ships if s.is_sunk),
            "total_pedidos": len(board.ships),
            "prendas_encajadas": sum(1 for res in board.shots_received.values() if res in ("hit", "sunk")),
            "fleet": fleet,
            "board": board.visible_state(reveal_ships=True)
        }

    # Identify last moves for telemetry
    move_a = next((m for m in reversed(game.move_log) if m.result != "pending" and m.agent_name == game.names[0]), None)
    move_b = next((m for m in reversed(game.move_log) if m.result != "pending" and m.agent_name == game.names[1]), None)

    telemetry = {
        "team_a": {
            "strategy": move_a.estrategia_aplicada if move_a else "Iniciando...",
            "reasoning": move_a.razonamiento if move_a else "A la espera...",
            "cursor": None
        },
        "team_b": {
            "strategy": move_b.estrategia_aplicada if move_b else "Iniciando...",
            "reasoning": move_b.razonamiento if move_b else "A la espera...",
            "cursor": None
        }
    }

    # Apply granular overrides for tactical writing sequence
    if override_telemetry:
        if game.names[0] in override_telemetry:
            telemetry["team_a"].update(override_telemetry[game.names[0]])
        if game.names[1] in override_telemetry:
            telemetry["team_b"].update(override_telemetry[game.names[1]])

    state = {
        "turn": game.turn_count,
        "turn_agent": "team_a" if game.current_agent == game.names[0] else "team_b",
        "team_a": _serialize_team(game.names[0]),
        "team_b": _serialize_team(game.names[1]),
        "comms": [
            {
                "turn": m.turn,
                "agent": "A" if m.agent_name == game.names[0] else "B",
                "coord": m.coordinate,
                "result": m.result.upper(),
                "icon": "📦" if m.result == "sunk" else ("🎯" if m.result == "hit" else ("🚫" if m.result == "already_shot" else "💦")),
                "reasoning": m.razonamiento
            } for m in game.move_log if m.result != "pending"
        ],
        "telemetry": telemetry,
        "finished": finished if finished is not None else game.is_over()[0],
        "winner": winner if winner is not None else game.is_over()[1]
    }
    return state


def _write_game_state(game: Game, finished: bool = None, winner: str = None, override_telemetry: dict = None) -> None:
    """Helper to write game_state.json and push to Real-time API."""
    state = serialize_game_state(game, finished=finished, winner=winner, override_telemetry=override_telemetry)
    
    def _sanitize(obj):
        if isinstance(obj, dict): return {str(k): _sanitize(v) for k, v in obj.items()}
        if isinstance(obj, list): return [_sanitize(i) for i in obj]
        return obj

    # 1. Escritura tradicional en archivo (Retrocompatibilidad y Debug)
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    with open(log_dir / "game_state.json", "w", encoding="utf-8") as f:
        json.dump(state, f, indent=4, ensure_ascii=False)
        
    # 2. PUSH a la API en tiempo real
    try:
        # Usamos un timeout muy corto para no bloquear el motor si la API no responde
        requests.post("http://127.0.0.1:8000/api/event", json=_sanitize(state), timeout=1.0)
    except Exception:
        pass # Silencioso si el servidor API no está arriba


# ── Agent discovery ───────────────────────────────────────────────────────────


def discover_agents(agents_dir: str | Path = "agentes") -> list[AgentConfig]:
    """
    Scan <agents_dir>/ for team sub-folders.
    Each valid team folder must contain:
        agent.md          – strategy manifesto
        almacen_*.md      – warehouse placement
    """
    agents_dir = Path(agents_dir)
    configs: list[AgentConfig] = []

    if not agents_dir.exists():
        console.print(f"[red]Carpeta '{agents_dir}' no encontrada.[/red]")
        return configs

    for team_dir in sorted(agents_dir.iterdir()):
        if not team_dir.is_dir():
            continue
        agent_md = team_dir / "agent.md"
        almacen_files = sorted(team_dir.glob("almacen_*.md"))

        if not agent_md.exists():
            console.print(
                f"[yellow][!] {team_dir.name}: agent.md no encontrado - omitido.[/yellow]"
            )
            continue
        if not almacen_files:
            console.print(
                f"[yellow][!] {team_dir.name}: almacen_*.md no encontrado - omitido.[/yellow]"
            )
            continue

        configs.append(
            AgentConfig(
                name=team_dir.name,
                agent_md_path=agent_md,
                almacen_path=almacen_files[0],
            )
        )
        console.print(f"[green][OK] Agente cargado: {team_dir.name}[/green]")

    return configs


# -- Tournament runner ---------------------------------------------------------


def run_tournament(
    agents_dir: str | Path = "agentes",
    llm_model: str = "ollama/qwen2:0.5b",
    output_file: str = "tournament_results.json",
    visual: bool = True,
    quick_mode: bool = True,
    api_sleep: float = 6.0,
    max_tokens: int = 150,
    ui_sleep: float = 1.0,
    board_size: int = 10,
    max_turns: int = 50,
    ship_sizes: list[int] | None = None,
) -> TournamentReport:
    """Run a full Round-Robin tournament and save results to JSON."""
    agents = discover_agents(agents_dir)
    if len(agents) < 2:
        raise ValueError(
            f"Se necesitan al menos 2 agentes para el torneo. "
            f"Se encontraron: {len(agents)}."
        )

    llm_client = LLMClient(
        model=llm_model,
        temperature=0.0,
        max_retries=1,
        quick_mode=quick_mode,
        api_sleep=api_sleep,
        max_tokens=max_tokens,
    )
    report = TournamentReport()
    pairs = list(combinations(agents, 2))
    num_matches = len(pairs)

    console.print(Rule(f"[bold]Torneo Round Robin - {len(agents)} equipos, {num_matches} partidas[/bold]"))

    for config_a, config_b in track(pairs, description="Jugando partidas..."):
        console.print(Rule(f"[cyan]{config_a.name}  vs  {config_b.name}[/cyan]"))
        try:
            match = run_match(
                config_a, config_b, llm_client, 
                visual=visual, ui_sleep=ui_sleep, 
                board_size=board_size,
                max_turns=max_turns,
                ship_sizes=ship_sizes
            )
        except Exception as exc:
            console.print(f"[red]Error en la partida: {exc}[/red]")
            match = MatchRecord(
                agent_a=config_a.name,
                agent_b=config_b.name,
                winner=None,
                total_turns=0,
                shots_a=0,
                shots_b=0,
            )
        report.matches.append(match)
        report.update_standings(match)
        result_str = match.winner if match.winner else "EMPATE"
        console.print(
            f"Resultado: [bold]{result_str}[/bold]  ({match.total_turns} turnos)"
        )

    _save_results(report, output_file)
    _print_standings(report)
    return report


def _save_results(report: TournamentReport, output_file: str) -> None:
    payload = {
        "partidas": [
            {
                "agente_a": m.agent_a,
                "agente_b": m.agent_b,
                "ganador": m.winner,
                "turnos_totales": m.total_turns,
                "disparos_a": m.shots_a,
                "disparos_b": m.shots_b,
                "hits_a": m.hits_a,
                "hits_b": m.hits_b,
                "latencia_media_a": round(m.avg_latency_a / 1000.0, 3),
                "latencia_media_b": round(m.avg_latency_b / 1000.0, 3),
                "prompt_tokens_a": m.prompt_tokens_a,
                "completion_tokens_a": m.completion_tokens_a,
                "prompt_tokens_b": m.prompt_tokens_b,
                "completion_tokens_b": m.completion_tokens_b,
                "errores_api_a": m.errors_a,
                "errores_api_b": m.errors_b,
                "disparos_invalidos_a": m.already_shot_a,
                "disparos_invalidos_b": m.already_shot_b,
            }
            for m in report.matches
        ],
        "clasificacion": {
            name: stats
            for name, stats in sorted(
                report.standings.items(),
                key=lambda x: (-x[1]["wins"], -x[1]["draws"], x[1]["total_shots"]),
            )
        },
    }
    # Ensure reports folder
    report_dir = Path("reports")
    report_dir.mkdir(exist_ok=True)
    
    # Ensure filename is inside reports/ if it's a relative path
    target_path = Path(output_file)
    
    # Append timestamp to avoid overwriting
    timestamp_str = time.strftime("%Y%m%d_%H%M%S")
    new_stem = f"{target_path.stem}_{timestamp_str}"
    target_path = target_path.with_name(f"{new_stem}{target_path.suffix}")

    if not target_path.is_absolute():
        target_path = report_dir / target_path.name
        
    output_file = str(target_path)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    
    # Also save as Markdown
    md_file = str(target_path.with_suffix(".md"))
    _save_markdown_report(report, md_file)
    
    console.print(f"\n[bold green]Resultados guardados en la carpeta 'reports/':[/bold green]")
    console.print(f" - JSON: [cyan]{output_file}[/cyan]")
    console.print(f" - Markdown: [cyan]{md_file}[/cyan]")


def _save_markdown_report(report: TournamentReport, md_file: str) -> None:
    """Generates a human-readable markdown report with tables and analytics."""
    lines = [
        "# [TOURNAMENT] Garment Strike - Informe de Torneo",
        f"\n*Fecha: {time.strftime('%Y-%m-%d %H:%M:%S')}*",
        "\n## Clasificacion Final",
        "\n| Equipo | V | D | E | Precision | Latencia | Errores | Tokens (P/C) |",
        "| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |"
    ]
    
    for name, s in sorted(
        report.standings.items(), key=lambda x: (-x[1]["wins"], -x[1]["draws"], x[1]["total_shots"])
    ):
        acc = (s["total_hits"] / s["total_shots"] * 100) if s["total_shots"] > 0 else 0
        lat = (s["total_latency"] / s["latency_count"] / 1000.0) if s["latency_count"] > 0 else 0
        tokens_str = f"{s['total_prompt_tokens']}/{s['total_completion_tokens']}"
        lines.append(
            f"| **{name}** | {s['wins']} | {s['losses']} | {s['draws']} | {acc:.1f}% | {lat:.2f}s | {s['total_errors']} | {tokens_str} |"
        )
        
    lines.append("\n## Detalle de Partidas")
    for i, m in enumerate(report.matches, 1):
        win_text = f"WINNER: {m.winner} ({m.win_reason})" if m.winner else f"DRAW ({m.win_reason})"
        acc_a = (m.hits_a / m.shots_a * 100) if m.shots_a > 0 else 0
        acc_b = (m.hits_b / m.shots_b * 100) if m.shots_b > 0 else 0
        
        lines.append(f"\n### Partida {i}: {m.agent_a} vs {m.agent_b}")
        lines.append(f"- **Resultado**: {win_text}")
        lines.append(f"- **Duración**: {m.total_turns} turnos")
        lines.append(f"- **Estadísticas {m.agent_a}**:")
        lines.append(f"  - Precision: {acc_a:.1f}% | Latencia: {m.avg_latency_a/1000.0:.2f}s | Errores: {m.errors_a}")
        lines.append(f"  - Tokens: {m.prompt_tokens_a} (P) / {m.completion_tokens_a} (C)")
        lines.append(f"- **Estadísticas {m.agent_b}**:")
        lines.append(f"  - Precision: {acc_b:.1f}% | Latencia: {m.avg_latency_b/1000.0:.2f}s | Errores: {m.errors_b}")
        lines.append(f"  - Tokens: {m.prompt_tokens_b} (P) / {m.completion_tokens_b} (C)")
        
    lines.append("\n## Leyenda")
    lines.append("- **V**: Victorias")
    lines.append("- **D**: Derrotas")
    lines.append("- **E**: Empates")
    lines.append("- **Precision**: Porcentaje de disparos que aciertan (Prendas encajadas / Disparos totales)")
    lines.append("- **Latencia**: Tiempo medio de respuesta del modelo de IA por turno (en segundos)")
    lines.append("- **Errores**: Fallos de comunicación con la API (Timeouts, Alucinaciones, etc.)")
    lines.append("- **Tokens (P/C)**: Consumo de Tokens (P = Prompt / Entrada, C = Completion / Salida)")
        
    lines.append("\n\n---\n*Generado por Garment Strike Engine*")
    
    with open(md_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def _print_standings(report: TournamentReport) -> None:
    tbl = Table(title="[bold]CLASIFICACION FINAL[/bold]", box=None, show_lines=True)
    tbl.add_column("Equipo", style="bold white")
    tbl.add_column("V", justify="center", style="green")
    tbl.add_column("D", justify="center", style="red")
    tbl.add_column("E", justify="center", style="yellow")
    tbl.add_column("Precision", justify="right", style="magenta")
    tbl.add_column("Latencia", justify="right", style="blue")
    tbl.add_column("Errores", justify="right", style="red")
    tbl.add_column("Tokens (P/C)", justify="right", style="cyan")

    for name, stats in sorted(
        report.standings.items(), key=lambda x: (-x[1]["wins"], -x[1]["draws"], x[1]["total_shots"])
    ):
        acc = (stats["total_hits"] / stats["total_shots"] * 100) if stats["total_shots"] > 0 else 0
        lat = (stats["total_latency"] / stats["latency_count"] / 1000.0) if stats["latency_count"] > 0 else 0
        tokens_str = f"{stats['total_prompt_tokens']}/{stats['total_completion_tokens']}"
        
        tbl.add_row(
            name,
            str(stats["wins"]),
            str(stats["losses"]),
            str(stats["draws"]),
            f"{acc:.1f}%",
            f"{lat:.2f}s",
            str(stats["total_errors"]),
            tokens_str,
        )
    console.print(tbl)
