# Diagnóstico: ¿Por qué costó tanto cargar los nuevos agentes?

## Resumen Ejecutivo

El problema tuvo **3 causas encadenadas**, cada una bloqueando la siguiente. No fue un solo fallo, sino una cadena de dependencias que hicieron que algo conceptualmente simple (cambiar unos `.md` en una carpeta) se convirtiera en una odisea.

---

## 🔍 Causa 1: El `.venv` Original se Corrompió

### Qué pasó
- El entorno virtual original (`.venv`) fue creado el **11/04/2026** y se modificó por última vez el **25/04/2026**.
- En algún momento entre el 25/04 y el 29/04, este entorno **se corrompió completamente**: no tiene `pip.exe`, no tiene `python.exe`, y Windows no puede ni listar su contenido (`Get-Item .venv` → `PathNotFound`).
- El directorio `.venv` todavía aparece en `list_dir` pero es un **fantasma**: su estructura interna está rota.

### Consecuencia
- Tuviste que crear un **segundo entorno virtual** (`.venv2`) para poder ejecutar cualquier cosa.
- El `.venv2` tiene la configuración correcta (Python 3.13.7 vía `uv 0.10.4`) y todas las dependencias instaladas.
- Pero el servidor del torneo (`uvicorn`) que estaba corriendo en memoria **seguía usando el proceso viejo** del `.venv` original.

### Cómo se podría haber evitado
- **Usar `uv` con lockfiles** (`uv.lock`) para poder recrear el entorno en segundos si se corrompe.
- **No tener dos `.venv*` simultáneamente**, ya que crea confusión sobre cuál está activo.

---

## 🔍 Causa 2: El Servidor No Recargaba el Código (Sin Hot-Reload)

### Qué pasó
El servidor del torneo se lanzaba así:
```powershell
python -m uvicorn server.tournament_api:app --port 8080
```

**Sin el flag `--reload`**. Esto significa que uvicorn carga todo el código Python **una sola vez** al arrancar y nunca más vuelve a leer los archivos `.py` del disco.

### La cadena de desgracias
1. El servidor se arrancó con el código **viejo** (antes de mi fix `self.all_agents = self._discover_agents()`).
2. Yo modifiqué `bracket_engine.py` para que redescubriera los agentes al hacer setup.
3. **Pero el proceso uvicorn seguía ejecutando la versión antigua del código** que tenía en memoria.
4. Por eso, al pulsar "Inicializar Torneo", seguía mostrando los equipos viejos: el código que corría no incluía el re-escaneo.

### Evidencia
Se detectaron **dos procesos uvicorn simultáneos** (PIDs 29736 y 30908), ambos sirviendo el puerto 8080. Esto indica que se intentó relanzar el servidor sin matar el anterior, lo cual agravó el problema.

### Cómo se podría haber evitado
- **Lanzar uvicorn con `--reload`** durante desarrollo:
  ```powershell
  python -m uvicorn server.tournament_api:app --port 8080 --reload
  ```
  Esto hace que uvicorn vigile los archivos `.py` y se reinicie automáticamente cuando detecta cambios.
- **Matar el proceso anterior** antes de relanzar. El comando de COMMANDS.md ya lo documenta, pero no se ejecutó.

---

## 🔍 Causa 3: Estado Persistente en `bracket_state.json`

### Qué pasó
Incluso si el código se hubiera recargado correctamente, había otro bloqueo:

```python
# tournament_api.py, líneas 36-43
engine = BracketEngine()        # Escanea torneo/ → encuentra agentes viejos
engine.load_state()              # Carga logs/bracket_state.json → SOBREESCRIBE con estado viejo

if not engine.matches:           # Como SÍ había estado guardado...
    engine.setup_tournament()    # ...NUNCA se ejecuta el setup automático
```

El archivo `logs/bracket_state.json` contenía los nombres de los equipos anteriores (`becario_logistico`, `halcon_tactico`, etc.). Al arrancar, el servidor:
1. Escaneaba la carpeta `torneo/` (encontrando los nuevos).
2. **Inmediatamente después**, cargaba el `bracket_state.json` con los equipos viejos.
3. Como el estado ya tenía partidas (`engine.matches` no estaba vacío), **no se volvía a hacer setup**.

### Solución que apliqué
Añadí `self.all_agents = self._discover_agents()` al inicio de `setup_tournament()`, para que al pulsar "Inicializar" en la web, forzara un re-escaneo. Pero como el servidor no recargaba el código (Causa 2), este fix no surtió efecto hasta que se reinició manualmente el servidor con el nuevo `.venv2`.

### Cómo se podría haber evitado
- El endpoint `/reset` debería también **forzar un re-escaneo de agentes**, no solo borrar el JSON.
- Mejor aún: el endpoint `/setup` debería ser el responsable exclusivo de descubrir agentes, sin depender del estado del constructor.

---

## 📊 Cronología del Problema

| Momento | Qué pasó |
|---|---|
| Antes del 29/04 | Torneo funcionando con 8 equipos de ejemplo (commit `5492a5c`) |
| 29/04 ~16:47 | Tú reemplazas los `.md` en `torneo/` con los 8 equipos reales |
| 29/04 ~17:03 | Preguntas "¿por qué no carga los nuevos equipos?" |
| 29/04 ~17:06 | Yo detecto que `bracket_state.json` tiene los nombres viejos |
| 29/04 ~17:06 | Aplico fix en `bracket_engine.py` (re-escaneo en `setup_tournament`) |
| 29/04 ~17:09 | **Sigue sin funcionar** porque el servidor uvicorn no recargó el código |
| 29/04 ~17:11 | Detecto 2 procesos uvicorn zombie. Intento matar procesos → cancelado por ti |
| 29/04 → 01/05 | Tú resuelves el problema reconstruyendo el entorno (`.venv2`) y relanzando |

---

## ✅ Lecciones Aprendidas y Recomendaciones

### 1. Siempre usar `--reload` en desarrollo
```diff
- python -m uvicorn server.tournament_api:app --port 8080
+ python -m uvicorn server.tournament_api:app --port 8080 --reload
```

### 2. Un solo entorno virtual
Eliminar `.venv` (el corrupto) y renombrar `.venv2` a `.venv` para evitar confusión:
```powershell
Remove-Item .venv -Recurse -Force -ErrorAction SilentlyContinue
Rename-Item .venv2 .venv
```

### 3. Mejorar el endpoint `/reset`
```python
@app.get("/reset")
def reset_tournament():
    if os.path.exists("logs/bracket_state.json"):
        os.remove("logs/bracket_state.json")
    engine.matches = {}
    engine.all_agents = engine._discover_agents()  # ← FORZAR re-escaneo
    return {"status": "Tournament reset", "agents_found": len(engine.all_agents)}
```

### 4. Agregar un script de "kill & restart" limpio
Añadir a `COMMANDS.md`:
```powershell
# Reinicio limpio del torneo (mata procesos + relanza)
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep 2
.\.venv\Scripts\python.exe -m uvicorn server.tournament_api:app --port 8080 --reload
```

### 5. Logging de diagnóstico en el motor
El `BracketEngine` debería imprimir qué agentes encuentra cada vez que escanea:
```python
def _discover_agents(self):
    agents = [...]
    print(f"[BRACKET] Agentes descubiertos: {[a.name for a in agents]}")
    return agents
```

---

> [!IMPORTANT]
> **La causa raíz fue la falta de `--reload` en uvicorn.** Si hubiera estado activo, el fix en `bracket_engine.py` habría surtido efecto inmediatamente sin necesidad de reiniciar nada. Las otras causas (venv corrupto, estado persistente) agravaron el problema pero no lo habrían causado por sí solas.
