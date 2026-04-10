# 🎯 MANIFIESTO ESTRATÉGICO — Equipo Ejemplo (Hunt & Target)

> Agente de ejemplo para el Hackathon Garment Strike.
> Implementa la estrategia clásica "Hunt & Target" (Exploración + Caza).

---

## 1. Identidad del Agente

- **Nombre del Equipo:** Equipo Ejemplo
- **Versión de Estrategia:** 1.0
- **Fecha:** Abril 2026
- **Filosofía:** Primero exploro con patrón en damero para maximizar cobertura.
  Cuando impacto, cambio a modo caza persiguiendo la línea del pedido.

---

## 2. FASE DE EXPLORACIÓN (sin impactos activos)

### Patrón de búsqueda: Damero Optimizado

Dispara en celdas donde `(índice_columna + fila)` es **par**.
- A=0, B=1, C=2, D=3, E=4, F=5, G=6, H=7, I=8, J=9
- Ejemplo: A1 (0+1=1 impar → no), A2 (0+2=2 par → sí), B1 (1+1=2 par → sí)

Secuencia de prioridad por zona:
1. **Centro primero** (E5, F5, E6, F6, D5, G5, E4, E7)
2. **Cuadrante superior-izquierdo** (B2, D2, B4, D4, B6, D6)
3. **Cuadrante superior-derecho** (G2, I2, G4, I4, G6, I6)
4. **Cuadrante inferior-izquierdo** (B8, D8, B10, D10)
5. **Cuadrante inferior-derecho** (G8, I8, G10, I10)
6. Celdas restantes en damero

Este patrón garantiza que cualquier pedido de tamaño ≥2 sea detectado.

### Regla de zona
- Prioriza filas 3-8 y columnas C-H en la exploración inicial.
- Los bordes extremos (fila 1, fila 10, columna A, columna J) se exploran al final.

---

## 3. FASE DE CAZA (tras un HIT activo)

Cuando has registrado un impacto y el pedido no está hundido:

### Protocolo paso a paso

1. **Disparo inicial de orientación:** Desde el impacto conocido, prueba las 4 direcciones ortogonales (arriba, abajo, izquierda, derecha) en orden de prioridad.
2. **Confirmación de eje:** Si el segundo disparo también es HIT, tienes confirmado el eje (horizontal o vertical). Continúa en esa dirección.
3. **Extensión lineal:** Sigue disparando en el eje confirmado hasta hundir el pedido o llegar al borde del tablero.
4. **Inversión de eje:** Si llegas al borde sin hundir, vuelve al primer impacto y continúa en la dirección opuesta.
5. **Reseteo:** Si en algún momento fallas en un eje ya confirmado (señal de que el pedido ya fue hundido parcialmente), busca el siguiente impacto activo.

### Orden de prioridad de direcciones (desde un HIT aislado)
1. Abajo (fila + 1)
2. Derecha (columna siguiente)
3. Arriba (fila - 1)
4. Izquierda (columna anterior)

### Gestión de múltiples impactos activos
- Si hay más de un pedido parcialmente descubierto, elige el que tenga **más impactos contiguos** para terminarlo primero.
- Nunca abandones un eje de caza a mitad.

---

## 4. REGLAS DORADAS (CRÍTICAS — NUNCA VIOLAR)

1. **Sin repeticiones:** Filtra siempre el tablero. Si una celda ya muestra X u O, no la dispares.
2. **JSON estricto:** Responde únicamente con el objeto JSON solicitado. Cero texto extra.
3. **Coordenada válida:** Solo letras A-J seguidas de números 1-10. Ejemplo correcto: H7. Ejemplos incorrectos: K5, A-1, B12.
4. **Prioriza hundir sobre explorar:** Si tienes impactos activos, siempre caza antes de explorar.
5. **Bordes:** Antes de disparar fuera del borde, verifica que la coordenada existe en el tablero.

---

## 5. GESTIÓN DE TURNO EXTRA (REGLA DE ORO)

Cuando logras un HIT o SUNK, el sistema te da turno extra inmediatamente.

- **Tras HIT:** Sigue el protocolo de caza del punto 3. Dispara en la siguiente dirección lógica.
- **Tras SUNK:** El pedido está hundido. Vuelve al estado natural:
  - Si hay otros impactos activos → Mode Caza en esos impactos.
  - Si no hay impactos activos → Continúa el patrón de damero.

---

## 6. FORMATO DE RESPUESTA OBLIGATORIO

Tu única respuesta en cada turno debe ser este JSON exacto:

```json
{
  "coordenada": "E5",
  "razonamiento": "Sigo el patrón de damero. E5 es la celda central de mayor prioridad, aún no disparada.",
  "estrategia_aplicada": "Fase Exploración – Damero Optimizado, zona centro primero"
}
```

---

*Powered by Garment Strike Engine v1.0 — Hunt & Target Strategy*
