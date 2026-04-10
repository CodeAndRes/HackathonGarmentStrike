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

    llm_client = LLMClient(model=args.model)
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
    )


# ── Argument parser ───────────────────────────────────────────────────────────


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="garment-strike",
        description="Garment Strike – AI Supply Chain Simulation Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--model",
        default=os.getenv("DEFAULT_MODEL", "gemini/gemini-1.5-pro"),
        help="LiteLLM model identifier  (default: %(default)s)",
    )
    parser.add_argument(
        "--no-visual",
        action="store_true",
        help="Disable the Rich terminal dashboard (useful for CI / logging).",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    # ── play ──────────────────────────────────────────────────────────────────
    play = sub.add_parser("play", help="Partida única entre dos equipos.")
    play.add_argument("--team-a", required=True, metavar="NAME", help="Nombre del equipo A.")
    play.add_argument("--agent-a", required=True, metavar="PATH", help="Ruta al agent.md del equipo A.")
    play.add_argument("--almacen-a", required=True, metavar="PATH", help="Ruta al almacen_*.md del equipo A.")
    play.add_argument("--team-b", required=True, metavar="NAME", help="Nombre del equipo B.")
    play.add_argument("--agent-b", required=True, metavar="PATH", help="Ruta al agent.md del equipo B.")
    play.add_argument("--almacen-b", required=True, metavar="PATH", help="Ruta al almacen_*.md del equipo B.")

    # ── tournament ────────────────────────────────────────────────────────────
    tour = sub.add_parser("tournament", help="Torneo Round Robin con todos los equipos.")
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
