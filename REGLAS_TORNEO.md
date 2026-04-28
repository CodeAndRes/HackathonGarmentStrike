# 🏆 MANUAL DEL COMANDANTE: TORNEO GARMENT STRIKE

¡Bienvenidos al torneo de logística táctica! Aquí se enfrentarán no solo agentes de IA, sino las mentes estratégicas que los configuran. En este torneo **no hay plantillas**. Deberéis investigar y descubrir la manera más inteligente de usar vuestras palabras para crear la estrategia perfecta.

---

## 🗺️ 1. MECÁNICAS DEL JUEGO

El juego es una batalla naval táctica (hundir la flota) adaptada a un entorno logístico. Dos agentes de IA se enfrentan enviando coordenadas a ciegas hasta destruir la logística del rival.

### Progresión del Torneo (El Desafío Crece)
El tamaño del almacén y la cantidad de pedidos aumentan con cada fase:
- **Primera Ronda:** Tablero **6x6** (A-F, 1-6). Tienes **3 pedidos** de tamaños: **4, 3, 2**. Límite: 50 turnos.
- **Segunda Ronda:** Tablero **8x8** (A-H, 1-8). Tienes **4 pedidos** de tamaños: **4, 3, 3, 2**. Límite: 60 turnos.
- **Gran Final:** Tablero **10x10** (A-J, 1-10). Tienes **5 pedidos** de tamaños: **5, 4, 3, 3, 2**. Sin límite de turnos.

### Reglas de Colocación (El Almacén)
- Solo pueden colocarse en línea recta (**horizontal o vertical**). No en diagonal.
- **No pueden superponerse** (dos cajas no pueden ocupar la misma coordenada).
- Pueden estar pegadas unas a otras, pero es estratégicamente peligroso.

---

## ⚔️ 2. EL ARSENAL (Tus Archivos)

Cada equipo debe entregar dos archivos de texto plano (`.md`). 
**Límite estricto:** Máximo **300 palabras** por archivo. La IA tiene una ventana de atención limitada; sé conciso y directo.

### Archivo 1: El Almacén (`almacen.md`)
Aquí defines dónde escondes tus pedidos para la ronda actual. El formato es estricto (ejemplo para la 1ª Ronda):
```text
P1: A1 B1 C1 D1
P2: A3 B3 C3
P3: F4 F5
```

### Archivo 2: La Estrategia (`agent.md`)
Este es el "cerebro" de tu IA. Escribe en lenguaje natural las instrucciones que debe seguir tu agente.
- **Búsqueda:** ¿Cómo debe explorar el tablero al principio? (¿Al azar? ¿En patrón de ajedrez? ¿Por los bordes?)
- **Caza:** Cuando acierta un tiro, ¿cómo debe reaccionar para hundir el resto de la caja sin desperdiciar turnos?
- *Nota técnica:* El motor ya se encarga de pedirle a la IA que responda en el formato técnico necesario. Tu trabajo en este archivo es puramente **explicarle cómo debe pensar y decidir**.

---

## 🏆 3. CONDICIONES DE VICTORIA Y DESEMPATE

El objetivo es hundir las 4 cajas del rival usando el **menor número de turnos posible**.

1. **Victoria Directa:** El primer agente en hundir todas las cajas del enemigo gana la partida.
2. **Límite de Turnos:** Si se alcanza el límite de turnos de la ronda sin un ganador claro, la batalla se detiene y actúan los jueces mecánicos.
3. **Reglas de Desempate (Tie-breakers Oficiales):** Si se llega al límite de turnos, el sistema de puntuación evalúa en este orden exacto:
   - **1º Criterio (Pedidos Hundidos):** El equipo que haya conseguido hundir más pedidos COMPLETOS del rival.
   - **2º Criterio (Impactos Totales):** Si hay empate, gana quien haya acertado más veces (partes de barcos dañadas).
   - **3º Criterio (Defensa):** Si persiste el empate, gana quien haya RECIBIDO MENOS impactos en su propio tablero.

---

## ⏱️ 4. DINÁMICA DEL TORNEO

1. **Setup Inicial:** Tendréis un tiempo para escribir vuestro `agent.md` y esconder vuestras cajas en el `almacen.md`.
2. **Observación Táctica:** Durante la batalla, observaréis el Dashboard en tiempo real. Prestad mucha atención: ¿vuestro agente dispara a zonas ilógicas? ¿Se queda atascado tras acertar un tiro?
3. **Ajustes entre Rondas:** Si pasáis de ronda, tendréis un tiempo muy limitado para editar vuestra estrategia y corregir los fallos que hayáis observado. ¡El que mejor se adapta, gana!
