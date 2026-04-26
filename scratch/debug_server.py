import time
from core.api import start_api_server

if __name__ == "__main__":
    print("Iniciando servidor de depuración en http://127.0.0.1:8000")
    print("Presiona Ctrl+C para detenerlo.")
    try:
        start_api_server()
    except KeyboardInterrupt:
        print("\nServidor detenido.")
