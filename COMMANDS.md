# ⚡ GUÍA DE COMANDOS: Garment Strike

Este documento contiene los comandos esenciales para operar el motor de simulación, los torneos y las interfaces visuales.

---

## 1. Menú Interactivo (Recomendado)
La forma más sencilla de manejar todo el sistema es a través del menú principal.
```powershell
python main.py
```

---

## 2. Partidas Individuales (CLI)
Para lanzar un combate rápido entre dos agentes específicos desde la terminal:
```powershell
python main.py play --team-a "Alpha" --agent-a agentes/logistica_prime/agent.md --almacen-a agentes/logistica_prime/almacen_logistica_prime.md --team-b "Beta" --agent-b agentes/novato_aleatorio/agent.md --almacen-b agentes/novato_aleatorio/almacen_novato_aleatorio.md
```
*Añade `--tactical` al final si quieres que envíe datos al Dashboard Web.*

---

## 3. Sistema de Torneos

### Gran Torneo (Eliminatorias/Bracket)
Para lanzar el servidor del torneo (API + Web) manualmente:
```powershell
python -m uvicorn server.tournament_api:app --port 8080 --reload
```
*Interfaz disponible en:* `http://localhost:8080`

### Torneo Round-Robin (Todos contra todos)
Para lanzar un torneo rápido donde todos los agentes de la carpeta `/agentes` se enfrenten entre sí:
```powershell
python main.py tournament --agents-dir agentes --output results.json
```

---

## 4. Visualización y Dashboards

### Dashboard Táctico (Seguimiento de partida)
Si la partida está en marcha y quieres ver el tablero en tiempo real, tienes dos opciones:

**Opción A: Dashboard HTML Nativo (Recomendado)**
```powershell
python -m uvicorn core.api:app --port 8000 --reload
```
*Disponible en:* `http://localhost:8000`

**Opción B: Dashboard Streamlit (Legacy / Por si acaso)**
```powershell
python -m streamlit run frontend/Interface.py
```
*Disponible en:* `http://localhost:8501`

---

## 5. Utilidades y Diagnóstico

### Verificar si hay un combate activo (Torneo)
Comprueba en el estado del bracket si hay algún proceso `"running"`:
```powershell
Get-Content logs/bracket_state.json | ConvertFrom-Json | Get-Member -MemberType NoteProperty | ForEach-Object { (Get-Content logs/bracket_state.json | ConvertFrom-Json).$($_.Name) } | Where-Object { $_.status -eq "running" } | Select-Object match_id, team_a, team_b, status
```

### Limpiar procesos de red (Reset de puertos)
Si un puerto (8080 u 8000) se queda bloqueado:
```powershell
Get-Process | Where-Object { $_.CommandLine -like "*uvicorn*" } | Stop-Process -Force
```

### Verificar procesos de Python en ejecución
Muestra qué scripts de Python o servidores están activos actualmente:
```powershell
Get-WmiObject Win32_Process | Where-Object { $_.Name -eq "python.exe" } | Select-Object ProcessId, CommandLine | Format-List
```

### Matar todos los procesos de Python
**CUIDADO**: Esto cerrará inmediatamente cualquier script, servidor o dashboard de Python abierto.
```powershell
Stop-Process -Name "python" -Force
```

### Ejecutar Suite de Pruebas
Para verificar que el motor core funciona correctamente:
```powershell
python -m pytest tests/ -v
```

---

## 6. Gestión de Entorno
Asegúrate siempre de tener el entorno virtual activo:
```powershell
# Activar en Windows
.venv\Scripts\Activate.ps1
```
