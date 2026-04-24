import streamlit as st

UI_CONFIG = {
    # --- 📐 TAMAÑO DE COORDENADAS (HEADER ROW & COL) ---
    "coord_let_height": "25px", # Alto fila letras (A..J).
    "coord_num_width": "25px",  # Ancho columna números (1..10).
    "cell_aspect_ratio": "1",   # 1 para cuadrado, >1 para rectangular
    "board_max_width": "min(100%, 55vh)", # Limita al 55% del alto de la pantalla para evitar tableros gigantes
    "cell_font_size": "0.75rem",

    # --- 📦 CAJAS CERRADAS (SEALED) ---
    # Define la caja sin descubrir
    "sealed_base_opacity": 0.1,    # Opacidad del panel base
    "sealed_border_width": 2,      # Ancho del borde exterior
    "sealed_tape_width": 20,        # Grosor de la cinta central
    "sealed_tape_opacity": 0.3,    # Opacidad de la cinta
    
    # --- 👕 PRENDAS ENCAJADAS (LOAD) ---
    # La prenda dentro de una caja exitosa
    "load_icon_scale": 2.5,
    "load_icon_stroke": 1.2,
    "load_icon_opacity": 0.7,
    
    # --- 🌊 PRENDAS PERDIDAS / AGUA (MISS) ---
    # La prenda que cae fuera (agua)
    "miss_container_scale": 1.5,   # Escala general del símbolo de agua
    "miss_icon_scale": 1.3,        # Escala de la prenda en sí misma
    "miss_icon_stroke": 1.8,       # Grosor de línea de la prenda perdida (Aumentado para VIS-01)
    "miss_icon_opacity": 0.6,      # Transparencia total (Aumentado de 0.2 para VIS-01)
    "miss_color": "#00d4ff",       # Color cyan vibrante (Cambiado de #9badc9 para VIS-01)
    
    # --- 🏗️ DIMENSIONES ESTRUCTURALES 3D ---
    "box_margin_x": 7,             # Margen exterior lateral
    "box_margin_y": 7,             # Margen exterior vertical
    "floor_inset_x": 10,           # Profundidad de Z-Axis horizontal
    "floor_inset_y": 10,           # Profundidad de Z-Axis vertical
    
    # --- 📐 SOLAPAS (FLAPS) ---
    "flap_height_y": 7,            # Cuánto sobresalen arriba/abajo
    "flap_width_x": 7,             # Cuánto sobresalen izquierda/derecha
    "flap_angle_offset_x": 4,      # Inclinación en los extremos horizontales
    "flap_angle_offset_y": 4,      # Inclinación en los extremos verticales
    "flap_fill_op": 0.4,           # Opacidad del interior del flap
    "flap_stroke_w": 2,            # Grosor de la línea del flap
    
    # --- 🔦 LUMINESCENCIA Y OPACIDADES DE ESTADO ---
    # Perímetro
    "perim_opacity_sealed": 1.0,
    "perim_opacity_open": 0.4,
    "perim_stroke": 2,
    
    # Fondo e hitos internos
    "floor_opacity_sealed": 0.8,
    "floor_opacity_open": 0.5,
    "floor_stroke": 1,
    "wall_fill_op": 0.1,           # Opacidad del relleno de las paredes internas
    
    # Diagonales de profundidad
    "depth_opacity_sealed": 0.8,
    "depth_opacity_open": 0.5,
    "depth_stroke": 1,
    
    # Divisores de celdas pegadas
    "div_opacity": 0.03,
    "div_stroke": 1,
}

def inject_styles():
    # Inyección de variables dinámicas al CSS nativo
    st.markdown(f"""
    <style>
        :root {{
            --coord-let-height: {UI_CONFIG['coord_let_height']};
            --coord-num-width: {UI_CONFIG['coord_num_width']};
            --cell-aspect-ratio: {UI_CONFIG['cell_aspect_ratio']};
            --board-max-width: {UI_CONFIG['board_max_width']};
            --cell-font-size: {UI_CONFIG['cell_font_size']};
        }}
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;700&family=Orbitron:wght@400;600;900&display=swap');

    :root {
        --bg-deep: #050a0e;
        --panel-bg: rgba(13, 17, 23, 0.9);
        --accent-alpha: #00ff88; /* Verde para Equipo A */
        --accent-beta: #ff4b4b;  /* Rojo para Equipo B */
        --text-main: #e6edf3;
        --grid-line: #1f2428;
    }

    /* Ocultar elementos nativos de Streamlit y forzar margen cero */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .block-container {
        padding-top: 0rem !important; 
        padding-bottom: 0rem !important;
        padding-left: 2.5rem !important;
        padding-right: 2.5rem !important;
        max-width: 100% !important;
    }
    
    /* Eliminar espacios que mete Streamlit entre markdowns */
    div[data-testid="stVerticalBlock"] > div:first-child {
        margin-top: -50px !important;
    }
    
    div.stMarkdown {
        margin-top: 0px !important;
        margin-bottom: 0px !important;
        padding-top: 0px !important;
    }

    .stApp {
        background: radial-gradient(circle at center, #0d1b2a 0%, #050a0e 100%);
        font-family: 'JetBrains+Mono', monospace;
        color: var(--text-main);
    }

    .tactical-header {
        font-family: 'Orbitron', sans-serif;
        text-transform: uppercase;
        letter-spacing: 2px;
        margin-bottom: 12px;
        font-weight: 700;
        border-bottom: 1px solid rgba(255,255,255,0.1);
        padding-bottom: 6px;
        font-size: 0.95rem;
        display: flex;
        justify-content: space-between;
        align-items: baseline;
    }
    
    .alpha-text { color: var(--accent-alpha); text-shadow: 0 0 10px rgba(0, 255, 136, 0.3); }
    .beta-text { color: var(--accent-beta); text-shadow: 0 0 10px rgba(255, 75, 75, 0.3); }

    .glass-panel {
        background: var(--panel-bg);
        border: 1px solid rgba(255,255,255,0.05);
        border-radius: 12px;
        padding: 10px; /* Reducido de 15px */
        backdrop-filter: blur(10px);
    }

    .tactical-grid {
        display: grid;
        grid-template-columns: var(--coord-num-width) repeat(10, 1fr);
        grid-template-rows: var(--coord-let-height) repeat(10, 1fr);
        gap: 0px; 
        background-color: rgba(0,0,0,0.5);
        padding: 2px;
        border-radius: 4px;
        position: relative;
        z-index: 1;
        width: 100%; /* Ocupa todo el ancho de la columna */
        margin: 0 auto;
    }

    /* Bordes y glow de tableros por equipo */
    .board-alpha { 
        border: 1px solid var(--accent-alpha); 
        box-shadow: 0 0 15px rgba(0, 255, 136, 0.2), inset 0 0 10px rgba(0, 255, 136, 0.1); 
    }
    .board-beta { 
        border: 1px solid var(--accent-beta); 
        box-shadow: 0 0 15px rgba(255, 75, 75, 0.2), inset 0 0 10px rgba(255, 75, 75, 0.1); 
    }
    
    /* Highlight Táctico (FOCUS-01) */
    @keyframes targetPulseAlpha {
        0%, 100% { box-shadow: 0 0 15px rgba(0, 255, 136, 0.2), inset 0 0 10px rgba(0, 255, 136, 0.1); border-color: var(--accent-alpha); }
        50% { box-shadow: 0 0 40px rgba(0, 255, 136, 0.8), inset 0 0 30px rgba(0, 255, 136, 0.4); border-color: #ffffff; }
    }
    @keyframes targetPulseBeta {
        0%, 100% { box-shadow: 0 0 15px rgba(255, 75, 75, 0.2), inset 0 0 10px rgba(255, 75, 75, 0.1); border-color: var(--accent-beta); }
        50% { box-shadow: 0 0 40px rgba(255, 75, 75, 0.8), inset 0 0 30px rgba(255, 75, 75, 0.4); border-color: #ffffff; }
    }
    .board-alpha.target-highlight { animation: targetPulseAlpha 1.5s infinite ease-in-out; }
    .board-beta.target-highlight { animation: targetPulseBeta 1.5s infinite ease-in-out; }

    /* Animación de Impacto/Nuevo Movimiento (ANIM-01) */
    @keyframes newActionImpact {
        0% { transform: scale(1.4); filter: brightness(2) drop-shadow(0 0 20px #ffffff); z-index: 10; }
        50% { transform: scale(0.9); filter: brightness(1.5) drop-shadow(0 0 10px rgba(255,255,255,0.5)); z-index: 10; }
        100% { transform: scale(1); filter: brightness(1) drop-shadow(0 0 0 transparent); z-index: 1; }
    }
    .new-action-anim {
        animation: newActionImpact 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    }

    .cell {
        aspect-ratio: 1;
        border: 0.5px solid rgba(255,255,255,0.05); /* Reducido para no interferir */
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.75rem;
        transition: all 0.2s;
    }

    /* Estilo de las etiquetas de coordenadas sincronizado con el equipo */
    .label { 
        font-family: 'Orbitron', sans-serif;
        font-size: 0.85rem; /* Aumentado de 0.7rem */
        font-weight: 700;
        opacity: 0.8; /* Aumentada opacidad para legibilidad */
        aspect-ratio: auto !important; /* Permite tamaños no cuadrados guiados por grid-template */
    }
    .label-alpha { color: var(--accent-alpha); }
    .label-beta { color: var(--accent-beta); }

    /* Estilos del Logistics Map */
    .ship { color: #00ff88; font-weight: bold; background: rgba(0, 255, 136, 0.05); } /* # */
    .hit { color: #ff8c00; font-weight: bold; background: rgba(255, 140, 0, 0.1); }  /* X */
    .miss { color: #00d4ff; opacity: 0.6; }                                           /* O */
    .unknown { color: #333; }                                                        /* ~ */

    /* Telemetría */
    .telemetry-box {
        border-left: 3px solid #00d4ff;
        background: rgba(0, 212, 255, 0.05);
        padding: 10px;
        margin-top: 10px;
        font-size: 0.85rem;
    }

    /* LED Titilante */
    @keyframes blinker { 50% { opacity: 0; } }
    .led-red {
        width: 10px;
        height: 10px;
        background-color: #ff4b4b;
        border-radius: 50%;
        display: inline-block;
        box-shadow: 0 0 10px #ff4b4b;
        animation: blinker 1.5s linear infinite;
        margin-right: 8px;
        vertical-align: middle;
    }

    /* POC: CARGO STYLES (Approach 1: CSS) */
    .box-css {
        background: linear-gradient(145deg, #3d2b1f 0%, #2a1d15 100%);
        border: 1px solid #5d4037 !important;
        position: relative;
        box-shadow: inset 0 0 5px rgba(0,0,0,0.5);
    }
    .box-css::before {
        content: '';
        position: absolute;
        top: 2px; left: 2px; right: 2px; bottom: 2px;
        border: 1px dashed rgba(255,255,255,0.1);
    }
    .hit-css {
        background: #5d4037;
        display: flex;
        align-items: center; justify-content: center;
    }
    .hit-css::after {
        content: '👕';
        font-size: 0.9rem;
        filter: drop-shadow(0 0 2px var(--accent-alpha));
    }
    .full-css {
        background: #1a1a1a;
        border: 1px solid #333 !important;
    }
    .full-css::after {
        content: '🏷️';
        position: absolute;
        top: 1px; right: 1px;
        font-size: 0.5rem;
    }

    /* POC: CARGO STYLES (Approach 2: SVG/Icon) */
    .box-svg {
        background: rgba(255,255,255,0.03);
    }
    .svg-icon {
        width: 80%;
        height: 80%;
    }

    /* POC: HOLOGRAPHIC STYLE (Inspired by Tablero3D.png) */
    .holo-cell {
        background: rgba(0, 243, 255, 0.01);
        border: 0.5px solid rgba(255, 255, 255, 0.05) !important; /* Rejilla de fondo muy fina */
        position: relative;
        overflow: visible;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    
    /* Solapas para caja abierta */
    .box-flaps::before, .box-flaps::after {
        content: '';
        position: absolute;
        top: -8px;
        width: 15px;
        height: 10px;
        border: 1px solid #00f3ff;
        background: rgba(0, 243, 255, 0.1);
    }
    .box-flaps::before { left: 5px; transform: skewY(-20deg); }
    .box-flaps::after { right: 5px; transform: skewY(20deg); }

    /* Líneas de celo para caja cerrada */
    .box-sealed::before {
        content: '';
        position: absolute;
        width: 100%;
        height: 2px;
        background: rgba(0, 243, 255, 0.4);
        transform: rotate(45deg);
    }
    .box-sealed::after {
        content: '';
        position: absolute;
        width: 100%;
        height: 2px;
        background: rgba(0, 243, 255, 0.4);
        transform: rotate(-45deg);
    }

    .holo-glow-cyan {
        border-color: #00f3ff !important;
        box-shadow: 0 0 10px rgba(0, 243, 255, 0.5), inset 0 0 5px rgba(0, 243, 255, 0.2);
    }
    .holo-glow-green {
        border-color: #00ff88 !important;
        box-shadow: 0 0 15px rgba(0, 255, 136, 0.6), inset 0 0 10px rgba(0, 255, 136, 0.2);
        color: #00ff88 !important;
    }
    
    /* Animación de parpadeo neón DINÁMICO (Usa el color del equipo) */
    @keyframes neonPulse {
        0%, 100% { filter: drop-shadow(0 0 2px var(--team-neon)) brightness(1); }
        50% { filter: drop-shadow(0 0 10px var(--team-neon)) brightness(1.3); }
    }
    .master-holo-box {
        animation: neonPulse 2s infinite ease-in-out;
        width: 100%;
        height: 100%;
    }

    /* SVG UI Helpers */
    @keyframes glitch {
        0% { transform: translate(0); }
        20% { transform: translate(-1px, 1px); }
        40% { transform: translate(-1px, -1px); }
        60% { transform: translate(1px, 1px); }
        80% { transform: translate(1px, -1px); }
        100% { transform: translate(0); }
    }
    .glitch-overlay { animation: glitch 0.3s infinite; opacity: 0.3; }

    
    .holo-container-segment {
        border-top: 2px solid #00f3ff !important;
        border-bottom: 2px solid #00f3ff !important;
    }
    .holo-container-start {
        border-left: 2px solid #00f3ff !important;
        border-top-left-radius: 4px;
        border-bottom-left-radius: 4px;
    }
    .holo-container-end {
        border-right: 2px solid #00f3ff !important;
        border-top-right-radius: 4px;
        border-bottom-right-radius: 4px;
    }
    
    /* Efecto de escaneo/trama digital */
    .holo-wireframe {
        background-image: 
            linear-gradient(rgba(0, 243, 255, 0.1) 1px, transparent 1px),
            linear-gradient(90deg, rgba(0, 243, 255, 0.1) 1px, transparent 1px);
        background-size: 4px 4px;
    }

    /* Títulos de Logs */
    .log-title {
        font-family: 'Orbitron', sans-serif;
        font-size: 1rem;
        letter-spacing: 2px;
        color: #e6edf3;
        margin-bottom: 10px;
        margin-top: 10px; /* Reducido de 42px para hacer espacio al scoreboard */
        border-bottom: 1px solid #1f2428;
        text-shadow: 0 0 8px rgba(255, 255, 255, 0.15); /* Neón tenue */
    }
    /* Contenedor de Logs (Sin Scroll, limitado por cantidad) */
    .log-scroll-area {
        overflow: hidden;
        padding-right: 0px;
        font-family: 'JetBrains Mono', monospace;
    }

    /* Scoreboard Central (UX-01) */
    .central-scoreboard {
        background: linear-gradient(180deg, rgba(13, 17, 23, 0.8) 0%, rgba(5, 10, 14, 0.9) 100%);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 12px;
        padding: 25px 15px 15px 15px;
        text-align: center;
        margin-bottom: 15px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.5), inset 0 0 15px rgba(255,255,255,0.02);
        position: relative;
    }
    
    .score-number {
        font-family: 'Orbitron', sans-serif;
        font-weight: 900;
        font-size: 3rem;
        line-height: 1;
        letter-spacing: -2px;
    }
    
    .score-divider {
        font-family: 'Orbitron', sans-serif;
        font-size: 1.2rem;
        color: rgba(255,255,255,0.2);
        font-weight: 900;
        padding: 0 15px;
    }

    .turn-badge {
        position: absolute;
        top: -12px;
        left: 50%;
        transform: translateX(-50%);
        background: #00d4ff;
        color: #000;
        font-family: 'Orbitron', sans-serif;
        font-weight: 900;
        font-size: 0.85rem;
        padding: 3px 15px;
        border-radius: 20px;
        box-shadow: 0 0 15px rgba(0, 212, 255, 0.4);
        letter-spacing: 3px;
    }
</style>
    """, unsafe_allow_html=True)
