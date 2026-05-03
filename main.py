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
import shutil
import yaml
import subprocess
import webbrowser
import atexit
from pathlib import Path

def kill_project_servers():
    """Surgical Tree Kill: Targets the API server and all its child workers."""
    try:
        # We find the PIDs and then use taskkill /T (Tree kill) to clean children
        cmd = 'Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like "*uvicorn*server.tournament_api:app*" } | ForEach-Object { taskkill /F /T /PID $_.ProcessId }'
        subprocess.run(["powershell", "-Command", cmd], capture_output=True, check=False)
    except:
        pass

# Register cleanup on exit
atexit.register(kill_project_servers)
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
    
    # Iniciar servidor de eventos tácticos solo si se solicita el modo táctico
    if getattr(args, 'tactical', False):
        server_thread = threading.Thread(target=start_api_server, daemon=True)
        server_thread.start()
        
        # CRÍTICO: Esperar a que el servidor esté listo antes de iniciar el motor
        time.sleep(1.5)
        console.print("[dim green]API táctica lista en http://127.0.0.1:8000[/dim green]")
    
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

    # Siempre creamos una carpeta de torneo "ad-hoc" para cumplir con la unificación
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    safe_name_a = "".join(c for c in args.team_a if c.isalnum())
    safe_name_b = "".join(c for c in args.team_b if c.isalnum())
    folder_name = f"torneos/Partida_{safe_name_a}_vs_{safe_name_b}_{timestamp}"
    output_dir = Path(folder_name)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Copiar agentes a la carpeta para que sea autocontenida
    shutil.copy(args.agent_a, output_dir / f"{args.team_a}.md")
    shutil.copy(args.almacen_a, output_dir / f"{args.team_a}.almacen.md")
    shutil.copy(args.agent_b, output_dir / f"{args.team_b}.md")
    shutil.copy(args.almacen_b, output_dir / f"{args.team_b}.almacen.md")
    
    from core.bracket_engine import BracketEngine
    engine = BracketEngine(tournament_dir=str(output_dir))
    engine.setup_tournament(seed_agents=[args.team_a, args.team_b], count=2)
    
    console.print(f"[dim]Carpeta de partida creada: {folder_name}[/dim]")

    match = run_match(
        config_a, config_b, llm_client, visual=not args.no_visual, 
        ui_sleep=args.ui_sleep, board_size=args.board_size,
        max_turns=args.max_turns,
        ship_sizes=args.ship_sizes,
        export_json=getattr(args, 'tactical', False),
        output_dir=output_dir,
        speed=getattr(args, 'speed', None)
    )

    winner_str = match.winner if match.winner else "EMPATE"
    console.print(f"\n[bold]Ganador:[/bold] {winner_str}")
    
    # Si teníamos un motor de bracket, actualizamos el estado final
    if output_dir:
        from core.bracket_engine import BracketMatch
        from dataclasses import asdict
        m_state = engine.matches.get("f1")
        if m_state:
            m_state.winner = winner_str
            m_state.status = "finished"
            m_state.result = asdict(match)
            engine.save_state()
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
        console.print("5. [bold white]Configurar Velocidad (Presets)[/bold white]")
        console.print("6. [cyan]Gran Torneo (Bracket)[/cyan]")
        console.print("7. [red]Salir[/red]")

        choice = Prompt.ask("\nSelecciona una opción", choices=["1", "2", "3", "4", "5", "6", "7"], default="7")

        if choice == "1":
            import subprocess
            console.print("\n[bold]Lanzando pytest...[/bold]")
            subprocess.run([sys.executable, "-m", "pytest", "tests/", "-v"])
            Prompt.ask("\nPresiona Enter para volver")

        elif choice == "2":
            # Partida de Ejemplo
            args.command = "play"
            args.team_a = "Alpha"
            args.agent_a = "agentes/Alpha/agent.md"
            args.almacen_a = "agentes/Alpha/almacen.md"
            args.team_b = "Beta"
            args.agent_b = "agentes/Beta/agent.md"
            args.almacen_b = "agentes/Beta/almacen.md"
            
            selected_model = pick_model_from_catalog(SETTINGS.get("default_model", "offline"))
            args.model = selected_model
            args.model_a = None
            args.model_b = None
            
            if Prompt.ask("\n¿Deseas iniciar la visualización táctica (Dashboard Web)?", choices=["s", "n"], default="n") == "s":
                args.tactical = True
                args.output = "partida_ejemplo.json"
            else:
                args.tactical = False
                args.output = None

            cmd_play(args)
            Prompt.ask("\nPartida finalizada. Presiona Enter para volver")

        elif choice == "3":
            # Partida Personalizada (Long block...)
            from core.engine import validate_game_config
            from core.tournament import discover_agents
            custom_board = 10
            custom_ships = [5, 4, 3, 3, 2]
            custom_turns = 50
            default_model = SETTINGS.get("default_model", "offline")
            custom_model_a = default_model
            custom_model_b = default_model
            custom_viz = "1"
            custom_save_file = None
            
            agents_list = discover_agents("agentes")
            team_a_idx = 0
            team_b_idx = min(1, len(agents_list) - 1) if agents_list else 0
            
            while True:
                console.clear()
                console.print("\n[bold cyan]-- Configuración de Partida Personalizada --[/bold cyan]")
                console.print(f"1. Tablero: {custom_board}x{custom_board}")
                console.print(f"2. Cajas: {custom_ships}")
                console.print(f"3. Turnos: {custom_turns}")
                console.print(f"4. Modelos (A: {custom_model_a} | B: {custom_model_b})")
                console.print(f"5. Equipos: {agents_list[team_a_idx].name if agents_list else 'N/A'} vs {agents_list[team_b_idx].name if agents_list else 'N/A'}")
                console.print(f"6. Visualización: {'Clásica' if custom_viz == '1' else 'Táctica'}")
                console.print(f"7. Guardar: {custom_save_file or 'No'}")
                console.print("8. [bold green]▶ INICIAR PARTIDA[/bold green]")
                console.print("9. [red]Cancelar[/red]")
                
                sub = Prompt.ask("\nSelecciona", choices=["1","2","3","4","5","6","7","8","9"], default="8")
                if sub == "9": break
                elif sub == "1": custom_board = IntPrompt.ask("Tamaño", default=custom_board)
                elif sub == "2": 
                    s = Prompt.ask("Cajas (ej: 3,2,2)", default=",".join(map(str, custom_ships)))
                    custom_ships = [int(x) for x in s.split(",")]
                elif sub == "3": custom_turns = IntPrompt.ask("Turnos", default=custom_turns)
                elif sub == "4":
                    custom_model_a = pick_model_from_catalog(custom_model_a)
                    if Prompt.ask("¿Usar el mismo para el equipo B?", choices=["s","n"], default="s") == "n":
                        custom_model_b = pick_model_from_catalog(custom_model_b)
                    else: custom_model_b = custom_model_a
                elif sub == "5":
                    for i, ag in enumerate(agents_list, 1): console.print(f"{i}. {ag.name}")
                    team_a_idx = IntPrompt.ask("Equipo A", default=team_a_idx+1) - 1
                    team_b_idx = IntPrompt.ask("Equipo B", default=team_b_idx+1) - 1
                elif sub == "6": custom_viz = Prompt.ask("Modo (1:Clásica, 2:Táctica)", choices=["1","2"], default="1")
                elif sub == "7": custom_save_file = Prompt.ask("Nombre archivo", default="partida.json")
                elif sub == "8":
                    args.command = "play"
                    args.model_a = custom_model_a
                    args.model_b = custom_model_b
                    args.board_size = custom_board
                    args.ship_sizes = custom_ships
                    args.max_turns = custom_turns
                    args.tactical = (custom_viz == "2")
                    args.team_a, args.agent_a, args.almacen_a = agents_list[team_a_idx].name, str(agents_list[team_a_idx].agent_md_path), str(agents_list[team_a_idx].almacen_path)
                    args.team_b, args.agent_b, args.almacen_b = agents_list[team_b_idx].name, str(agents_list[team_b_idx].agent_md_path), str(agents_list[team_b_idx].almacen_path)
                    args.output = custom_save_file
                    cmd_play(args)
                    Prompt.ask("Finalizado. Enter para volver")
                    break

        elif choice == "4":
            import webbrowser
            console.print("\n[bold blue]Abriendo Dashboard Táctico...[/bold blue]")
            webbrowser.open("http://127.0.0.1:8000")
            Prompt.ask("Presiona Enter para volver")

        elif choice == "5":
            speed = Prompt.ask("Velocidad", choices=["cinematic", "fast", "ultra"], default="fast")
            try:
                with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
                    conf = yaml.safe_load(f)
                conf["choreography"]["active_mode"] = speed.upper()
                with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
                    yaml.dump(conf, f, default_flow_style=False)
                console.print(f"[green](OK) Modo {speed.upper()} activado.[/green]")
                time.sleep(1)
            except Exception as e: console.print(f"[red]Error: {e}[/red]")

        elif choice == "6":
            import subprocess
            import webbrowser
            import shutil
            from core.bracket_engine import BracketEngine

            console.print("\n[bold cyan]-- Gestión de Torneos --[/bold cyan]")
            console.print("1. [green]Crear Nuevo Torneo[/green]")
            console.print("2. [yellow]Jugar Torneo Existente[/yellow]")
            console.print("3. [red]Cancelar[/red]")
            
            t_choice = Prompt.ask("Selecciona", choices=["1", "2", "3"], default="2")
            if t_choice == "3": continue
            
            selected_dir = None
            if t_choice == "1":
                t_name = Prompt.ask("Nombre del nuevo torneo")
                selected_dir = f"torneos/{t_name}"
                target_path = Path(selected_dir)
                target_path.mkdir(parents=True, exist_ok=True)
                dest_agents = target_path / "agentes"
                
                # 1. Preguntar tamaño primero
                count = IntPrompt.ask("¿Tamaño del torneo? (2, 4, 8)", choices=["2", "4", "8"], default=8)
                
                # 2. Descubrir agentes disponibles
                base_engine = BracketEngine(tournament_dir=".") 
                available_agents = base_engine._discover_agents()
                
                if len(available_agents) < count:
                    console.print(f"[red]Error: Solo hay {len(available_agents)} agentes disponibles, pero el torneo es de {count}.[/red]")
                    console.print("[yellow]Añade más carpetas a 'agentes/' y reintenta.[/yellow]")
                    continue

                # 3. Draft con validación estricta de cantidad
                to_copy = []
                while len(to_copy) != count:
                    console.print(f"\n[bold cyan]-- Draft de Agentes (Selecciona EXACTAMENTE {count}) --[/bold cyan]")
                    for i, agent in enumerate(available_agents, 1):
                        console.print(f"{i}. [green]{agent.name}[/green]")
                    
                    selection = Prompt.ask(f"\nSelecciona {count} números separados por coma", default="")
                    try:
                        idxs = [int(x.strip()) - 1 for x in selection.split(",")]
                        to_copy = [available_agents[i] for i in idxs if 0 <= i < len(available_agents)]
                        
                        if len(to_copy) != count:
                            console.print(f"[red]Error: Has seleccionado {len(to_copy)} agentes, pero se necesitan {count}.[/red]")
                            to_copy = [] # Reset para reintentar
                    except Exception:
                        console.print("[red]Entrada inválida. Usa números separados por comas.[/red]")
                        to_copy = []

                # 4. Copiado selectivo
                dest_agents.mkdir(parents=True, exist_ok=True)
                for agent in to_copy:
                    src_folder = agent.agent_md_path.parent
                    shutil.copytree(src_folder, dest_agents / agent.name, dirs_exist_ok=True)
                
                console.print(f"[green](OK) {len(to_copy)} agentes añadidos al torneo.[/green]")

                # 5. Inicializar el bracket
                engine = BracketEngine(tournament_dir=selected_dir)
                engine.setup_tournament(count=count)
                console.print(f"[green](OK) Torneo inicializado correctamente.[/green]")
            else:
                available = [str(d) for d in Path("torneos").iterdir() if d.is_dir()]
                if not available:
                    console.print("[red]No hay torneos guardados.[/red]")
                    continue
                for i, d in enumerate(available, 1): console.print(f"{i}. {Path(d).name}")
                t_idx = IntPrompt.ask("Selecciona", default=1)
                selected_dir = available[t_idx-1] if 1 <= t_idx <= len(available) else None
            
            if selected_dir:
                kill_project_servers() # Clean any previous zombie before starting
                env = os.environ.copy()
                env["TOURNAMENT_DIR"] = selected_dir
                # Launch FastAPI server with logging
                server_cmd = [sys.executable, "-m", "uvicorn", "server.tournament_api:app", "--port", "8080", "--reload"]
                log_path = target_path / "server.log"
                with open(log_path, "a", encoding="utf-8") as log_file:
                    subprocess.Popen(server_cmd, env=env, stdout=log_file, stderr=log_file, shell=(os.name == 'nt'))
                
                console.print(f"[green](OK) Servidor del Torneo iniciado en puerto 8080.[/green]")
                console.print(f"[dim]Logs disponibles en: {log_path}[/dim]")
                time.sleep(2)
                webbrowser.open("http://localhost:8080")
                Prompt.ask("Torneo en marcha. Presiona Enter para volver")

        elif choice == "7":
            kill_project_servers()
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
    base_parser.add_argument(
        "--speed",
        type=str,
        choices=["cinematic", "fast", "ultra"],
        default=None,
        help="Modo de velocidad de la coreografía (cinematic, fast, ultra)",
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
        import traceback
        console.print(f"[red]Error inesperado: {exc}[/red]")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
