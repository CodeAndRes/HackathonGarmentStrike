# ESTRATEGIA GARMENT STRIKE — AGENTE TÁCTICO v2

## FASE 1: BÚSQUEDA
Usa patrón de paridad: dispara solo donde (fila_número + columna_número) sea PAR.
Este patrón garantiza detectar cualquier pedido de tamaño ≥2 usando solo
la mitad del tablero. Es matemáticamente óptimo e imbatible en eficiencia.

Orden de disparo dentro del patrón:
1. Empieza por los centros de los 4 cuadrantes del tablero actual.
   Los pedidos de tamaño 4 y 3 tienen alta probabilidad de atravesarlos.
2. Continúa rotando entre cuadrantes en espiral desde borde hacia interior.

Regla de zona muerta: si el espacio libre restante en una zona es menor
al tamaño del pedido más pequeño que aún no has hundido, IGNORA esa zona
por completo y avanza. No malgastes turnos en huecos imposibles.

## FASE 2: CAZA (tras primer impacto)
1. Dispara en cruz alrededor del impacto: Este → Oeste → Sur → Norte.
   Salta casillas ya disparadas o fuera del tablero.
2. Segundo impacto: el eje queda fijado (horizontal o vertical).
   Persigue SOLO en esa línea en ambas direcciones hasta encontrar
   "Agua" o el borde. No compruebes laterales: es desperdicio puro.
3. Pedido hundido: retoma el patrón de paridad exactamente donde lo dejaste.

## FASE 3: MEMORIA Y AJUSTE
- NUNCA repitas casilla disparada.
- Los pedidos pueden estar pegados entre sí. Tras hundir uno, NO descartes
  casillas adyacentes: retoma el patrón ciegamente.
- Una vez fijado el eje, descarta inmediatamente las direcciones perpendiculares.
- Busca pedidos de tamaño 4 y 3 primero: son los más fáciles de interceptar
  con el patrón de paridad (exponen 2 casillas pares cada uno).

## REGLA DE ORO
Patrón de paridad → centros de cuadrante primero → caza direccional
con eje fijo → vuelve al patrón. Sin improvisar. Sin repetir. Sin desperdiciar.