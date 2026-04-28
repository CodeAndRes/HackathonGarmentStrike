"""
check_ready.py
--------------
Pre-hackathon readiness checker for Garment Strike.

Checks:
  1) Gemini API key presence
  2) Ollama local availability (localhost:11434)
  3) Agent folder validation and whether each team would trigger
     auto-generated board layout fallback.

Usage:
  python check_ready.py
  python check_ready.py --agents-dir agentes
"""
from __future__ import annotations

import argparse
import socket
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from core.engine import AlmacenParser

console = Console()


def check_gemini_key() -> tuple[bool, str]:
    import os

    key = os.getenv("GEMINI_API_KEY", "").strip()
    if key:
        return True, "GEMINI_API_KEY configurada"
    return False, "Falta GEMINI_API_KEY (crear .env o exportar variable)"


def check_ollama_running(host: str = "127.0.0.1", port: int = 11434) -> tuple[bool, str]:
    try:
        with socket.create_connection((host, port), timeout=1.2):
            return True, f"Ollama activo en {host}:{port}"
    except OSError as exc:
        return False, f"Ollama no responde en {host}:{port} ({exc})"


def validate_agents(agents_dir: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []

    if not agents_dir.exists():
        return [
            {
                "equipo": "(global)",
                "estado": "ERROR",
                "detalle": f"Carpeta no encontrada: {agents_dir}",
            }
        ]

    for f in sorted(agents_dir.glob("*.md")):
        if f.name.endswith(".almacen.md"):
            continue

        team = f.stem
        # Almacenes a validar por fase
        almacenes_to_check = [
            (f"{team}.almacen.md", "q"),
            (f"{team}.almacen.s.md", "s"),
            (f"{team}.almacen.f.md", "f"),
        ]

        # Cargar reglas de settings para validar correctamente cada fase
        import yaml
        try:
            with open("settings.yaml", "r", encoding="utf-8") as settings_f:
                all_rules = yaml.safe_load(settings_f).get("tournament", {}).get("rounds", {})
        except:
            all_rules = {}

        for filename, phase in almacenes_to_check:
            almacen_path = agents_dir / filename
            
            if not almacen_path.exists():
                if phase == "q": # El principal es obligatorio o usará fallback
                    rows.append({"equipo": f"{team} ({phase})", "estado": "WARN", "detalle": f"Falta {filename}"})
                continue

            rules = all_rules.get(phase, {})
            size = rules.get("board_size", 10)
            ship_sizes = rules.get("ship_sizes", [5,4,3,3,2])

            ships, used_fallback, reason = AlmacenParser.parse_with_status(
                almacen_path, size=size, ship_sizes=ship_sizes, emit_warning=False
            )

            if used_fallback:
                rows.append({"equipo": f"{team} ({phase})", "estado": "WARN", "detalle": f"Error en {filename}: {reason}"})
            else:
                rows.append({"equipo": f"{team} ({phase})", "estado": "OK", "detalle": f"Archivo {filename} valido"})


    if not rows:
        rows.append(
            {
                "equipo": "(global)",
                "estado": "WARN",
                "detalle": f"No se encontraron archivos .md en {agents_dir}",
            }
        )

    return rows


def render_status(label: str, ok: bool, detail: str) -> None:
    color = "green" if ok else "red"
    icon = "OK" if ok else "FAIL"
    console.print(f"[{color}]{icon}[/{color}] [bold]{label}[/bold] - {detail}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Garment Strike readiness checker")
    parser.add_argument("--agents-dir", default="torneo", help="Carpeta de equipos")
    args = parser.parse_args()

    load_dotenv()

    console.print(Panel.fit("Garment Strike - Check Ready", border_style="cyan"))

    gemini_ok, gemini_msg = check_gemini_key()
    ollama_ok, ollama_msg = check_ollama_running()

    render_status("Gemini API", gemini_ok, gemini_msg)
    render_status("Ollama Local", ollama_ok, ollama_msg)

    rows = validate_agents(Path(args.agents_dir))

    tbl = Table(title="Validacion de equipos (/agentes)")
    tbl.add_column("Equipo", style="bold")
    tbl.add_column("Estado")
    tbl.add_column("Detalle")

    for row in rows:
        state = row["estado"]
        style = "green" if state == "OK" else "yellow" if state == "WARN" else "red"
        tbl.add_row(row["equipo"], f"[{style}]{state}[/{style}]", row["detalle"])

    console.print(tbl)

    has_error = any(r["estado"] == "ERROR" for r in rows)
    if has_error:
        console.print("\n[red]Resultado: NO LISTO[/red]")
        return 1

    has_warn = any(r["estado"] == "WARN" for r in rows) or (not gemini_ok) or (not ollama_ok)
    if has_warn:
        console.print("\n[yellow]Resultado: LISTO CON ADVERTENCIAS[/yellow]")
        return 0

    console.print("\n[green]Resultado: LISTO PARA HACKATHON[/green]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
