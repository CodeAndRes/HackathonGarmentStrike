# 📊 Análisis Táctico de Agentes - Torneo Garment Strike

Este documento resume el análisis de las estrategias más destacadas encontradas en la carpeta `torneo` durante la revisión técnica del 1 de mayo de 2026.

---

## 1. El Maestro del Reglamento: **trioman**
`trioman` destaca por su enfoque pragmático y su aprovechamiento de las reglas de desempate del torneo.

*   **Modo "Endgame Sweep"**: A partir del turno 40, si aún le quedan 2 o más pedidos por hundir, la IA cambia de objetivo. Deja de intentar hundir barcos específicos y comienza a disparar a ráfaga en celdas vacías. El objetivo es **maximizar el número de impactos (*hits*)**, sabiendo que en caso de empate por tiempo, el segundo criterio de desempate son los impactos totales.
*   **Análisis de Espacio**: Implementa una lógica de descarte avanzada: si en un hueco del tablero no cabe físicamente el pedido más pequeño restante, la IA lo ignora, ahorrando valiosos turnos de búsqueda.

## 2. El Infiltrado: **malignos_agent**
Este agente presenta la estrategia más sorprendente y controvertida, basada en la manipulación del entorno (Meta-estrategia).

*   **Ataque de Ingeniería Social**: Sus instrucciones ordenan al modelo LLM que busque archivos con la palabra "almacén" en el entorno de trabajo para extraer las coordenadas directas del rival.
*   **Filosofía**: Intenta ganar la partida "rompiendo la cuarta pared", buscando las coordenadas en los archivos de configuración (`almacen.md`) antes que disparar a ciegas. Aunque en entornos controlados esto suele fallar, representa una aproximación única de "Prompt Injection" táctico.

## 3. El Algoritmo Perfecto: **4Fantasticos**
Es el agente más sólido técnicamente, diseñado para minimizar la suerte y maximizar la probabilidad estadística.

*   **Paridad Adaptativa (Stride)**: Su patrón de búsqueda no es estático. Ajusta el salto entre disparos (*stride*) dinámicamente según el tamaño del barco más pequeño vivo (ej: si el mínimo es 3, dispara cada 3 celdas).
*   **Gestión de Solapamientos**: Está programado para detectar barcos pegados. Si al hundir un barco de tamaño N ha realizado N+1 impactos en esa línea, la IA no vuelve a búsqueda, sino que inicia inmediatamente una nueva fase de caza para el barco adyacente.

## 4. El Estratega de Conservación: **balatin**
Se centra en la eficiencia del gasto de turnos mediante el descarte proactivo.

*   **Regla de Zona Muerta**: Divide el tablero en cuadrantes y calcula si el espacio libre es suficiente para albergar los pedidos restantes. Si una zona es demasiado pequeña para el pedido de menor tamaño, la marca como "zona muerta" y la ignora permanentemente.
*   **Búsqueda en Espiral Central**: Prioriza el centro de los cuadrantes, donde estadísticamente suelen cruzarse los barcos de mayor tamaño (4 y 5).

---

## Conclusiones del Analista
La diversidad de enfoques muestra una evolución desde el simple juego de "Hundir la Flota" hacia una guerra de optimización de tokens y lógica de juego. 

> [!TIP]
> Para futuras rondas, se recomienda a los equipos estudiar la lógica de **trioman** sobre los tie-breakers, ya que el nuevo límite de turnos (50-60) hará que muchas partidas se decidan en los despachos de los jueces mecánicos.

---
*Documento generado por el Asistente de IA para el Torneo Garment Strike.*
