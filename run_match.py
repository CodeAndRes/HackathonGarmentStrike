
import subprocess
import sys

def run():
    print("[*] Iniciando Garment Strike...")
    
    command = [
        "python", "main.py", "play",
        "--team-a", "Equipo Alpha",
        "--agent-a", "agentes/ejemplo/agent.md",
        "--almacen-a", "agentes/ejemplo/almacen_equipo_ejemplo.md",
        "--team-b", "Equipo Beta",
        "--agent-b", "agentes/ejemplo/agent.md",
        "--almacen-b", "agentes/ejemplo/almacen_equipo_ejemplo2.md"
    ]
    
    try:
        # Ejecutamos y permitimos que la salida fluya directamente a la terminal
        subprocess.run(command, check=True)
    except KeyboardInterrupt:
        print("\n[!] Partida detenida por el usuario.")
    except Exception as e:
        print(f"\n[!] Error al ejecutar la partida: {e}")

if __name__ == "__main__":
    run()
