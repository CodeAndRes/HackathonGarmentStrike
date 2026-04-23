# ⚡ MISSION: Tactical Dashboard Agent

> **Status**: ACTIVE
> **Role**: Senior Tactical UI Specialist
> **Current Focus**: Transforming Garment Strike Interface from Mocks to Core-Integrated Reality.

---

## 🧠 Agent Identity & Vision
Este agente actúa como el guardián de la coherencia visual y funcional del dashboard de **Garment Strike**. Su objetivo es asegurar que la interfaz de Streamlit no solo sea estética, sino que sea una extensión visual precisa de la lógica de simulación del motor core.

---

## 🎨 Design DNA (Evolution: 19th April)

### Holographic Container System
- **Ship Identity (Anti-Fusion)**: Use of unique `ShipIDs` to ensure adjacent containers render as independent units. No more accidental merging of geometries.
- **Structural Integrity**: Unified opacities across all ship segments. Box perimeters and flaps remain dim (0.4 op) until the order is 100% completed (`is_sealed`).
- **3D Depth**: Implementation of internal wall fills (`wall_fill_op`) and central floor guide lines for a reinforced sense of volume.
- **Premium Iconography**: Global use of the **Detailed Garment Icon** for both LOAD and MISS states, ensuring high-fidelity visual consistency.
- **Centralized Control**: 100% of spatial and visual parameters (margins, angles, strokes, opacities) managed via a single `UI_CONFIG` dictionary.

### Typography & Layout
- **Headlines**: `Orbitron` (font-weight: 700/900).
- **Technicals/Rationale**: `JetBrains Mono` (font-weight: 400).
- **Architecture**: Zero-Scroll High Density layout. Boards side-by-side, telemetry stacked beneath. Ultra-compact footers.

---

## ⚙️ Logic Synchronization

Cualquier cambio en el frontend debe respetar el mapeo de símbolos del **Logistics Map** del Core Engine:

| Símbolo | Significado | Estilo CSS |
| :--- | :--- | :--- |
| `#` | Pedido/Nave (Ship) | `.ship` (Neon Green) |
| `X` | Impacto (Hit) | `.hit` (Alert Orange) |
| `O` | Fallo (Miss) | `.miss` (Sky Blue) |
| `~` | Desconocido (Unknown) | `.unknown` (Low Opacity) |

---

## 🚧 Roadmap: The Transformation

### Phase A: Architecture & Advanced Visuals (Completed ✅)
- [x] Establishment of Basic High-Fidelity UI in `Interface.py`.
- [x] Implementation of Responsive Tactical Grids (Visually tuned).
- [x] Achieve "Zero-Scroll" high density layout.
- [x] **Advanced Visuals**: Unified ships, smart tape, closed flaps, and internal volume effects.
- [x] **Config-First Architecture**: Unified settings in `UI_CONFIG`.

### Phase B: Core Integration & Visibility (CURRENT 📍)
- [ ] **[MISIÓN UX-01]**: Centrar y ampliar el panel de resultados actual. Debe ser el foco central y verse mucho más grande.
- [ ] **[MISIÓN VIS-01]**: Aumentar el contraste de las "prendas perdidas" (Misses). Usar un color más vibrante y visible.
- [ ] **[MISIÓN PANEL-01]**: Crear un panel de "Acción en Tiempo Real" que muestre: Jugador Actual, Coordenada del disparo y Resultado inmediato.
- [ ] **[MISIÓN FOCUS-01]**: Implementar el "Highlight Táctico": El tablero que recibe el disparo en el turno actual debe iluminarse o resaltarse para guiar la vista del público.
- [ ] **[MISIÓN ANIM-01]**: Tantear e integrar animaciones/transiciones para impactos y cambios de turno.

### Phase C: Polish & SFX
- [ ] Subtle animations for HIT/MISS events.
- [ ] Dynamic strategy descriptions based on AI reasoning tokens.

---

## 📝 Persistence & Workflow Note
- **Ramas Individuales**: Cada misión (`UX-01`, `VIS-01`, etc.) debe desarrollarse en su propia rama de Git (ej: `feat-dashboard-ux-01`).
- **Commits Granulares**: Realizar commits frecuentes para cada cambio significativo.
- **Consultar al inicio**: Este archivo debe ser consultado al inicio de cada sesión para mantener la continuidad del "hilo" de desarrollo del 19 de abril de 2026. Al resumir, priorizar la configuración maquetada en UI_CONFIG.
