"""
core/api.py
───────────
Servidor FastAPI ligero para el Dashboard Táctico en tiempo real.
Expone:
  - WebSocket /ws/tactical  → Push de eventos al dashboard HTML
  - GET /api/state           → Último estado (fallback para reconexión)
  - POST /api/event          → Recibe eventos del motor de juego
"""
import asyncio
import json
import logging
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

logging.getLogger("asyncio").setLevel(logging.CRITICAL)

app = FastAPI()

# Permitir conexiones desde cualquier origen (el HTML se abre como file://)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class TacticalState:
    def __init__(self):
        self.current_event = None
        self.subscribers: list[WebSocket] = []

    async def broadcast(self, event: dict):
        self.current_event = event
        dead = []
        for ws in self.subscribers:
            try:
                await ws.send_json(event)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.subscribers.remove(ws)

state = TacticalState()

@app.websocket("/ws/tactical")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    state.subscribers.append(websocket)
    # Enviar estado actual al conectarse (para reconexión)
    if state.current_event:
        try:
            await websocket.send_json(state.current_event)
        except Exception:
            pass
    try:
        while True:
            await websocket.receive_text()  # Keep-alive
    except (WebSocketDisconnect, ConnectionResetError, Exception):
        pass
    finally:
        if websocket in state.subscribers:
            state.subscribers.remove(websocket)

@app.post("/api/event")
async def post_event(event: dict):
    await state.broadcast(event)
    return {"status": "ok"}

@app.get("/api/state")
async def get_state():
    if state.current_event:
        return state.current_event
    try:
        p = Path("logs/game_state.json")
        if p.exists():
            return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {"error": "no_state"}

# Servir el dashboard HTML directamente
@app.get("/")
async def serve_dashboard():
    html_path = Path("frontend/index.html")
    if html_path.exists():
        return FileResponse(html_path, media_type="text/html")
    return HTMLResponse("<h1>Dashboard not found</h1>", status_code=404)

def start_api_server(host="127.0.0.1", port=8000):
    import uvicorn
    # Eliminamos install_signal_handlers para evitar incompatibilidad con versiones antiguas
    uvicorn.run(app, host=host, port=port, log_level="critical")
