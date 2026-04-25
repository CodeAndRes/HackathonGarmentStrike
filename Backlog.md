# Garment Strike — Backlog & Roadmap

## 📝 Notas y Estrategia
- ⚠️ **Posible cambio de estrategia:** 
  - Los equipos programarán un módulo en python (`Brain.py`) que se encargue de decidir la estrategia.
  - El módulo puede consultar a la IA cada 10 turnos.
  - Se le pasa el historial completo de los (miss, hit y sunk) y la IA devolvería el cuadrante a atacar.
- **Roles:** Parece que hay problemas con la separación de roles de cada jugador. Parece que la IA está recordando y tomando decisiones estratégicas sobre las jugadas del oponente. No está bien definido el rol de cada jugador o el aislamiento de state.

---

## 📋 Tareas Pendientes (Próximos Pasos)

### Frontend & UI (En progreso por Agente Frontend)
- [ ] **Visibilidad del Panel de Resultados**: Centrar y ampliar el panel de puntuación actual.
- [ ] **Resaltar Turno Actual**: Crear un panel que muestre qué jugador está jugando, la coordenada y el resultado inmediato.
- [ ] **Highlight Táctico**: Resaltar el tablero que recibe el disparo en cada turno para guiar al espectador.
- [ ] **Fin de Partida en Web**: Crear una pantalla clara de victoria/derrota cuando termina el torneo.
- [ ] **Sonidos y Animaciones**: Añadir SFX (impactos, hundimientos) y animaciones visuales (Miss/Hit).
- [ ] **Crear una segunda pantalla para el torneo**: 8 jugadores, 4 partidas en primera fase, 2 en segunda fase y 1 en la final.
 
### Backend & Core
- [ ] **Tiempos de latencia**: El sleep de 5 segundos se puede volver dinámico o aplicar un 'Exponential Backoff' basado en los códigos de error de la API (ej. HTTP 429).
- [ ] **Agentes Híbridos / Fallback Automático**: Si el LLM falla por completo tras N reintentos, implementar un algoritmo simple en Python (ej. tiro en cruz o damero) para que el agente siga jugando en vez de fallar o tirar aleatoriamente.
- [ ] **Manejo de Errores Vistoso**: Ocultar el traceback feo al cancelar la partida con `Ctrl+C` y mostrar un mensaje limpio de "Partida interrumpida".

---

## 🚀 Mejoras Arquitectónicas Futuras (Backlog Avanzado)
- [ ] **Torneos Concurrentes**: Usar `concurrent.futures.ThreadPoolExecutor` en `run_tournament` para jugar múltiples enfrentamientos de Round-Robin simultáneamente.
- [ ] **Caché Inteligente de Determinismo**: Si dos agentes deterministas (temp 0.0) se enfrentan a un tablero idéntico, cachear la respuesta para ahorrar llamadas a la API y tokens.
- [ ] **Modo "Máquina del Tiempo" (Replay)**: Añadir un `st.slider` en el dashboard para rebobinar una partida finalizada y hacer un "VOD review" turno a turno.
- [ ] **Personalización de Equipos**: Permitir definir avatares y códigos de color HEX en los archivos `agent.md` para que el dashboard los inyecte automáticamente.
- [ ] **Perfiles YAML para Torneos**: Crear pre-sets de torneos (ej. `ligas_rapidas.yaml`) en lugar de depender únicamente de argumentos de consola.


---

## ✅ Tareas Completadas Recientes (Fases 1 a 4)
- [x] **Visibilidad de Telemetría Dual**: Integrado en el Frontend para ver el razonamiento y estrategia de AMBOS jugadores.
- [x] **Zero-Scroll en Logs**: Optimizado el panel de logs de movimientos para que el texto no se corte y mantenga el enfoque sin scroll excesivo.
- [x] **Limpieza de Terminología**: Adaptación completa de términos marítimos a logísticos ("Pedidos Encajados", "Prendas Perdidas") en todo el core y UI.
- [x] **Instrumentación LLM**: Captura de tokens (Prompt/Completion) y telemetría de errores en tiempo real inyectada en `match_turns.log` y reportes Markdown.
- [x] **Recarga de Configuración en Caliente**: `.env` y `settings.yaml` se recargan al inicio de cada partida sin necesidad de reiniciar la aplicación.
- [x] **Configuraciones Elásticas**: Arreglado el menú interactivo para aceptar tamaños de tablero y pedidos variables de forma robusta.
- [x] Traducir en la respuesta del LLM los términos asociados a Battleship a terminología de Logística.
- [x] Compresión de la información de celdas prohibidas/anteriores para ahorrar tokens.
- [x] Parametrización de pruebas unitarias (más de 170 tests activos).
- [x] Exportación `game_state.json` en tiempo real para Dashboard externo.

