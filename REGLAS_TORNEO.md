# 🏆 MANUAL DEL COMANDANTE: TORNEO GARMENT STRIKE

¡Bienvenidos al torneo de logística táctica! Aquí se enfrentarán no solo agentes de IA, sino las mentes estratégicas que los configuran. Como comandante, tu éxito depende de tu capacidad para "entrenar" a tu agente a través de sus archivos de configuración.

## 📋 Reglas Fundamentales

### 1. El Arsenal del Agente
Cada equipo debe gestionar y entregar dos archivos clave:
- **`persona.md` (La Estrategia):** Define el razonamiento, la personalidad y el patrón táctico de tu agente. Es su "instinto" de combate.
- **`board.md` (El Almacén):** Define la disposición de tus 5 pedidos (tamaños 5, 4, 3, 3 y 2) en la cuadrícula 10x10.

### 2. Restricciones Técnicas
- **Límite de Tamaño:** Máximo **5 KB** por archivo. (Los agentes procesan mejor la información concisa).
- **Formato Estricto:** Se deben usar las plantillas de `/templates`. Alterar la estructura puede causar que el agente "se confunda" o el sistema rechace el archivo.

### 3. Dinámica de Tiempos (Cronómetro Central)
El torneo sigue un ritmo estricto controlado por el cronómetro del dashboard:
- **Fase de Setup Inicial:** **10 Minutos**. Tiempo generoso para rellenar las plantillas, esconder tus pedidos y definir tu "Gran Estrategia".
- **Fase de Ajuste Táctico:** **3 Minutos**. Entre rondas, el tiempo es escaso. Solo tendrás 180 segundos para reaccionar a lo que viste en la batalla anterior.

## 🕵️ El Rol del Jugador: Observación y Re-Calibración
No eres un espectador, eres un **Analista Táctico**. Durante el combate, DEBES observar el dashboard para responder:
1. **¿Mi agente es predecible?** Si el rival te hunde barcos rápido, tu `board.md` es demasiado obvio.
2. **¿Mi agente desperdicia tiros?** Si dispara a zonas donde ya falló o no sigue un patrón lógico, tu `persona.md` necesita reglas más claras.
3. **¿Cómo juega el rival?** Puedes adaptar tu estrategia para la siguiente ronda basándote en los patrones de los otros equipos.

---

## 💡 Matices y Estrategias Avanzadas (Pro-Tips)

### A. La Paradoja del Engaño
En el `persona.md`, puedes describir una táctica que no vas a usar para confundir a los equipos que intenten espiar tu código (si las reglas lo permiten), pero asegúrate de que las **Reglas con ID** sean las que realmente quieres que ejecute la IA.

### B. Gestión de "Branching"
Te recomendamos tener preparadas varias versiones de tus archivos:
- `persona_agresivo.md`: Para rivales novatos.
- `persona_analitico.md`: Para rivales con mapas complejos.
- `board_disperso.md` vs `board_agrupado.md`.

### C. Eficiencia de Instrucciones
La IA tiene una "ventana de atención". En lugar de escribir un párrafo largo, usa listas de puntos:
- `[ID: BUSQUEDA]` Priorizar esquinas.
- `[ID: CAZA]` Tras acierto, buscar en cruz.
Esto es mucho más efectivo que una descripción narrativa larga.

> [!IMPORTANT]
> **Recuerda:** Gana el equipo que mejor se adapte. Si tu agente pierde la primera ronda, tienes 3 minutos para cambiar radicalmente su forma de pensar. **¡Haz que cuenten!**
