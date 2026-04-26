# 🌿 Mapa de Ramas (Git Branch Map)

Este documento describe la estructura y el propósito de las ramas actuales en el repositorio **BT-Supply-Impulse**.

## 📌 Ramas Principales

### 🟦 `main`
*   **Estado**: Estable / Producción.
*   **Contenido**: El núcleo del motor de simulación. Incluye el sistema de agentes LLM (Pydantic), el motor de combate naval logístico y el visualizador clásico basado en terminal (Rich).
*   **Diferencia Clave**: No incluye las capacidades de visualización web en tiempo real avanzada.

### 🚀 `feature/html-native-dashboard` (Rama Actual)
*   **Estado**: En desarrollo activo.
*   **Conceptual**: Migración completa del frontend de Streamlit a un **Dashboard Nativo HTML/JS**.
*   **Cambios frente a `main`**:
    *   Sustitución de Streamlit por un servidor **FastAPI** ultrarrápido.
    *   Visualización 3D mediante **SVG Dinámico** con estética Cyberpunk/Holográfica.
    *   Implementación de WebSockets con fallback automático a **HTTP Polling** para máxima compatibilidad.
    *   Motor optimizado para enviar eventos en tiempo real sin bloquear la ejecución de los agentes.

---

## 🛠️ Ramas de Desarrollo y Experimentación

### 🌉 `feature/tactical-js-bridge`
*   **Estado**: Precursora / Mantenimiento.
*   **Conceptual**: Creación del "Puente de Datos" entre Python y el mundo Web.
*   **Cambios frente a `main`**: Introdujo por primera vez los endpoints `/api/event` y `/ws/tactical`. Sirvió de base técnica para que el motor pudiera "hablar" con cualquier frontend JS, aunque el diseño visual era aún rudimentario.

### 🎨 `feat-dashboard-ux-01`
*   **Estado**: Experimental (Visual).
*   **Conceptual**: Rama dedicada exclusivamente a refinamientos estéticos y UX.
*   **Cambios frente a `main`**:
    *   Lógica de colores selectivos: las prendas reflejan el color del atacante.
    *   Identificación visual de cajas hundidas basada en quién realizó el impacto final.
    *   *Nota*: Muchos de estos conceptos se han integrado o refinado directamente en la rama nativa de HTML.

---

## 🌍 Ramas Remotas (`remotes/origin/`)
*   `origin/main`: Sincronizada con el repositorio central.
*   `origin/feature/tactical-js-bridge`: Versión respaldada del puente de datos.

> [!TIP]
> Para la mayoría de las tareas de desarrollo actuales, **`feature/html-native-dashboard`** es la rama de referencia, ya que contiene la tecnología de visualización más avanzada y estable.
