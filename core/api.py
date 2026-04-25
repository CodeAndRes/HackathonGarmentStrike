import asyncio
import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import json

# Silenciar logs ruidosos de asyncio en Windows
logging.getLogger("asyncio").setLevel(logging.CRITICAL)

app = FastAPI()

class TacticalState:
    def __init__(self):
        self.current_event = None
        self.subscribers = []
        self.ready_event = asyncio.Event()

    async def broadcast(self, event: dict):
        self.current_event = event
        for ws in self.subscribers:
            try:
                await ws.send_json(event)
            except:
                pass

    async def wait_for_ready(self, timeout=30.0):
        try:
            # Esperamos un tiempo generoso por si el frontend se refresca
            await asyncio.wait_for(self.ready_event.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            print("⚠️ Timeout táctico: El motor continúa por seguridad.")
        finally:
            self.ready_event.clear()

state = TacticalState()

@app.websocket("/ws/tactical")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    state.subscribers.append(websocket)
    if state.current_event:
        try:
            await websocket.send_json(state.current_event)
        except: pass
        
    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            if msg.get("status") == "READY_FOR_IMPACT":
                state.ready_event.set()
    except (WebSocketDisconnect, ConnectionResetError):
        pass # Ignorar desconexiones ruidosas de Streamlit
    finally:
        if websocket in state.subscribers:
            state.subscribers.remove(websocket)

@app.post("/api/event")
async def post_event(event: dict):
    await state.broadcast(event)
    return {"status": "broadcasted"}

@app.get("/api/state")
async def get_state():
    try:
        with open("logs/game_state.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"error": "state_not_found"}

@app.get("/api/wait_ready")
async def wait_ready():
    await state.wait_for_ready()
    return {"status": "ready"}

def start_api_server(host="127.0.0.1", port=8000):
    import uvicorn
    uvicorn.run(app, host=host, port=port, log_level="critical")
