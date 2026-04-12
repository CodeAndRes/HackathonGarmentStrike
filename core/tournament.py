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
import time
import random
from dataclasses import asdict, dataclass, field
from itertools import combinations
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.progress import track
from rich.rule import Rule
from rich.table import Table

from core.engine import AlmacenParser, Board, Game
from core.llm_client import AgentMove, LLMClient, MoveHistoryEntry
from core.visualizer import GameDashboard

console = Console()
LOGISTICS_MAP = {
    "hit": "Prenda encajada",
    "miss": "Prenda perdida",
    "sunk": "Pedido ENCAJADO",
    "already_shot": "Celda duplicada"
}


# ── Agent config ──────────────────────────────────────────────────────────────


@dataclass
class AgentConfig:
    name: str
    agent_md_path: Path
    almacen_path: Path

    def load_agent_md(self) -> str:
        return self.agent_md_path.read_text(encoding="utf-8")

    def load_board(self) -> Board:
        ships = AlmacenParser.parse(self.almacen_path)
        return Board(ships)


# ── Match / tournament records ────────────────────────────────────────────────


@dataclass
class MatchRecord:
    agent_a: str
    agent_b: str
    winner: Optional[str]
    total_turns: int
    shots_a: int
    shots_b: int
    already_shot_a: int = 0   # wasted shots by A
    already_shot_b: int = 0   # wasted shots by B


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
                "wasted_shots": 0,
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
        self.standings[match.agent_a]["total_shots"] += match.shots_a
        self.standings[match.agent_b]["total_shots"] += match.shots_b
        self.standings[match.agent_a]["wasted_shots"] += match.already_shot_a
        self.standings[match.agent_b]["wasted_shots"] += match.already_shot_b


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
    llm_client: LLMClient,
    visual: bool = True,
    ui_sleep: float = 1.0,
) -> MatchRecord:
    """
    Play one full match.

    Reviewer Agent note on the Golden Rule:
        After apply_move() returns 'hit' or 'sunk', switch_turn() is NOT called.
        The same agent fires again in the next loop iteration.
    """
    board_a = config_a.load_board()
    board_b = config_b.load_board()
    agent_md_a = config_a.load_agent_md()
    agent_md_b = config_b.load_agent_md()

    game = Game(config_a.name, board_a, config_b.name, board_b)
    dashboard = GameDashboard(config_a.name, config_b.name) if visual else None
    agent_mds = {config_a.name: agent_md_a, config_b.name: agent_md_b}
    wasted: dict[str, int] = {config_a.name: 0, config_b.name: 0}

    log_file = Path("logs/match_turns.log")
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

    try:
        while True:
            finished, winner = game.is_over()
            if finished:
                break
            
            # OPTIMIZATION LIMIT: 50 turns
            if game.turn_count >= 50:
                with log_file.open("a", encoding="utf-8") as f:
                    f.write(f"\n[SISTEMA] Límite de 50 turnos alcanzado. Cortando partida para optimización.\n")
                break

            current = game.current_agent
            opponent = game.opponent
            target_board = game.agents[current]   # board being attacked

            # Ask the LLM for a move
            # Ask the LLM for a move
            board_text = (
                target_board.grid_text_minimal()
                if llm_client.quick_mode
                else target_board.grid_text(reveal_ships=False)
            )
            forbidden_set = {f"{c}{r}" for c, r in target_board.shots_received.keys()}

            try:
                move: AgentMove = llm_client.get_move(
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
            except Exception as e:
                # El modelo falló (error de red, cuota, auth, etc.) o alucinó repetidamente.
                # Reportamos el error real antes del fallback.
                error_msg = f"LLM Error: {str(e)}"
                
                # Elegimos una celda libre ALEATORIA para no crashear y continuar la partida.
                libres = []
                for c in "ABCDEFGHIJ":
                    for r in range(1, 11):
                        cand = f"{c}{r}"
                        if cand not in forbidden_set:
                            libres.append(cand)
                
                libre = random.choice(libres) if libres else "A1"
                col, row = libre[0], int(libre[1:])
                razon = f"SISTEMA: Fallback por error crítico de API. Detalle: {error_msg}"
                estrategia = "EMERGENCY FALLBACK"
                lat = 0.0

            result = game.apply_move(col, row, razon, estrategia)

            if result == "already_shot":
                wasted[current] += 1

            with log_file.open("a", encoding="utf-8") as f:
                lat_str = f" {lat/1000.0:.2f}s" if lat else ""
                log_res = LOGISTICS_MAP.get(result, result.upper())
                f.write(f"[T {game.turn_count:>3}] {current:<15} -> {col}{row:<3} | {log_res:<16} | lat:{lat_str}\n")
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

            # ── GOLDEN RULE ────────────────────────────────────────────────────
            # HIT or SUNK  → same agent shoots again (do NOT switch).
            # MISS or ALREADY_SHOT → pass the turn to the other agent.
            # ──────────────────────────────────────────────────────────────────
            if result not in ("hit", "sunk"):
                game.switch_turn()
    finally:
        if dashboard:
            dashboard.stop()

    finished, winner = game.is_over()

    if dashboard:
        dashboard.print_winner(winner, game.turn_count)

    return MatchRecord(
        agent_a=config_a.name,
        agent_b=config_b.name,
        winner=winner,
        total_turns=game.turn_count,
        shots_a=game.shots_fired[config_a.name],
        shots_b=game.shots_fired[config_b.name],
        already_shot_a=wasted[config_a.name],
        already_shot_b=wasted[config_b.name],
    )


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
                f"[yellow]⚠  {team_dir.name}: agent.md no encontrado – omitido.[/yellow]"
            )
            continue
        if not almacen_files:
            console.print(
                f"[yellow]⚠  {team_dir.name}: almacen_*.md no encontrado – omitido.[/yellow]"
            )
            continue

        configs.append(
            AgentConfig(
                name=team_dir.name,
                agent_md_path=agent_md,
                almacen_path=almacen_files[0],
            )
        )
        console.print(f"[green]✓  Agente cargado: {team_dir.name}[/green]")

    return configs


# ── Tournament runner ─────────────────────────────────────────────────────────


def run_tournament(
    agents_dir: str | Path = "agentes",
    llm_model: str = "ollama/qwen2:0.5b",
    output_file: str = "tournament_results.json",
    visual: bool = True,
    quick_mode: bool = True,
    api_sleep: float = 6.0,
    max_tokens: int = 150,
    ui_sleep: float = 1.0,
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

    console.print(
        Rule(f"[bold]Torneo Round Robin – {len(agents)} equipos, {len(pairs)} partidas[/bold]")
    )

    for config_a, config_b in track(pairs, description="Jugando partidas..."):
        console.print(Rule(f"[cyan]{config_a.name}  vs  {config_b.name}[/cyan]"))
        try:
            match = run_match(config_a, config_b, llm_client, visual=visual, ui_sleep=ui_sleep)
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
                "disparos_invalidos_a": m.already_shot_a,
                "disparos_invalidos_b": m.already_shot_b,
            }
            for m in report.matches
        ],
        "clasificacion": {
            name: stats
            for name, stats in sorted(
                report.standings.items(),
                key=lambda x: (-x[1]["wins"], x[1]["total_shots"]),
            )
        },
    }
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    console.print(f"\n[bold green]Resultados guardados en: {output_file}[/bold green]")


def _print_standings(report: TournamentReport) -> None:
    tbl = Table(title="[bold]🏆  Clasificación Final[/bold]", box=None, show_lines=True)
    tbl.add_column("Equipo", style="bold white")
    tbl.add_column("V", justify="center", style="green")
    tbl.add_column("D", justify="center", style="red")
    tbl.add_column("E", justify="center", style="yellow")
    tbl.add_column("Disparos", justify="right", style="cyan")
    tbl.add_column("Inválidos", justify="right", style="dim")

    for name, stats in sorted(
        report.standings.items(), key=lambda x: (-x[1]["wins"], x[1]["total_shots"])
    ):
        tbl.add_row(
            name,
            str(stats["wins"]),
            str(stats["losses"]),
            str(stats["draws"]),
            str(stats["total_shots"]),
            str(stats["wasted_shots"]),
        )
    console.print(tbl)
