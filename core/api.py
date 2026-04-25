from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
import asyncio
import json

app = FastAPI()

# Almacén de eventos en memoria para que la web pueda recuperar el estado actual al recargar
class TacticalState:
    def __init__(self):
        self.current_event = None
        self.subscribers = []

    async def broadcast(self, event: dict):
        self.current_event = event
        for ws in self.subscribers:
            try:
                await ws.send_json(event)
            except:
                pass

state = TacticalState()

@app.websocket("/ws/tactical")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    state.subscribers.append(websocket)
    
    # Si ya hay un evento activo, se lo enviamos de inmediato al conectar
    if state.current_event:
        await websocket.send_json(state.current_event)
        
    try:
        while True:
            # Mantener conexión viva
            data = await websocket.receive_text()
            # Podríamos recibir acks aquí si fuera necesario
    except WebSocketDisconnect:
        state.subscribers.remove(websocket)

@app.post("/api/event")
async def post_event(event: dict):
    """El motor llama a este endpoint para enviar una instrucción táctica."""
    await state.broadcast(event)
    return {"status": "broadcasted"}

def start_api_server(host="127.0.0.1", port=8000):
    import uvicorn
    uvicorn.run(app, host=host, port=port, log_level="error")
