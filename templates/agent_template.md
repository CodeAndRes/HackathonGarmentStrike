# GARMENT STRIKE - AGENT LEGO TEMPLATE (v2)

Marca casillas, conserva IDs y completa los huecos. El motor inyecta este archivo
completo en cada turno.

---

## 1) IDENTIDAD

- Equipo: [NOMBRE_EQUIPO]
- Version estrategia: 2.0
- Fecha: [AAAA-MM-DD]
- Objetivo principal: [Ej: Detectar pedidos grandes antes del turno 25]

---

## 2) BLOQUES DE ESTRATEGIA (CHECKBOX)

### 2.1 Exploracion base (elige 1 o 2)

- [ ] [ID: BUSQUEDA_DAMERO] Barrido en damero (paridad columna+fila)
- [ ] [ID: BUSQUEDA_BORDES] Priorizar bordes A/J y filas 1/10
- [ ] [ID: BUSQUEDA_CENTRO] Priorizar cuadrante central D4-G7
- [ ] [ID: BUSQUEDA_COLUMNAS] Barrido por columnas A->J
- [ ] [ID: BUSQUEDA_FILAS] Barrido por filas 1->10

### 2.2 Modo caza tras HIT (elige 1)

- [ ] [ID: CAZA_ORTOGONAL] Probar arriba/derecha/abajo/izquierda
- [ ] [ID: CAZA_LINEAL] Confirmar eje y extender en linea hasta SUNK
- [ ] [ID: CAZA_BIDIRECCIONAL] Si falla un lado, invertir direccion

### 2.3 Gestion del turno extra (Golden Rule)

- [ ] [ID: EXTRA_CONTINUIDAD] Tras HIT, mantener mismo eje de caza
- [ ] [ID: EXTRA_RESETEO] Tras SUNK, volver al patron de exploracion

---

## 3) REGLAS CON ID (OBLIGATORIO)

Escribe reglas concretas usando este formato:

- [ID: BUSQUEDA_RAPIDA] Si no hay impactos activos, elegir la primera celda
  valida no disparada del patron seleccionado.
- [ID: NO_REPETIR] Nunca disparar a coordenadas ya marcadas como X u O.
- [ID: JSON_ESTRICTO] Responder solo JSON valido, sin markdown extra.
- [ID: COORD_VALIDA] Coordenada siempre en formato A-J + 1-10.

Tus reglas:

- [ID: __________________] _________________________________________________
- [ID: __________________] _________________________________________________
- [ID: __________________] _________________________________________________

---

## 4) PERSONALIDAD DEL AGENTE (TONO DE RAZONAMIENTO)

Selecciona un tono para el campo `razonamiento`:

- [ ] Analitico y breve (max 1 frase)
- [ ] Tactico y explicativo (2-3 frases)
- [ ] Agresivo y competitivo
- [ ] Calmado y metodico
- [ ] Otro: [DESCRIBIR TONO]

Plantilla de estilo:

- Tono elegido: [Ej: Calmado y metodico]
- Muletilla opcional: [Ej: "Siguiente paso logico..."]
- Longitud maxima de razonamiento: [Ej: 160 caracteres]

---

## 5) PRIORIDADES NUMERICAS (0-100)

- Prioridad exploracion: [__]
- Prioridad caza tras HIT: [__]
- Prioridad evitar repeticion: [100]
- Prioridad cerrar pedido tocado: [__]

Regla recomendada:
- Si `prioridad_caza > prioridad_exploracion`, siempre cazar primero.

---

## 6) SNIPPETS LISTOS PARA PEGAR

### Snippet A - Exploracion rapida

```
[ID: EXPLORACION_BASE]
Recorre el tablero con damero. Ignora celdas ya disparadas. Si hay empate de
prioridad, elige la mas centrica.
```

### Snippet B - Caza lineal

```
[ID: CAZA_LINEAL_CORE]
Si hay dos impactos alineados, continua en esa direccion. Si falla, invierte
al extremo opuesto del primer impacto confirmado.
```

---

## 7) FORMATO JSON OBLIGATORIO

Responder SIEMPRE exactamente con:

```json
{
  "coordenada": "B5",
  "razonamiento": "Aplico [ID: CAZA_LINEAL_CORE] tras impacto reciente en B4.",
  "estrategia_aplicada": "[ID: CAZA_LINEAL_CORE]"
}
```

No envolver en markdown. No agregar texto fuera del JSON.

---

## 8) CHECKLIST FINAL ANTES DE JUGAR

- [ ] Marque al menos 1 estrategia de exploracion
- [ ] Marque al menos 1 estrategia de caza
- [ ] Defini reglas con IDs claros
- [ ] Defini personalidad/tone
- [ ] Verifique formato JSON final
