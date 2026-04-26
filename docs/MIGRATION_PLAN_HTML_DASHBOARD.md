# 🚀 Plan de Migración: Streamlit → HTML/JS Nativo (Dashboard Táctico)

> **Rama origen**: `feature/tactical-js-bridge`
> **Rama de trabajo**: `feature/html-native-dashboard`
> **Prioridad**: Fluidez visual > Estética > Funcionalidad adicional
> **Fecha**: 26 Abril 2026

---

## 📋 RESUMEN EJECUTIVO

Reemplazar el frontend Streamlit (`frontend/`) por una página HTML nativa que se conecta por WebSocket al servidor FastAPI existente (`core/api.py`). El motor de juego (`core/tournament.py`) dejará de usar `time.sleep()` para escenificación y simplemente emitirá eventos. El HTML renderizará animaciones de forma nativa.

### Qué se CREA
- `frontend/index.html` — Dashboard completo (HTML + CSS + JS en un solo archivo)

### Qué se MODIFICA
- `core/tournament.py` — Eliminar sleeps, fix bug doble `apply_move()`, simplificar emisión de eventos
- `core/api.py` — Limpiar y robustecer el WebSocket broadcast
- `main.py` — Actualizar opción 4 del menú para abrir `index.html` en lugar de Streamlit

### Qué NO se toca
- `core/engine.py` — Intacto
- `core/llm_client.py` — Intacto
- `core/visualizer.py` — Intacto (dashboard de terminal sigue funcionando)
- `agentes/`, `templates/`, `tests/` — Intactos

---

## 🔧 PASO 0: Preparación

```bash
cd c:\Projects\BT-Supply-Impulse
git checkout feature/tactical-js-bridge
git pull
git checkout -b feature/html-native-dashboard
```

---

## 🔧 PASO 1: Modificar `core/api.py`

El servidor FastAPI actual ya funciona. Solo necesita pequeños ajustes.

### Archivo: `core/api.py`

Reemplazar el contenido COMPLETO del archivo con:

```python
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
    uvicorn.run(app, host=host, port=port, log_level="critical")
```

### Cambios clave respecto al original:
1. Añadido CORS middleware (el HTML puede abrirse como `file://` o servido)
2. Añadida ruta `GET /` que sirve `frontend/index.html`
3. Limpieza de WebSockets muertos en `broadcast()`
4. Eliminado `wait_for_ready` y `ready_event` (ya no necesarios)

---

## 🔧 PASO 2: Fix bug y simplificar `core/tournament.py`

### BUG CRÍTICO A CORREGIR

En la función `run_match()`, `game.apply_move()` se llama DOS VECES por turno:
- Línea ~354 (dentro del `try`, durante la escenificación de fases)
- Línea ~384 (fuera del `try`, siempre)

La segunda devuelve `already_shot` y corrompe estadísticas.

### Cambios necesarios en `run_match()` (líneas ~313-418):

Buscar este bloque (dentro del `try`, líneas ~338-362):

```python
                # -- FASE 0: RESET --
                if export_json:
                    _write_game_state(game, override_telemetry={current: {"strategy": "", "reasoning": "", "cursor": "focus"}})
                time.sleep(0.5) 

                # -- FASE 1: OBJETIVO --
                if export_json:
                    _write_game_state(game, override_telemetry={current: {"strategy": estrategia, "reasoning": "", "cursor": "strategy"}})
                time.sleep(1.5) 

                # -- FASE 2: ANÁLISIS --
                if export_json:
                    _write_game_state(game, override_telemetry={current: {"strategy": estrategia, "reasoning": razon, "cursor": "reasoning"}})
                time.sleep(3.0)

                # -- FASE 3: IMPACTO --
                result = game.apply_move(col, row, razon, estrategia)
                if export_json:
                    _write_game_state(game, override_telemetry={current: {"strategy": estrategia, "reasoning": razon, "cursor": "impact"}})
                time.sleep(1.0)

                # -- FASE 4: RESULTADO FINAL --
                if export_json:
                    _write_game_state(game) 
                time.sleep(3.0) 
```

**REEMPLAZAR** todo ese bloque con:

```python
                # Emitir telemetría pre-disparo (el frontend anima a su ritmo)
                if export_json:
                    _write_game_state(game, override_telemetry={current: {
                        "strategy": estrategia,
                        "reasoning": razon,
                        "cursor": "aiming",
                        "target": move.coordenada
                    }})
```

Luego buscar este bloque (fuera del `try`, líneas ~380-418):

```python
            if lat > 0:
                lats[current].append(lat)

            # -- ESCENA 3: IMPACTO (Se ejecuta el movimiento, desaparece el cursor) --
            result = game.apply_move(col, row, razon, estrategia)
            if result in ("hit", "sunk"):
                hits_count[current] += 1

            if export_json:
                _write_game_state(game)
```

**REEMPLAZAR** con:

```python
            if lat > 0:
                lats[current].append(lat)

            # Ejecutar el movimiento UNA SOLA VEZ
            result = game.apply_move(col, row, razon, estrategia)
            if result in ("hit", "sunk"):
                hits_count[current] += 1

            if export_json:
                _write_game_state(game)
            
            # Pequeña pausa para que el frontend procese el evento
            if export_json:
                time.sleep(0.3)
```

También buscar el bloque "ESCENA 0" (líneas ~313-316):

```python
            # -- ESCENA 0: RESET Y FOCO (Borrar textos del equipo actual para el inicio del turno) --
            if export_json:
                _write_game_state(game, override_telemetry={current: {"strategy": "", "reasoning": "", "cursor": None}})
            time.sleep(1.0) # 2 ciclos de polling
```

**REEMPLAZAR** con:

```python
            # Reset telemetría del equipo activo antes de pedir el movimiento
            if export_json:
                _write_game_state(game, override_telemetry={current: {"strategy": "", "reasoning": "", "cursor": None}})
```

### Resumen de cambios en tournament.py:
1. **Eliminar la primera llamada a `game.apply_move()`** (la de línea ~354 dentro del try)
2. **Eliminar todos los `time.sleep()` de escenificación** (0.5, 1.5, 3.0, 1.0, 3.0 = 10 segundos)
3. **Mantener solo un `time.sleep(0.3)`** después del apply_move para dar margen al WebSocket
4. **Añadir campo `target`** en la telemetría pre-disparo para que el frontend muestre la coordenada objetivo

---

## 🔧 PASO 3: Crear `frontend/index.html`

Este es el archivo principal. Es un single-file HTML con CSS y JS embebido.

### Estructura del layout (3 columnas):

```
┌──────────────────────────────────────────────────────────────────┐
│  ⚡ GARMENT STRIKE              LIVE │ TURNO #14 │ ALPHA 3/5 ...│
├─────────────────┬──────────────┬─────────────────────────────────┤
│                 │   SCOREBOARD │                                 │
│  TABLERO A      │   3  VS  2   │  TABLERO B                     │
│  (10x10 grid)   │              │  (10x10 grid)                  │
│                 │  MOVIMIENTOS │                                 │
│                 │  [log list]  │                                 │
├─────────────────┴──────────────┴─────────────────────────────────┤
│  TELEMETRÍA A (OBJETIVO/ANÁLISIS)  │  TELEMETRÍA B              │
├────────────────────────────────────┴─────────────────────────────┤
│  PANTALLA DE VICTORIA (overlay, solo al terminar)               │
└──────────────────────────────────────────────────────────────────┘
```

### Esquema JSON de entrada (el que llega por WebSocket)

Este es el contrato. El JSON que `serialize_game_state()` ya produce tiene esta forma:

```json
{
    "turn": 14,
    "turn_agent": "team_a",
    "team_a": {
        "name": "ALPHA",
        "pedidos_encajados": 3,
        "total_pedidos": 5,
        "prendas_encajadas": 12,
        "fleet": { "1,0": "P1", "2,0": "P1" },
        "board": [["~","#","X","O"], ...]
    },
    "team_b": { ... },
    "comms": [
        {
            "turn": 14,
            "agent": "A",
            "coord": "G7",
            "result": "HIT",
            "icon": "👕",
            "reasoning": "Detected pattern..."
        }
    ],
    "telemetry": {
        "team_a": {
            "strategy": "Hunt & Target",
            "reasoning": "Analyzing sector G...",
            "cursor": "aiming",
            "target": "G7"
        },
        "team_b": { "strategy": "...", "reasoning": "...", "cursor": null }
    },
    "finished": false,
    "winner": null
}
```

### Símbolos del board y su significado visual:
| Símbolo | Significado | Render |
|---------|-------------|--------|
| `~` | Agua / desconocido | Celda vacía oscura |
| `#` | Barco propio (no tocado) | Caja holográfica con borde neón del equipo |
| `X` | Impacto (hit o sunk) | Caja con icono de prenda 👕 + glow naranja |
| `O` | Fallo (miss) | Prenda caída/desvanecida (opacidad baja) |

### Fleet dict:
Las claves son `"fila,columna"` (0-indexed). El valor es el `ship_id` (ej: `"P1"`). Se usa para saber qué celdas pertenecen al mismo barco (para bordes inteligentes: si dos celdas adyacentes tienen el mismo ship_id, no dibujar borde entre ellas).

### Especificación del CSS

#### Variables raíz (copiar del design_system.py actual):
```css
:root {
    --bg-deep: #050a0e;
    --panel-bg: rgba(13, 17, 23, 0.9);
    --accent-alpha: #00ff88;
    --accent-beta: #ff4b4b;
    --text-main: #e6edf3;
    --grid-line: #1f2428;
}
```

#### Fuentes:
```css
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;600;700;900&family=JetBrains+Mono:wght@300;400;700&display=swap');
```

- **Orbitron**: Todos los títulos, badges, números de turno, coordenadas
- **JetBrains Mono**: Texto de log, razonamiento, stats

#### Animaciones necesarias (CSS puro):
1. **`@keyframes cellFlash`** — Cuando una celda cambia de estado: flash blanco 0.3s
2. **`@keyframes neonPulse`** — Parpadeo suave del borde de barcos no descubiertos: 2s infinite
3. **`@keyframes pulseRed`** — LED rojo LIVE: 1s infinite
4. **`@keyframes fadeIn`** — Para nuevas entradas del log: 0.5s
5. **`@keyframes victoryGlow`** — Para la pantalla de victoria: pulso dorado 2s

### Especificación del JavaScript

#### Conexión WebSocket:
```javascript
function connect() {
    const ws = new WebSocket(`ws://${window.location.hostname || '127.0.0.1'}:8000/ws/tactical`);
    ws.onmessage = (e) => {
        const state = JSON.parse(e.data);
        updateDashboard(state);
    };
    ws.onclose = () => setTimeout(connect, 1000); // Auto-reconexión
}
```

#### Función `updateDashboard(state)`:
1. Actualizar header (turno, scores)
2. Actualizar tableros con **diff**: comparar `state.team_X.board` con el estado anterior celda por celda. Solo re-renderizar celdas que cambiaron. Añadir clase `cell-flash` a las celdas nuevas.
3. Actualizar log: si hay nuevos `comms`, prepend al log con clase `fade-in`
4. Actualizar telemetría: mostrar strategy/reasoning del equipo activo. Si `cursor === "aiming"`, mostrar la coordenada target con efecto de parpadeo.
5. Si `state.finished === true`, mostrar overlay de victoria.

#### Función `renderBoard(teamKey, teamData)`:
Generar una grid CSS. Para cada celda:
- Obtener `sym = board[row][col]`
- Obtener `shipId = fleet["row,col"]` (puede no existir)
- Calcular conexiones (si celdas adyacentes tienen el mismo shipId → no borde entre ellas)
- Renderizar SVG del barco usando la misma lógica de `holographics.py`:
  - `#` → Caja cerrada (borde neón + cinta central + etiqueta)
  - `X` → Caja abierta con prenda dentro (icono SVG de camiseta)
  - `O` → Prenda caída (mismo SVG, rotado 45°, opacidad 0.2)
  - `~` → Vacía

#### SVG de la caja (portar de `holographics.py`):

La caja 3D se dibuja en un viewBox de 100x100 con estos elementos:
1. **Perímetro exterior** — Rectángulo con margen de 7px. Omitir lados donde hay conexión.
2. **Fondo interior** — Rectángulo más pequeño (inset 10px adicionales). Líneas finas.
3. **Diagonales de profundidad** — Conectan esquinas exteriores con interiores (efecto 3D).
4. **Solapas** — Triángulos en los lados no conectados (efecto de caja abierta).
5. **Paredes internas** — Fills semi-transparentes entre perímetro y fondo.
6. **Icono de prenda** (solo en estado `X`/hit) — Path SVG de camiseta centrado.

Para caja cerrada (`#`):
1. Rectángulo con fill semi-transparente del color del equipo
2. Línea central (cinta de sellado) horizontal o vertical según orientación
3. Etiqueta blanca pequeña en esquina inferior derecha

#### SVG de la prenda (para miss `O`):
Mismo path de camiseta que en hit, pero rotado 45° y con opacidad 0.2.

```
Path de camiseta (copiar exacto):
M20.38 3.46L16 2a4 4 0 01-8 0L3.62 3.46a2 2 0 00-1.34 2.23l.58 3.47a1 1 0 00.99.84H6v10c0 1.1.9 2 2 2h8a2 2 0 002-2V10h2.15a1 1 0 00.99-.84l.58-3.47a2 2 0 00-1.34-2.23z
```

### Pantalla de Victoria

Cuando `state.finished === true`:
- Overlay semi-transparente negro sobre todo el dashboard
- Texto grande centrado: "🏆 VICTORIA: [nombre del ganador]" o "⚖️ EMPATE"
- Animación de glow dorado pulsante
- Estadísticas finales (turnos, hits, accuracy)

---

## 🔧 PASO 4: Actualizar `main.py`

### Cambio en la opción 4 del menú interactivo (líneas ~252-276):

Buscar el bloque `elif choice == "4":` (el del Dashboard, líneas 252-276):

```python
        elif choice == "4":
            import subprocess
            import webbrowser
            
            console.print("\n[bold blue]Iniciando Dashboard Táctico...[/bold blue]")
            cmd = [sys.executable, "-m", "streamlit", "run", "Interface.py"]
            # ... (streamlit launch code)
```

**REEMPLAZAR** con:

```python
        elif choice == "4":
            import webbrowser
            
            console.print("\n[bold blue]Iniciando Dashboard Táctico...[/bold blue]")
            console.print("[dim]El servidor API se inicia automáticamente al lanzar una partida.[/dim]")
            console.print("[dim]Abriendo el dashboard en el navegador...[/dim]")
            webbrowser.open("http://127.0.0.1:8000")
            
            Prompt.ask("\nPresiona Enter para volver al menú")
```

### Cambio en opción 2 del menú (partida de ejemplo):

Buscar la línea que dice `console.print("1. Clásica (Terminal)")` (línea ~239) y el bloque de visualización.

Cambiar el texto de la opción 2:
```python
            console.print("2. Táctica (Dashboard Web — abrir http://127.0.0.1:8000)")
```

### NOTA: El servidor FastAPI ya se inicia en `cmd_play()` (línea 66):
```python
threading.Thread(target=start_api_server, daemon=True).start()
```
Esto sigue siendo correcto. No tocar.

---

## 🔧 PASO 5: Limpiar el segundo `elif choice == "4"` duplicado

En `main.py`, hay un bloque duplicado/muerto:

Línea ~424-425:
```python
                elif sub_choice == "7":
                    break
```
Y línea ~427-429:
```python
        elif choice == "4":
            console.print("[yellow]Saliendo...[/yellow]")
            break
```

El `elif choice == "4"` de la línea 427 corresponde realmente a `choice == "5"` (Salir). Verificar que el flujo del menú siga correcto tras los cambios.

---

## 🧪 PASO 6: Verificación

### Test 1: Verificar que los tests unitarios siguen pasando
```bash
cd c:\Projects\BT-Supply-Impulse
python -m pytest tests/ -v
```
No debería fallar ninguno porque no tocamos engine.py ni llm_client.py.

### Test 2: Partida offline con dashboard HTML
1. Ejecutar: `python main.py`
2. Elegir opción 2 (Partida de Ejemplo)
3. Seleccionar modelo: elegir `ollama/` local o escribir `offline`
4. Seleccionar modo: **Táctica (Web)**
5. Abrir `http://127.0.0.1:8000` en el navegador
6. Verificar:
   - [ ] Los tableros se renderizan correctamente
   - [ ] Las celdas se actualizan sin parpadeo
   - [ ] Los impactos (X) tienen animación flash
   - [ ] La telemetría muestra estrategia y razonamiento
   - [ ] El log de movimientos se actualiza en tiempo real
   - [ ] Al terminar la partida, aparece la pantalla de victoria
   - [ ] No hay scrollbar visible (zero-scroll)

### Test 3: Verificar que no hay doble disparo
Revisar el archivo `reports/turns_*.log` después de una partida. NO deben aparecer entradas duplicadas de `ALREADY_SHOT` consecutivas para el mismo agente y coordenada.

### Test 4: Verificar reconexión
1. Durante una partida, cerrar la pestaña del navegador
2. Volver a abrir `http://127.0.0.1:8000`
3. El dashboard debe mostrar el estado actual inmediatamente (gracias al `current_event` en el WebSocket)

---

## 📁 Estructura final esperada

```
frontend/
├── index.html          ← NUEVO (dashboard completo)
├── Interface.py        ← Se conserva pero ya no se usa activamente
├── TacticalBridge.py   ← Se conserva pero ya no se usa activamente
├── README.md           ← Actualizar con nuevas instrucciones
└── src/                ← Se conserva como referencia de diseño
    ├── data/bridge.py
    ├── renderers/holographics.py  ← Referencia para portar SVGs
    └── styles/design_system.py    ← Referencia para portar CSS
```

---

## ⚠️ NOTAS IMPORTANTES PARA EL MODELO EJECUTOR

1. **No borrar archivos de Streamlit**. Solo crear el nuevo `index.html` y modificar los archivos indicados. Los archivos de Streamlit se conservan por si hay que hacer rollback.

2. **El contrato de datos NO cambia**. `serialize_game_state()` en `tournament.py` ya produce el JSON correcto. El HTML solo consume ese JSON.

3. **El servidor FastAPI ya se arranca en `cmd_play()`** (línea 66 de main.py). No crear otro.

4. **Los SVGs de `holographics.py` son la referencia visual**. El HTML debe producir el mismo efecto visual. Copiar la lógica de conexiones (smart borders) fielmente.

5. **El `index.html` debe ser autocontenido**: todo el CSS y JS embebido. No crear archivos separados. Las únicas dependencias externas son las Google Fonts (Orbitron y JetBrains Mono) cargadas por CDN.

6. **Probar siempre con modo `offline`** para no gastar tokens de API durante el desarrollo.

7. **La resolución objetivo es 1920x1080** (pantalla completa, sin scroll).

8. **Colores del equipo**: Alpha = `#00ff88` (verde neón), Beta = `#ff4b4b` (rojo neón). Estos NUNCA cambian.

---

*Plan creado el 25 de Abril 2026 por análisis del repositorio completo.*
