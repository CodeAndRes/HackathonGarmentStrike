import streamlit as st
import time

# ──────────────────────────────────────────────────────────────────────────────
# 1. Configuración de la página (Título y Layout)
# ──────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Garment Strike | Supply Chain Simulation",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

from src.styles.design_system import inject_styles, UI_CONFIG
from src.renderers.holographics import get_holo_box_svg, get_holo_miss_svg
from src.data.bridge import get_game_state
from TacticalBridge import tactical_telemetry_bridge
from streamlit_autorefresh import st_autorefresh

# Polling transparente cada 2 segundos
st_autorefresh(interval=2000, limit=None, key="data_polling")

inject_styles()
state = get_game_state()

# 4. Renderizadores
# ──────────────────────────────────────────────────────────────────────────────
def render_tactical_board(title, color_class, team_data, secondary_stat=""):
    stat_html = f"<small style='color:#666; font-family: \"JetBrains Mono\", monospace; font-weight: 400; text-transform:none; letter-spacing:0;'>{secondary_stat}</small>" if secondary_stat else ""
    st.markdown(f'<div class="tactical-header {color_class}"><span>{title}</span>{stat_html}</div>', unsafe_allow_html=True)
    
    rows = team_data.get('board', [])
    max_rows = len(rows) if rows else 10
    max_cols = len(rows[0]) if rows and rows[0] else 10

    cols = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")[:max_cols]
    
    # Determinar clase de etiqueta según el equipo
    label_team_class = "label-alpha" if "alpha" in color_class.lower() else "label-beta"
    board_glow_class = "board-alpha" if "alpha" in color_class.lower() else "board-beta"
    
    grid_html = f'<div class="tactical-grid {board_glow_class}" style="grid-template-columns: var(--coord-num-width) repeat({max_cols}, 1fr); grid-template-rows: var(--coord-let-height) repeat({max_rows}, 1fr);">'
    
    # Headers
    grid_html += f'<div class="cell label {label_team_class}"></div>'
    for c in cols: grid_html += f'<div class="cell label {label_team_class}">{c}</div>'
    
    # Grid dinámico
    for row in range(max_rows):
        grid_html += f'<div class="cell label {label_team_class}">{row+1}</div>'
        for col in range(max_cols):
            try:
                sym = rows[row][col]
            except (IndexError, KeyError):
                sym = "~"
            
            # Obtener ID de barco para lógica de conexión inteligente
            fleet = team_data.get('fleet', {})
            ship_id = fleet.get((row, col), "NONE")
            
            cell_class = "cell holo-cell"
            content = ""
            team_color = "#00ff88" if "alpha" in color_class.lower() else "#ff4b4b"
            
            # Conexiones inteligentes (Soportando nuevos iconos logísticos)
            ship_syms = ["#", "X", "👕", "📦"]
            is_ship = sym in ship_syms
            
            # Inyectar color de neón dinámico para el equipo
            cell_style = f"--team-neon: {team_color};"
            if is_ship: cell_style += " border: none !important;"
            
            conn = {"top": False, "bottom": False, "left": False, "right": False}
            sealed = False
            
            if is_ship and ship_id != "NONE":
                # Arriba
                if row > 0 and rows[row-1][col] in ship_syms and fleet.get((row-1, col)) == ship_id: conn["top"] = True
                # Abajo
                if row < max_rows - 1 and rows[row+1][col] in ship_syms and fleet.get((row+1, col)) == ship_id: conn["bottom"] = True
                # Izquierda
                if col > 0 and rows[row][col-1] in ship_syms and fleet.get((row, col-1)) == ship_id: conn["left"] = True
                # Derecha
                if col < max_cols - 1 and rows[row][col+1] in ship_syms and fleet.get((row, col+1)) == ship_id: conn["right"] = True
                
                # Estado cerrado (sealed) si todos los segmentos del MISMO barco han sido impactados
                if sym in ["X", "👕", "📦"]:
                    sealed = True
                    # Verificación: ¿Hay alguna parte de este barco que NO sea un impacto/entrega?
                    for (r, c), sid in fleet.items():
                        if sid == ship_id and rows[r][c] not in ["X", "👕", "📦"]:
                            sealed = False
                            break

            if sym == "#": 
                content = get_holo_box_svg("IDLE", team_color, conn)
            elif sym in ["X", "👕", "📦"]: 
                content = get_holo_box_svg("LOAD", team_color, conn, sealed)
            elif sym in ["O", "❔"]: 
                content = get_holo_miss_svg()
            
            grid_html += f'<div class="{cell_class}" style="{cell_style}">{content}</div>'
    
    grid_html += '</div>'
    st.markdown(grid_html, unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# 5. Dashboard UI (Cabecera Optimizada)
# ──────────────────────────────────────────────────────────────────────────────
header_html = f"""
<div style="display: flex; justify-content: space-between; align-items: center; width: 100%; border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 15px; margin-bottom: 60px; gap: 15px;">
    <h3 style="font-family: Orbitron; font-weight: 900; letter-spacing: 5px; color: white; margin: 0; padding: 0; flex-shrink: 0;">⚡ GARMENT STRIKE</h3>
    <div style="display: flex; align-items: center; gap: 15px; background: rgba(255,255,255,0.02); padding: 3px 12px; border-radius: 4px; border: 1px solid rgba(255,255,255,0.05); font-family: 'JetBrains Mono', monospace; font-size: 0.7rem; color: #e6edf3; flex-shrink: 0;">
        <div style="display: flex; align-items: center; border-right: 1px solid #333; padding-right: 12px; gap: 6px;">
            <span class="led-red"></span><span style="color:#ff4b4b; font-family:Orbitron; font-weight:bold; font-size:0.65rem;">LIVE</span>
        </div>
        <div style="border-right: 1px solid #333; padding-right: 12px;">
            TURNO: <b style="color:#00d4ff;">#{state['turn']}</b>
        </div>
        <div style="border-right: 1px solid #333; padding-right: 12px;">
            <span class="alpha-text">{state['team_a']['name']}</span>: <b>{state['team_a']['pedidos_encajados']}/{state['team_a']['total_pedidos']}</b>
        </div>
        <div>
            <span class="beta-text">{state['team_b']['name']}</span>: <b>{state['team_b']['pedidos_encajados']}/{state['team_b']['total_pedidos']}</b>
        </div>
    </div>
</div>""".strip()

st.markdown(header_html, unsafe_allow_html=True)

# Layout Principal (Boards)
# 32% Tablero A - 36% Logs - 32% Tablero B
col_a, col_mid, col_b = st.columns([32, 36, 32])

with col_a:
    render_tactical_board(f"{state['team_a']['name']} (PROPIO)", "alpha-text", state['team_a'], f"Prendas encajadas: {state['team_a'].get('prendas_encajadas', 0)}")

with col_mid:
    st.markdown('<div class="log-title"><i class="fa-solid fa-terminal" style="margin-right:10px;"></i>MOVIMIENTOS</div>', unsafe_allow_html=True)
    
    logs_html = '<div class="log-scroll-area">'
    # Mostramos los últimos 15 movimientos
    for move in state['comms'][-15:]:
        color_agent = "var(--accent-alpha)" if "ALPHA" in move['agent'] or "A" == move['agent'] else "var(--accent-beta)"
        log_entry = (
            f'<div style="border-left: 2px solid {color_agent}; margin-bottom: 2px; background: rgba(255,255,255,0.02); '
            f'padding: 2px 8px; border-radius: 2px; display: flex; align-items: center; gap: 6px; overflow: hidden; line-height: 1;">'
            f'<span style="color:#666; font-size:0.7rem; flex-shrink: 0; font-family: \'JetBrains Mono\', monospace;">[T{move["turn"]}]</span>'
            f'<span style="color:#ccc; font-size:0.75rem; flex-shrink: 0; font-family: \'JetBrains Mono\', monospace; font-weight: 700; letter-spacing: 0px;">{move["coord"]}</span>'
            f'<span style="flex-shrink: 0; font-size: 0.8rem;">{move["icon"]}</span>'
            f'<span style="color:#999; font-size:0.7rem; font-family: \'JetBrains Mono\', monospace; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; opacity: 0.8;">- {move.get("reasoning", "")}</span>'
            f'</div>'
        )
        logs_html += log_entry
    logs_html += "</div>"
    st.markdown(logs_html, unsafe_allow_html=True)

with col_b:
    render_tactical_board(f"{state['team_b']['name']} (PROPIO)", "beta-text", state['team_b'], f"Prendas encajadas: {state['team_b'].get('prendas_encajadas', 0)}")

st.markdown("<div style='height: 25px;'></div>", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# 6. Telemetría Dual (Puente Táctico JS con estilo original)
# ──────────────────────────────────────────────────────────────────────────────
tactical_telemetry_bridge(state)

# Footer Ultra-Compacto
st.markdown("<div style='border-top: 1px solid #1f2428; margin-top: 0px; margin-bottom: 5px;'></div>", unsafe_allow_html=True)
st.caption(f"Status: Playing - {state['team_a']['name']} vs {state['team_b']['name']} | Operational Dashboard v2.0")
