#!/usr/bin/env python3
"""
monitor_match.py
───────────────
Monitorea una partida en progreso y muestra logs de turnos.
"""
import time
import subprocess
import sys
from pathlib import Path
from datetime import datetime


def run_match_with_logs():
    """Lanza la partida con output en tiempo real."""
    cmd = [
        sys.executable,
        "main.py",
        "--model",
        "ollama/llama3:latest",
        "play",
        "--team-a",
        "Equipo Alpha",
        "--agent-a",
        "agentes/ejemplo/agent.md",
        "--almacen-a",
        "agentes/ejemplo/almacen_equipo_ejemplo.md",
        "--team-b",
        "Equipo Beta",
        "--agent-b",
        "agentes/ejemplo/agent.md",
        "--almacen-b",
        "agentes/ejemplo/almacen_equipo_ejemplo2.md",
    ]

    print("[*] Lanzando partida con monitoreo de logs...")
    print(f"[*] {datetime.now().strftime('%H:%M:%S')} - Inicio\n")

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    turn_count = 0
    start_time = time.time()

    try:
        for line in process.stdout:
            line = line.rstrip()
            if line:
                print(line)
                if "turno" in line.lower() or "turn" in line.lower():
                    turn_count += 1
                    elapsed = time.time() - start_time
                    print(f"    ⏱ Turno {turn_count} | {elapsed:.1f}s")

        returncode = process.wait()
        elapsed = time.time() - start_time
        print(
            f"\n[✓] Partida completada en {elapsed:.1f}s (≈{turn_count} turnos)"
        )
        sys.exit(returncode)

    except KeyboardInterrupt:
        print("\n[!] Partida interrumpida por el usuario.")
        process.terminate()
        sys.exit(1)


if __name__ == "__main__":
    run_match_with_logs()
