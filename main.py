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
import threading
from core.api import start_api_server

console = Console()
SETTINGS_PATH = Path("settings.yaml")

def reload_configurations():
    """Reloads .env and settings.yaml into memory."""
    global SETTINGS, MODELS_CATALOG, FULL_SETTINGS
    load_dotenv(override=True)
    if SETTINGS_PATH.exists():
        try:
            with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
                FULL_SETTINGS = yaml.safe_load(f) or {}
                SETTINGS = FULL_SETTINGS.get("engine", {})
        except Exception as e:
            SETTINGS = {}
    else:
        SETTINGS = {}
    MODELS_CATALOG = FULL_SETTINGS.get("models_catalog", {})

# Initial load
reload_configurations()


# ── Sub-command handlers ──────────────────────────────────────────────────────


def cmd_play(args: argparse.Namespace) -> None:
    """Run a single match between two agent configs."""
    reload_configurations()
    
    # Iniciar servidor de eventos tácticos (Real-time Bridge)
    threading.Thread(target=start_api_server, daemon=True).start()
    
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

    # Resolve per-team models (F3.2: mixed models)
    model_a = getattr(args, 'model_a', None) or args.model
    model_b = getattr(args, 'model_b', None) or args.model

    def _get_client(m):
        if m == "offline":
            from core.llm_client import OfflineLLMClient
            return OfflineLLMClient(board_size=args.board_size)
        return LLMClient(
            model=m,
            api_sleep=args.sleep,
            max_tokens=args.max_tokens,
            board_size=args.board_size,
        )

    if model_a == model_b:
        # Same model → single client (saves memory)
        llm_client = _get_client(model_a)
    else:
        # Different models → per-team clients
        console.print(f"[bold cyan]⚔ Modo mixto:[/bold cyan] {model_a} vs {model_b}")
        llm_client = {
            args.team_a: _get_client(model_a),
            args.team_b: _get_client(model_b),
        }

    match = run_match(
        config_a, config_b, llm_client, visual=not args.no_visual, 
        ui_sleep=args.ui_sleep, board_size=args.board_size,
        max_turns=args.max_turns,
        ship_sizes=args.ship_sizes,
        export_json=getattr(args, 'tactical', False)
    )

    winner_str = match.winner if match.winner else "EMPATE"
    console.print(f"\n[bold]Ganador:[/bold] {winner_str}")
    console.print(f"[bold]Turnos totales:[/bold] {match.total_turns}")
    
    acc_a = (match.hits_a / match.shots_a * 100) if match.shots_a > 0 else 0
    acc_b = (match.hits_b / match.shots_b * 100) if match.shots_b > 0 else 0

    console.print(
        f"[bold]Disparos:[/bold]  {args.team_a}={match.shots_a} ({acc_a:.1f}% hit) | {args.team_b}={match.shots_b} ({acc_b:.1f}% hit)"
    )
    console.print(
        f"[bold]Latencia:[/bold]  {args.team_a}={match.avg_latency_a/1000.0:.2f}s | {args.team_b}={match.avg_latency_b/1000.0:.2f}s"
    )
    console.print(
        f"[bold]Tokens (P/C):[/bold] {args.team_a}={match.prompt_tokens_a}/{match.completion_tokens_a} | {args.team_b}={match.prompt_tokens_b}/{match.completion_tokens_b}"
    )
    if match.errors_a > 0 or match.errors_b > 0:
        console.print(
            f"[bold red]Errores API:[/bold red] {args.team_a}={match.errors_a} | {args.team_b}={match.errors_b}"
        )

    if getattr(args, 'output', None):
        from core.tournament import TournamentReport, _save_results
        report = TournamentReport()
        report.matches.append(match)
        report.update_standings(match)
        _save_results(report, args.output)


def cmd_tournament(args: argparse.Namespace) -> None:
    """Run a Round-Robin tournament."""
    reload_configurations()
    from core.tournament import run_tournament, discover_agents

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


# ── Interactive Menu Helpers ──────────────────────────────────────────────────


def pick_model_from_catalog(current_model: str) -> str:
    """Helper to pick a model from the recommended catalog in settings.yaml."""
    if not MODELS_CATALOG:
        return Prompt.ask("Modelo de IA", default=current_model)
    
    console.print("\n[bold cyan]-- Catálogo de Modelos Recomendados --[/bold cyan]")
    providers = list(MODELS_CATALOG.keys())
    for i, provider in enumerate(providers, 1):
        console.print(f"{i}. [bold]{provider.upper()}[/bold]")
    console.print(f"{len(providers)+1}. [dim]Otro (Manual)[/dim]")
    
    p_idx = IntPrompt.ask("Selecciona proveedor", default=1)
    if 1 <= p_idx <= len(providers):
        provider = providers[p_idx-1]
        models = MODELS_CATALOG[provider]
        console.print(f"\n[bold]{provider.upper()} - Modelos:[/bold]")
        for j, model in enumerate(models, 1):
            console.print(f"  {j}. {model}")
        
        m_idx = IntPrompt.ask("Selecciona modelo", default=1)
        if 1 <= m_idx <= len(models):
            return models[m_idx-1]
    
    return Prompt.ask("Introduce el nombre del modelo manualmente", default=current_model)


def run_interactive_menu(args: argparse.Namespace) -> None:
    """Interactively ask the user what they want to do."""
    while True:
        reload_configurations()
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
        console.print("4. [blue]Abrir Dashboard Táctico (Web)[/blue]")
        console.print("5. [red]Salir[/red]")

        choice = Prompt.ask("\nSelecciona una opción", choices=["1", "2", "3", "4", "5"], default="5")

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
            args.almacen_b = "agentes/ejemplo/almacen_equipo_ejemplo2.md"
            
            # Use catalog for Example Match too
            default_model = SETTINGS.get("default_model", "groq/llama-3.1-8b-instant")
            selected_model = pick_model_from_catalog(default_model)
            args.model = selected_model
            args.model_a = None
            args.model_b = None
            
            console.print("\n[bold]Modo de Visualización:[/bold]")
            console.print("1. Clásica (Terminal)")
            console.print("2. Táctica (Web Dashboard)")
            v = Prompt.ask("Elige", choices=["1", "2"], default="1")
            args.tactical = (v == "2")
            
            if Prompt.ask("\n¿Deseas guardar el informe detallado (JSON/Markdown) en la carpeta 'reports/'?", choices=["s", "n"], default="n") == "s":
                args.output = "partida_ejemplo.json"
            else:
                args.output = None

            cmd_play(args)
            Prompt.ask("\nPartida finalizada. Presiona Enter para volver")

        elif choice == "4":
            import subprocess
            import webbrowser
            
            console.print("\n[bold blue]Iniciando Dashboard Táctico...[/bold blue]")
            # Launch streamlit in the background using the current python environment
            cmd = [sys.executable, "-m", "streamlit", "run", "Interface.py"]
            
            try:
                # Use Popen to run in background without blocking the menu
                subprocess.Popen(
                    cmd, 
                    cwd="frontend", 
                    stdout=subprocess.DEVNULL, 
                    stderr=subprocess.DEVNULL,
                    shell=(os.name == 'nt') # Necessary on Windows for some envs
                )
                console.print("[green](OK) Servidor Streamlit lanzado en segundo plano.[/green]")
                console.print("[dim]Abriendo navegador en http://localhost:8501...[/dim]")
                time.sleep(2)
                webbrowser.open("http://localhost:8501")
            except Exception as e:
                console.print(f"[red]Error al lanzar el dashboard: {e}[/red]")
            
            Prompt.ask("\nPresiona Enter para volver al menú")

        elif choice == "3":
            from core.engine import validate_game_config
            from core.tournament import discover_agents
            
            # Defaults
            custom_board = 10
            custom_ships = [5, 4, 3, 3, 2]
            custom_turns = 50
            default_model = SETTINGS.get("default_model", "groq/llama-3.1-8b-instant")
            custom_model_a = default_model
            custom_model_b = default_model
            custom_viz = "1" # 1: Clásica, 2: Táctica
            custom_save_file = None
            custom_save_label = "No"
            
            agents_list = discover_agents("agentes")
            team_a_idx = 0
            team_b_idx = min(1, len(agents_list) - 1) if agents_list else 0
            
            while True:
                console.clear()
                console.print("\n[bold cyan]-- Configuración de Partida Personalizada --[/bold cyan]")
                console.print(f"1. Tamaño del tablero [6-10] (actual: {custom_board})")
                console.print(f"2. Configuración de cajas (actual: {custom_ships})")
                console.print(f"3. Máximo de turnos (actual: {custom_turns})")
                if custom_model_a == custom_model_b:
                    console.print(f"4. Modelo de IA (actual: {custom_model_a})")
                else:
                    console.print(f"4. Modelos de IA (A: {custom_model_a} | B: {custom_model_b})")
                
                team_a_name = agents_list[team_a_idx].name if agents_list else "Ninguno"
                team_b_name = agents_list[team_b_idx].name if agents_list else "Ninguno"
                console.print(f"5. Seleccionar equipos (actual: {team_a_name} vs {team_b_name})")
                viz_str = "Clásica (Terminal)" if custom_viz == "1" else "Táctica (Web Dashboard JSON)"
                console.print(f"6. Modo de Visualización (actual: {viz_str})")
                console.print(f"7. Guardar informe (actual: {custom_save_label})")
                console.print("8. [bold green]▶ INICIAR PARTIDA[/bold green]")
                console.print("9. [red]Cancelar[/red]")
                
                sub_choice = Prompt.ask("\nSelecciona una opción", choices=["1", "2", "3", "4", "5", "6", "7", "8", "9"], default="8")
                
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
                    console.print("\n  [bold]a.[/bold] Mismo modelo para ambos equipos")
                    console.print("  [bold]b.[/bold] Modelo diferente por equipo")
                    model_choice = Prompt.ask("  Elige", choices=["a", "b"], default="a")
                    if model_choice == "a":
                        custom_model_a = pick_model_from_catalog(custom_model_a)
                        custom_model_b = custom_model_a
                    else:
                        console.print("\n[bold]Configuración Equipo A:[/bold]")
                        custom_model_a = pick_model_from_catalog(custom_model_a)
                        console.print("\n[bold]Configuración Equipo B:[/bold]")
                        custom_model_b = pick_model_from_catalog(custom_model_b)
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
                    console.print("2. Táctica (Exportación JSON para Dashboard Web)")
                    custom_viz = Prompt.ask("Selecciona modo", choices=["1", "2"], default=custom_viz)
                elif sub_choice == "7":
                    save_name = Prompt.ask("Nombre del archivo (ej: mi_partida.json) o 'no'", default="no")
                    if save_name.lower() != "no":
                        if not save_name.endswith(".json"): save_name += ".json"
                        custom_save_file = save_name
                        custom_save_label = save_name
                    else:
                        custom_save_file = None
                        custom_save_label = "No"
                elif sub_choice == "8":
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
                    if custom_model_a == custom_model_b:
                        console.print(f"Modelo: {custom_model_a}")
                    else:
                        console.print(f"Modelo A: {custom_model_a}")
                        console.print(f"Modelo B: {custom_model_b}")
                    console.print(f"Enfrentamiento: {agents_list[team_a_idx].name} vs {agents_list[team_b_idx].name}")
                    
                    confirm = Prompt.ask("\n¿Iniciar partida?", choices=["s", "n"], default="s")
                    if confirm.lower() == "s":
                        args.command = "play"
                        args.model = custom_model_a  # fallback default
                        args.model_a = custom_model_a
                        args.model_b = custom_model_b
                        args.board_size = custom_board
                        args.ship_sizes = custom_ships
                        args.max_turns = custom_turns
                        args.tactical = (custom_viz == "2")
                        
                        agent_a = agents_list[team_a_idx]
                        agent_b = agents_list[team_b_idx]
                        
                        args.team_a = agent_a.name
                        args.agent_a = str(agent_a.agent_md_path)
                        args.almacen_a = str(agent_a.almacen_path)
                        
                        args.team_b = agent_b.name
                        args.agent_b = str(agent_b.agent_md_path)
                        args.almacen_b = str(agent_b.almacen_path)
                        args.output = custom_save_file
                        
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
    play.add_argument("--model-a", metavar="MODEL", default=None,
                      help="LLM model for team A (overrides --model). Enables mixed-model matches.")
    play.add_argument("--model-b", metavar="MODEL", default=None,
                      help="LLM model for team B (overrides --model). Enables mixed-model matches.")
    play.add_argument("--tactical", action="store_true", help="Modo táctico: genera game_state.json para dashboard web.")
    play.add_argument("--output", metavar="FILE", help="Si se especifica, guarda el informe en reports/ (ej: partida1.json)")

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
        console.print(f"[red]Error de configuracion: {exc}[/red]")
        sys.exit(1)
    except Exception as exc:
        console.print(f"[red]Error inesperado: {exc}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
