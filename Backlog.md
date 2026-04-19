# Garment Strike — Backlog & Roadmap

## 📝 Notas y Estrategia
- ⚠️ **Posible cambio de estrategia:** 
  - Los equipos programarán un módulo en python (`Brain.py`) que se encargue de decidir la estrategia.
  - El módulo puede consultar a la IA cada 10 turnos.
  - Se le pasa el historial completo de los (miss, hit y sunk) y la IA devolvería el cuadrante a atacar.
- **Roles:** Parece que hay problemas con la separación de roles de cada jugador. Parece que la IA está recordando y tomando decisiones estratégicas sobre las jugadas del oponente. No está bien definido el rol de cada jugador o el aislamiento de state.

---

## 📋 Tareas Pendientes
- [ ] **Tiro forzado:** Debe ser random pero excluyendo proactivamente las coordenadas que ya han sido atacadas.
- [ ] **Tiempos de latencia:** El sleep de 5 segundos igual no es necesario según los tiempos de la última partida. Reducir o volver dinámico.
- [ ] **Arquitectura Multi-Agente:** Posible combinación de dos modelos de IA para mejorar la estrategia.
  - Uno para ejecutar la estrategia y obedecer las reglas.
  - Otro para establecer la estrategia, delimitando zonas de búsqueda.
- [ ] **Retención de memoria LLM:** Probar la retención de memoria de la IA. Lo ideal es que se le pasen las reglas al inicio y luego solo el estado del tablero y las jugadas realizadas.
- [ ] **Seguridad/Config:** Separar el archivo de parámetros (settings) de la carga de las claves API-key (e.g., .env exclusivo o gestión de secretos).
- [ ] **Recuperación:** Posible envío de contexto mayor tras Fallback (error de validación).
- [ ] **Agentes Github:** Revisar la creación de posibles workflows y skills nuevas.
- [ ] La configuración de cajas de la partida personalizada queda un poco confusa, yo pensaba que debia ponerle parentesis!. 
- [ ] Emplezar a iterar con diferentes estrategias y ver como se comporta la IA.
- [ ] Aun hay terminos que hacen referencia al juego original undir la flota
- [ ] En la ventana de razonaminto se ve como el modelos habla en terminos de barcos y hundir etc...
- [ ] Podríamos ver el razonamiento de ambos jugadores
- [ ] Hacer mas grande el log de la partida en el frontend, el texto se corta 
- [ ] Error visible al cancelar la partida con Ctrl+C. 
    ```
       C:\Projects\BT-Supply-Impulse\core\engine.py:395: RuntimeWarning: [AlmacenParser] Formato inválido en 'agentes\\ejemplo\\almacen_equipo_ejemplo.md': Configuración de pedidos incorrecta. Esperado [3, 3, 2], recibido [5, 4, 3, 3, 2].. Usando layout aleatorio legal.
        ships, _, _ = cls.parse_with_status(filepath, size=size, ship_sizes=ship_sizes)

      Partida interrumpida por el usuario.
      PS C:\Projects\BT-Supply-Impulse>
    ```

---

## ✅ Tareas Completadas (Fases 1, 2 y 3)
- [x] Traducir en la respuesta del LLM los términos asociados a Battleship a terminología de Logística (`SUNK` -> Pedido Encajado, `HIT` -> Prenda encajada, `MISS` -> Prenda perdida).
- [x] Fijar / avisar del tamaño de la pantalla del terminal para que no se rompa el formato Rich.
- [x] Comprimir la información de celdas prohibidas/anteriores agrupadas por rangos (miss, hit y sunk) reduciendo tokens.
- [x] Organizar y parametrizar todas las pruebas unitarias para ser multiconfiguración (más de 170 tests activos).
- [x] Inyectar en los logs (`match_turns.log`) la fecha, hora y el modelo ejecutante.
- [x] Explorar y habilitar la posibilidad de usar distintos modelos de IA para cada jugador simultáneamente.
- [x] Crear un menú inicial interactivo completo con opciones de:
  - Tests
  - Partida normal y de Ejemplo
  - Partida personalizada / minimalista
  - Selección de modelos de IA y mapeo de equipos
- [x] Tamaño de tablero dinámico (`board_size`) completamente propagado en la clase Board y parseadores.
- [x] Configuración de barcos (pedidos) variables propagada por completo.
- [x] Asegurar la portabilidad con instrucciones claras de instalación, requerimientos y cómo obtener claves API de los distintos modelos soportados.
- [x] Modo Táctico: Exportación `game_state.json` en tiempo real para Dashboard externo.