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
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, IntPrompt
from rich.rule import Rule

console = Console()

# Load .env if present (silently ignored if not found)
load_dotenv()


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
    )
    match = run_match(config_a, config_b, llm_client, visual=not args.no_visual)

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
            console.print("\n[bold cyan]-- Configuración de Partida Personalizada --[/bold cyan]")
            # Note: This is a simplified interactive setup. 
            # Could be expanded to list folders in agentes/
            args.command = "play"
            args.team_a = Prompt.ask("Nombre Equipo A", default="Equipo_A")
            args.team_b = Prompt.ask("Nombre Equipo B", default="Equipo_B")
            
            models = [
                "gemini/gemini-1.5-pro",
                "gemini/gemini-3-flash-preview",
                "ollama/llama3:latest",
                "ollama/gemma4:e4b",
                "ollama/phi3:mini",
                "ollama/qwen3.5:0.8b"
            ]
            console.print("\nModelos sugeridos:")
            for i, m in enumerate(models, 1):
                console.print(f"{i}. {m}")
            
            m_idx = IntPrompt.ask("Selecciona un modelo (o introduce nombre manual)", default=1)
            if 1 <= m_idx <= len(models):
                args.model = models[m_idx-1]
            else:
                args.model = Prompt.ask("Nombre del modelo (LiteLLM format)")
            
            # Simple path defaults for now
            args.agent_a = "agentes/ejemplo/agent.md"
            args.almacen_a = "agentes/ejemplo/almacen_equipo_ejemplo.md"
            args.agent_b = "agentes/ejemplo/agent.md"
            args.almacen_b = "agentes/ejemplo/almacen_equipo_ejemplo.md"
            
            cmd_play(args)
            Prompt.ask("\nPartida finalizada. Presiona Enter para volver")

        elif choice == "4":
            console.print("[yellow]Saliendo...[/yellow]")
            break


# ── Argument parser ───────────────────────────────────────────────────────────


def build_parser() -> argparse.ArgumentParser:
    # Common arguments for both CLI and interactive mode
    base_parser = argparse.ArgumentParser(add_help=False)
    base_parser.add_argument(
        "--model",
        default=os.getenv("DEFAULT_MODEL", "gemini/gemini-1.5-pro"),
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
        default=float(os.getenv("API_SLEEP", "0.0")),
        help="Wait N seconds between moves (remote models) (default: %(default)s)",
    )
    base_parser.add_argument(
        "--max-tokens",
        type=int,
        default=int(os.getenv("MAX_TOKENS", "150")),
        help="Max tokens to generate per move (default: %(default)s)",
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
