"""
core/visualizer.py
──────────────────
Rich-based terminal dashboard for Garment Strike.

Shows:
  · Two boards side-by-side (spectator view – both revealed).
  · Move log (last N entries with color-coded results).
  · Thought Telemetry panel: which part of agent.md is being executed.
"""
from __future__ import annotations

from rich import box
from rich.columns import Columns
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.rule import Rule

from core.engine import Board, BOARD_COLS, MoveRecord

console = Console()

# ── Cell styling ──────────────────────────────────────────────────────────────

_CELL_STYLE: dict[str, str] = {
    "~": "dim blue",          # unknown
    "X": "bold red",          # hit / sunk
    "O": "bold cyan",         # miss – water
    "#": "bold green",        # own ship (revealed)
}

_RESULT_STYLE: dict[str, str] = {
    "hit": "bold yellow",
    "sunk": "bold red on white",
    "miss": "dim cyan",
    "already_shot": "dim",
}

_RESULT_ICON: dict[str, str] = {
    "hit": "💥 HIT",
    "sunk": "🔥 SUNK",
    "miss": "💧 MISS",
    "already_shot": "⚠️  ALREADY SHOT",
}


# ── Board renderer ────────────────────────────────────────────────────────────


def render_board(board: Board, title: str, reveal: bool = False) -> Table:
    """Return a Rich Table representing the board."""
    grid = board.visible_state(reveal_ships=reveal)
    tbl = Table(
        title=title,
        box=box.SIMPLE_HEAVY,
        show_lines=True,
        title_style="bold white",
    )
    tbl.add_column("", style="bold white", justify="right", width=3, no_wrap=True)
    for col in BOARD_COLS:
        tbl.add_column(col, justify="center", width=3, no_wrap=True)

    for ri, row_data in enumerate(grid):
        row_num = str(ri + 1)
        cells = [Text(ch, style=_CELL_STYLE.get(ch, "white")) for ch in row_data]
        tbl.add_row(row_num, *cells)

    return tbl


# ── Move log panel ────────────────────────────────────────────────────────────


def render_move_log(moves: list[MoveRecord], last_n: int = 12) -> Panel:
    content = Text()
    for rec in moves[-last_n:]:
        icon = _RESULT_ICON.get(rec.result, rec.result.upper())
        result_style = _RESULT_STYLE.get(rec.result, "white")
        content.append(f"[T{rec.turn:>3}] ", style="dim")
        content.append(f"{rec.agent_name:<18}", style="bold white")
        content.append(f" {rec.coordinate:<4}", style="bold magenta")
        content.append(f"  {icon:<18}", style=result_style)
        if rec.razonamiento:
            snippet = rec.razonamiento[:55] + ("…" if len(rec.razonamiento) > 55 else "")
            content.append(f"  ↳ {snippet}", style="dim italic")
        content.append("\n")
    return Panel(
        content,
        title="[bold]📋 Log de Movimientos[/bold]",
        border_style="blue",
        padding=(0, 1),
    )


# ── Thought telemetry panel ───────────────────────────────────────────────────


def render_telemetry(
    agent_name: str, strategy: str, reasoning: str
) -> Panel:
    content = Text()
    content.append("Agente activo:  ", style="dim")
    content.append(f"{agent_name}\n", style="bold yellow")
    content.append("Estrategia:     ", style="dim")
    content.append(f"{strategy or '(no especificada)'}\n\n", style="bold green")
    content.append("Razonamiento:\n", style="dim")
    content.append(reasoning or "(sin razonamiento)", style="italic white")
    return Panel(
        content,
        title="[bold cyan]🧠 Telemetría de Pensamiento[/bold cyan]",
        border_style="cyan",
        padding=(0, 1),
    )


# ── Score bar ─────────────────────────────────────────────────────────────────


def render_scores(
    name_a: str,
    board_a: Board,
    name_b: str,
    board_b: Board,
    turn: int,
) -> Text:
    def sunk_count(board: Board) -> int:
        return sum(1 for s in board.ships if s.is_sunk)

    def hit_coords(board: Board) -> int:
        return sum(1 for r in board.shots_received.values() if r in ("hit", "sunk"))

    bar = Text()
    bar.append(f"  Turno #{turn}   ", style="bold white")
    bar.append(f"[{name_a}] ", style="bold green")
    bar.append(f"pedidos hundidos: {sunk_count(board_b)}/5  |  ", style="yellow")
    bar.append(f"impactos totales: {hit_coords(board_b)}   ", style="cyan")
    bar.append("  │  ", style="dim")
    bar.append(f"[{name_b}] ", style="bold red")
    bar.append(f"pedidos hundidos: {sunk_count(board_a)}/5  |  ", style="yellow")
    bar.append(f"impactos totales: {hit_coords(board_a)}", style="cyan")
    return bar


# ── Full dashboard ────────────────────────────────────────────────────────────


class GameDashboard:
    """Stateless terminal dashboard.  Call render() after every move."""

    def __init__(self, name_a: str, name_b: str) -> None:
        self.name_a = name_a
        self.name_b = name_b

    def render(
        self,
        board_a: Board,
        board_b: Board,
        move_log: list[MoveRecord],
        current_agent: str,
        last_strategy: str = "",
        last_reasoning: str = "",
    ) -> None:
        console.clear()
        console.print(Rule("[bold yellow]  ⚡  GARMENT STRIKE – Supply Chain Simulation  ⚡  [/bold yellow]"))

        # Score bar
        console.print(
            render_scores(
                self.name_a, board_a,
                self.name_b, board_b,
                turn=len(move_log),
            )
        )
        console.print()

        # Dual board (spectator: both revealed)
        tbl_a = render_board(
            board_a,
            title=f"[green]{self.name_a}[/green]  (propio)",
            reveal=True,
        )
        tbl_b = render_board(
            board_b,
            title=f"[red]{self.name_b}[/red]  (propio)",
            reveal=True,
        )
        console.print(Columns([tbl_a, tbl_b], equal=True, expand=True))

        # Move log
        console.print(render_move_log(move_log))

        # Thought telemetry (only when we have data)
        if last_strategy or last_reasoning:
            console.print(
                render_telemetry(current_agent, last_strategy, last_reasoning)
            )

    def print_winner(self, winner: str | None, total_turns: int) -> None:
        console.print()
        if winner:
            console.print(
                Rule(f"[bold green]🏆  GANADOR: {winner}  –  {total_turns} turnos  🏆[/bold green]")
            )
        else:
            console.print(
                Rule(f"[bold yellow]⚖️  EMPATE  –  {total_turns} turnos alcanzados[/bold yellow]")
            )
