"""
main.py
───────
Entry point for Garment Strike.

Sub-commands:
  play        – Single match between two teams.
  tournament  – Round-Robin tournament from a folder of agent configs.

Usage examples:
  python main.py play \\
      --team-a "Alpha" --agent-a agentes/alpha/agent.md --almacen-a agentes/alpha/almacen_alpha.md \\
      --team-b "Beta"  --agent-b agentes/beta/agent.md  --almacen-b agentes/beta/almacen_beta.md

  python main.py tournament --agents-dir agentes/ --output results.json

  python main.py tournament --model openai/gpt-4o --no-visual
"""
from __future__ import annotations

import argparse
import os
import sys
import time
import yaml
from pathlib import Path
from dotenv import load_dotenv

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, IntPrompt
from rich.rule import Rule

console = Console()
load_dotenv()

# Load settings.yaml if present
SETTINGS_PATH = Path("settings.yaml")
if SETTINGS_PATH.exists():
    try:
        with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
            full_settings = yaml.safe_load(f) or {}
            SETTINGS = full_settings.get("engine", {})
    except Exception as e:
        console.print(f"[yellow]Aviso: No se pudo leer settings.yaml ({e}). Usando defaults.[/yellow]")
        SETTINGS = {}
else:
    SETTINGS = {}


# ── Sub-command handlers ──────────────────────────────────────────────────────


def cmd_play(args: argparse.Namespace) -> None:
    """Run a single match between two agent configs."""
    from core.llm_client import LLMClient
    from core.tournament import AgentConfig, run_match

    config_a = AgentConfig(
        name=args.team_a,
        agent_md_path=Path(args.agent_a),
        almacen_path=Path(args.almacen_a),
    )
    config_b = AgentConfig(
        name=args.team_b,
        agent_md_path=Path(args.agent_b),
        almacen_path=Path(args.almacen_b),
    )

    llm_client = LLMClient(
        model=args.model,
        api_sleep=args.sleep,
        max_tokens=args.max_tokens,
        board_size=args.board_size,
    )
    match = run_match(
        config_a, config_b, llm_client, visual=not args.no_visual, 
        ui_sleep=args.ui_sleep, board_size=args.board_size,
        max_turns=args.max_turns,
        ship_sizes=args.ship_sizes
    )

    winner_str = match.winner if match.winner else "EMPATE"
    console.print(f"\n[bold]Ganador:[/bold] {winner_str}")
    console.print(f"[bold]Turnos totales:[/bold] {match.total_turns}")
    console.print(
        f"[bold]Disparos:[/bold] {args.team_a}={match.shots_a}  |  {args.team_b}={match.shots_b}"
    )


def cmd_tournament(args: argparse.Namespace) -> None:
    """Run a Round-Robin tournament."""
    from core.tournament import run_tournament

    run_tournament(
        agents_dir=args.agents_dir,
        llm_model=args.model,
        output_file=args.output,
        visual=not args.no_visual,
        api_sleep=args.sleep,
        max_tokens=args.max_tokens,
        ui_sleep=args.ui_sleep,
        board_size=args.board_size,
        max_turns=args.max_turns,
        ship_sizes=args.ship_sizes,
    )


def run_interactive_menu(args: argparse.Namespace) -> None:
    """Interactively ask the user what they want to do."""
    while True:
        console.clear()
        console.print(
            Panel(
                "[bold yellow]⚡ GARMENT STRIKE – AI Supply Chain Simulator ⚡[/bold yellow]\n"
                "[dim]Hackathon Abril 2026[/dim]",
                expand=False,
            )
        )
        console.print("\n[bold cyan]Menú Principal:[/bold cyan]")
        console.print("1. [green]Ejecutar Pruebas (Tests)[/green]")
        console.print("2. [yellow]Partida de Ejemplo (Alpha vs Beta)[/yellow]")
        console.print("3. [magenta]Partida Personalizada[/magenta]")
        console.print("4. [red]Salir[/red]")

        choice = Prompt.ask("\nSelecciona una opción", choices=["1", "2", "3", "4"], default="4")

        if choice == "1":
            import subprocess

            console.print("\n[bold]Lanzando pytest...[/bold]")
            subprocess.run([sys.executable, "-m", "pytest", "tests/", "-v"])
            Prompt.ask("\nPresiona Enter para volver")

        elif choice == "2":
            # Quick match config
            args.command = "play"
            args.team_a = "Alpha"
            args.agent_a = "agentes/ejemplo/agent.md"
            args.almacen_a = "agentes/ejemplo/almacen_equipo_ejemplo.md"
            args.team_b = "Beta"
            args.agent_b = "agentes/ejemplo/agent.md"
            args.almacen_b = "agentes/ejemplo/almacen_equipo_ejemplo.md"
            cmd_play(args)
            Prompt.ask("\nPartida finalizada. Presiona Enter para volver")

        elif choice == "3":
            from core.engine import validate_game_config
            from core.tournament import discover_agents
            
            # Defaults
            custom_board = 10
            custom_ships = [5, 4, 3, 3, 2]
            custom_turns = 50
            custom_model = SETTINGS.get("default_model", "groq/llama-3.1-8b-instant")
            
            agents_list = discover_agents("agentes")
            team_a_idx = 0
            team_b_idx = min(1, len(agents_list) - 1) if agents_list else 0
            
            while True:
                console.clear()
                console.print("\n[bold cyan]-- Configuración de Partida Personalizada --[/bold cyan]")
                console.print(f"1. Tamaño del tablero \[6-10] (actual: {custom_board})")
                console.print(f"2. Configuración de cajas (actual: {custom_ships})")
                console.print(f"3. Máximo de turnos (actual: {custom_turns})")
                console.print(f"4. Modelo de IA (actual: {custom_model})")
                
                team_a_name = agents_list[team_a_idx].name if agents_list else "Ninguno"
                team_b_name = agents_list[team_b_idx].name if agents_list else "Ninguno"
                console.print(f"5. Seleccionar equipos (actual: {team_a_name} vs {team_b_name})")
                console.print("6. ▶ INICIAR PARTIDA")
                console.print("7. [red]Cancelar[/red]")
                
                sub_choice = Prompt.ask("\nSelecciona una opción", choices=["1", "2", "3", "4", "5", "6", "7"], default="6")
                
                if sub_choice == "1":
                    custom_board = IntPrompt.ask("Tamaño del tablero (6-10)", default=custom_board)
                elif sub_choice == "2":
                    ships_str = Prompt.ask("Tamaños de cajas separados por comas (ej: 3,2,2)", default=",".join(map(str, custom_ships)))
                    try:
                        custom_ships = [int(s.strip()) for s in ships_str.split(",")]
                    except ValueError:
                        console.print("[red]Formato inválido. Usa números separados por comas.[/red]")
                        time.sleep(1)
                elif sub_choice == "3":
                    custom_turns = IntPrompt.ask("Máximo de turnos", default=custom_turns)
                elif sub_choice == "4":
                    custom_model = Prompt.ask("Modelo de IA", default=custom_model)
                elif sub_choice == "5":
                    if not agents_list:
                        console.print("[red]No se encontraron agentes en la carpeta 'agentes/'.[/red]")
                        time.sleep(1.5)
                        continue
                    console.print("\n[bold]Equipos disponibles:[/bold]")
                    for i, ag in enumerate(agents_list, 1):
                        console.print(f"{i}. {ag.name}")
                    idx_a = IntPrompt.ask("Selecciona el equipo A (número)", default=team_a_idx + 1)
                    idx_b = IntPrompt.ask("Selecciona el equipo B (número)", default=team_b_idx + 1)
                    
                    if 1 <= idx_a <= len(agents_list) and 1 <= idx_b <= len(agents_list):
                        team_a_idx = idx_a - 1
                        team_b_idx = idx_b - 1
                    else:
                        console.print("[red]Selección inválida.[/red]")
                        time.sleep(1.5)
                elif sub_choice == "6":
                    # Validate before starting
                    try:
                        validate_game_config(custom_board, custom_ships)
                    except ValueError as e:
                        console.print(f"\n[bold red]Error de Configuración:[/bold red] {e}")
                        Prompt.ask("Presiona Enter para continuar")
                        continue
                    
                    if not agents_list:
                        console.print("\n[bold red]No hay equipos seleccionados o disponibles.[/bold red]")
                        Prompt.ask("Presiona Enter para continuar")
                        continue
                        
                    # Show summary
                    console.clear()
                    console.print("[bold green]-- Resumen de Configuración --[/bold green]")
                    console.print(f"Tablero: {custom_board}x{custom_board}")
                    console.print(f"Cajas: {custom_ships}")
                    console.print(f"Turnos: {custom_turns}")
                    console.print(f"Modelo: {custom_model}")
                    console.print(f"Enfrentamiento: {agents_list[team_a_idx].name} vs {agents_list[team_b_idx].name}")
                    
                    confirm = Prompt.ask("\n¿Iniciar partida?", choices=["s", "n"], default="s")
                    if confirm.lower() == "s":
                        args.command = "play"
                        args.model = custom_model
                        args.board_size = custom_board
                        args.ship_sizes = custom_ships
                        args.max_turns = custom_turns
                        
                        agent_a = agents_list[team_a_idx]
                        agent_b = agents_list[team_b_idx]
                        
                        args.team_a = agent_a.name
                        args.agent_a = str(agent_a.agent_md_path)
                        args.almacen_a = str(agent_a.almacen_path)
                        
                        args.team_b = agent_b.name
                        args.agent_b = str(agent_b.agent_md_path)
                        args.almacen_b = str(agent_b.almacen_path)
                        
                        cmd_play(args)
                        Prompt.ask("\nPartida finalizada. Presiona Enter para volver")
                        break
                elif sub_choice == "7":
                    break

        elif choice == "4":
            console.print("[yellow]Saliendo...[/yellow]")
            break


# ── Argument parser ───────────────────────────────────────────────────────────


def build_parser() -> argparse.ArgumentParser:
    # Common arguments for both CLI and interactive mode
    base_parser = argparse.ArgumentParser(add_help=False)
    base_parser.add_argument(
        "--model",
        default=SETTINGS.get("default_model", os.getenv("DEFAULT_MODEL", "gemini/gemini-1.5-pro")),
        help="LiteLLM model identifier  (default: %(default)s)",
    )
    base_parser.add_argument(
        "--no-visual",
        action="store_true",
        help="Disable the Rich terminal dashboard (useful for CI / logging).",
    )
    base_parser.add_argument(
        "--sleep",
        type=float,
        default=float(SETTINGS.get("api_sleep", os.getenv("API_SLEEP", "0.0"))),
        help="Wait N seconds between moves (remote models) (default: %(default)s)",
    )
    base_parser.add_argument(
        "--max-tokens",
        type=int,
        default=int(SETTINGS.get("max_tokens", os.getenv("MAX_TOKENS", "150"))),
        help="Max tokens to generate per move (default: %(default)s)",
    )
    base_parser.add_argument(
        "--ui-sleep",
        type=float,
        default=float(SETTINGS.get("ui_sleep", os.getenv("UI_SLEEP", "1.2"))),
        help="Slow down UI rendering by N seconds (default: %(default)s)",
    )
    base_parser.add_argument(
        "--board-size",
        type=int,
        default=int(SETTINGS.get("board_size", 10)),
        help="Grid size (6 to 10) (default: %(default)s)",
    )
    base_parser.add_argument(
        "--max-turns",
        type=int,
        default=int(SETTINGS.get("max_turns", 50)),
        help="Max turns per match (default: %(default)s)",
    )
    
    def parse_ship_sizes(s: str | list) -> list[int]:
        if isinstance(s, list):
            return [int(x) for x in s]
        s = s.strip("[]")
        return [int(x.strip()) for x in s.split(",")]

    base_parser.add_argument(
        "--ship-sizes",
        type=parse_ship_sizes,
        default=SETTINGS.get("ship_sizes", [5, 4, 3, 3, 2]),
        help="Ship sizes comma-separated, e.g. 3,2,2 (default: %(default)s)",
    )

    parser = argparse.ArgumentParser(
        prog="garment-strike",
        description="Garment Strike - AI Supply Chain Simulation Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
        parents=[base_parser]
    )

    sub = parser.add_subparsers(dest="command", required=False)

    # -- play ------------------------------------------------------------------
    play = sub.add_parser("play", help="Partida única entre dos equipos.", parents=[base_parser])
    play.add_argument("--team-a", required=True, metavar="NAME", help="Nombre del equipo A.")
    play.add_argument("--agent-a", required=True, metavar="PATH", help="Ruta al agent.md del equipo A.")
    play.add_argument("--almacen-a", required=True, metavar="PATH", help="Ruta al almacen_*.md del equipo A.")
    play.add_argument("--team-b", required=True, metavar="NAME", help="Nombre del equipo B.")
    play.add_argument("--agent-b", required=True, metavar="PATH", help="Ruta al agent.md del equipo B.")
    play.add_argument("--almacen-b", required=True, metavar="PATH", help="Ruta al almacen_*.md del equipo B.")

    # -- tournament ------------------------------------------------------------
    tour = sub.add_parser("tournament", help="Torneo Round Robin con todos los equipos.", parents=[base_parser])
    tour.add_argument(
        "--agents-dir",
        default="agentes",
        metavar="DIR",
        help="Carpeta con subcarpetas de equipos  (default: agentes/).",
    )
    tour.add_argument(
        "--output",
        default="tournament_results.json",
        metavar="FILE",
        help="Archivo JSON de resultados  (default: tournament_results.json).",
    )

    return parser


# ── Entry point ───────────────────────────────────────────────────────────────


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    try:
        if args.command == "play":
            cmd_play(args)
        elif args.command == "tournament":
            cmd_tournament(args)
        else:
            run_interactive_menu(args)
    except KeyboardInterrupt:
        console.print("\n[yellow]Partida interrumpida por el usuario.[/yellow]")
        sys.exit(0)
    except FileNotFoundError as exc:
        console.print(f"[red]Archivo no encontrado: {exc}[/red]")
        sys.exit(1)
    except ValueError as exc:
        console.print(f"[red]Error de configuración: {exc}[/red]")
        sys.exit(1)
    except Exception as exc:
        console.print(f"[red]Error inesperado: {exc}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
