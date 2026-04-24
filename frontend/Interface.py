import streamlit as st
import pandas as pd
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

from src.styles.design_system import inject_styles
from src.renderers.holographics import get_holo_box_svg, get_holo_miss_svg
from src.data.bridge import get_game_state
from streamlit_autorefresh import st_autorefresh

# Polling transparente cada 2 segundos cuando Live Mode está activo
st_autorefresh(interval=2000, limit=None, key="data_polling")

inject_styles()
state = get_game_state()

# 4. Renderizadores
# ──────────────────────────────────────────────────────────────────────────────
def render_tactical_board(title, color_class, team_data, secondary_stat="", is_target=False, last_coord=None):
    stat_html = f"<small style='color:#666; font-family: \"JetBrains Mono\", monospace; font-weight: 400; text-transform:none; letter-spacing:0;'>{secondary_stat}</small>" if secondary_stat else ""
    st.markdown(f'<div class="tactical-header {color_class}"><span>{title}</span>{stat_html}</div>', unsafe_allow_html=True)
    
    rows = team_data.get('board', [])
    max_rows = len(rows) if rows else 10
    max_cols = len(rows[0]) if rows and rows[0] else 10

    cols = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")[:max_cols]
    
    # Determinar clase de etiqueta según el equipo
    label_team_class = "label-alpha" if "alpha" in color_class.lower() else "label-beta"
    board_glow_class = "board-alpha" if "alpha" in color_class.lower() else "board-beta"
    if is_target:
        board_glow_class += " target-highlight"
    
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
            
            # Colores base
            board_color = "#00ff88" if "alpha" in color_class.lower() else "#ff4b4b"
            attacker_color = "#ff4b4b" if "alpha" in color_class.lower() else "#00ff88"
            
            # Conexiones inteligentes (Soportando nuevos iconos logísticos)
            ship_syms = ["#", "X", "👕", "📦"]
            is_ship = sym in ship_syms
            
            if last_coord:
                let = last_coord[0].upper()
                try:
                    num = int(last_coord[1:]) - 1
                    if col == ord(let) - ord('A') and row == num:
                        cell_class += " new-action-anim"
                except ValueError:
                    pass
            
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

            # ── LÓGICA DE COLOR SELECTIVA (NUEVA REGLA) ──
            if sym in ["X", "👕", "📦"]:
                if sealed:
                    # Pedido completado: Todo del color del atacante
                    box_color = attacker_color
                    garment_color = attacker_color
                else:
                    # Pedido parcial: Caja del tablero, prenda del atacante
                    box_color = board_color
                    garment_color = attacker_color
            else:
                box_color = board_color
                garment_color = board_color

            # Inyectar color de neón dinámico (Borde de celda)
            cell_style = f"--team-neon: {box_color};"
            if is_ship: cell_style += " border: none !important;"

            if sym == "#": 
                content = get_holo_box_svg("IDLE", box_color, conn)
            elif sym in ["X", "👕", "📦"]: 
                content = get_holo_box_svg("LOAD", box_color, conn, sealed, garment_color=garment_color)
            elif sym in ["O", "❔"]: 
                content = get_holo_miss_svg()
            
            grid_html += f'<div class="{cell_class}" style="{cell_style}">{content}</div>'
    
    grid_html += '</div>'
    st.markdown(grid_html, unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# 5. Dashboard UI (Header & Layout)
# ──────────────────────────────────────────────────────────────────────────────
header_html = f"""
<div style="display: flex; justify-content: space-between; align-items: center; width: 100%; margin-bottom: 80px;">
    <div style="display: flex; align-items: center; gap: 15px;">
        <span class="led-red"></span>
        <h3 style="font-family: Orbitron; font-weight: 900; letter-spacing: 5px; color: white; margin: 0; padding: 0;">GARMENT STRIKE</h3>
    </div>
    <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; color: #666; letter-spacing: 1px;">
        TACTICAL OPERATIONS DASHBOARD
    </div>
</div>""".strip()

st.markdown(header_html, unsafe_allow_html=True)

# Layout Principal (Boards)
# 30% Tablero A - 40% Logs/Score - 30% Tablero B
col_a, col_mid, col_b = st.columns([30, 40, 30])

# Lógica de Highlight Táctico (FOCUS-01) y Animación (ANIM-01)
is_alpha_target = False
is_beta_target = False
last_coord = None
if state.get('comms'):
    last_move = state['comms'][-1]
    last_agent = last_move['agent'].upper()
    last_coord = last_move['coord']
    if "ALPHA" in last_agent or last_agent == "A":
        is_beta_target = True  # Alpha dispara a Beta
    else:
        is_alpha_target = True # Beta dispara a Alpha

with col_a:
    render_tactical_board(f"{state['team_a']['name']} (PROPIO)", "alpha-text", state['team_a'], f"Prendas encajadas: {state['team_a']['prendas_encajadas']}", is_target=is_alpha_target, last_coord=last_coord if is_alpha_target else None)

with col_mid:
    # ── NUEVO PANEL DE RESULTADOS (SCOREBOARD CENTRAL) ──
    scoreboard_html = f"""
    <div class="central-scoreboard">
        <div class="turn-badge">TURNO {state['turn']}</div>
        <div style="display: flex; justify-content: space-between; align-items: center; padding: 0 10px;">
            <div style="text-align: right; flex: 1;">
                <div style="color: var(--accent-alpha); font-family: Orbitron; font-weight: 700; font-size: 0.95rem; letter-spacing: 1px; margin-bottom: 5px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{state['team_a']['name']}</div>
                <div class="score-number" style="color: var(--accent-alpha); text-shadow: 0 0 20px rgba(0, 255, 136, 0.4);">{state['team_b']['pedidos_encajados']}</div>
                <div style="font-family: 'JetBrains Mono'; font-size: 0.7rem; color: #666; margin-top: 5px;">DE {state['team_b']['total_pedidos']} PEDIDOS</div>
            </div>
            <div class="score-divider" style="margin: 0 15px;">VS</div>
            <div style="text-align: left; flex: 1;">
                <div style="color: var(--accent-beta); font-family: Orbitron; font-weight: 700; font-size: 0.95rem; letter-spacing: 1px; margin-bottom: 5px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{state['team_b']['name']}</div>
                <div class="score-number" style="color: var(--accent-beta); text-shadow: 0 0 20px rgba(255, 75, 75, 0.4);">{state['team_a']['pedidos_encajados']}</div>
                <div style="font-family: 'JetBrains Mono'; font-size: 0.7rem; color: #666; margin-top: 5px;">DE {state['team_a']['total_pedidos']} PEDIDOS</div>
            </div>
        </div>
    </div>
    """
    st.markdown(scoreboard_html, unsafe_allow_html=True)

    # ── PANEL-01: ACCIÓN EN TIEMPO REAL ──
    if state['comms']:
        last_move = state['comms'][-1]
        is_alpha_move = "ALPHA" in last_move['agent'].upper() or "A" == last_move['agent'].upper()
        action_color = "var(--accent-alpha)" if is_alpha_move else "var(--accent-beta)"
        action_team = state['team_a']['name'] if is_alpha_move else state['team_b']['name']
        
        icon = last_move['icon']
        if icon == "📦":
            result_text = "PEDIDO ENCAJADO"
            result_color = "#00ff88"
        elif icon in ["👕", "X"]:
            result_text = "PRENDA ENCAJADA"
            result_color = "#ff8c00"
        else:
            result_text = "PRENDA PERDIDA"
            result_color = "#00d4ff"

        action_html = f"""
        <div style="background: rgba(255,255,255,0.03); border-left: 3px solid {action_color}; padding: 10px 15px; margin-bottom: 10px; border-radius: 4px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 4px 6px rgba(0,0,0,0.3);">
            <div>
                <div style="font-family: Orbitron; font-size: 0.65rem; color: #888; margin-bottom: 3px; letter-spacing: 1px;">ÚLTIMA ACCIÓN</div>
                <div style="color: {action_color}; font-weight: bold; font-family: 'JetBrains Mono'; font-size: 0.9rem;">{action_team} <span style="color: #fff; font-size: 0.8rem; margin: 0 5px;">→</span> {last_move['coord']}</div>
            </div>
            <div style="text-align: right;">
                <div style="font-family: Orbitron; font-size: 0.65rem; color: #888; margin-bottom: 3px; letter-spacing: 1px;">RESULTADO</div>
                <div style="color: {result_color}; font-weight: bold; font-family: Orbitron; font-size: 0.8rem; letter-spacing: 1px;">{result_text}</div>
            </div>
        </div>
        """
        st.markdown(action_html, unsafe_allow_html=True)

    st.markdown('<div class="log-title"><i class="fa-solid fa-terminal" style="margin-right:10px;"></i>MOVIMIENTOS</div>', unsafe_allow_html=True)
    
    logs_html = '<div class="log-scroll-area">'
    # Mostramos los últimos 10 movimientos para mantener Zero-Scroll
    for move in state['comms'][-10:]:
        color_agent = "var(--accent-alpha)" if "ALPHA" in move['agent'] or "A" == move['agent'] else "var(--accent-beta)"
        # Formato ultra-compacto: [T14] G7 📦- Detec...
        log_entry = (
            f'<div style="border-left: 2px solid {color_agent}; margin-bottom: 2px; background: rgba(255,255,255,0.02); '
            f'padding: 2px 8px; border-radius: 2px; display: flex; align-items: center; gap: 6px; overflow: hidden; line-height: 1;">'
            f'<span style="color:#666; font-size:0.7rem; flex-shrink: 0; font-family: \'JetBrains Mono\', monospace;">[T{move["turn"]}]</span>'
            f'<span style="color:#ccc; font-size:0.75rem; flex-shrink: 0; font-family: \'JetBrains Mono\', monospace; font-weight: 700; letter-spacing: 0px;">{move["coord"]}</span>'
            f'<span style="flex-shrink: 0; font-size: 0.8rem;">{move["icon"]}</span>'
            f'<span style="color:#999; font-size:0.7rem; font-family: \'JetBrains Mono\', monospace; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; opacity: 0.8;">- {move["reasoning"]}</span>'
            f'</div>'
        )
        logs_html += log_entry
    logs_html += "</div>"
    st.markdown(logs_html, unsafe_allow_html=True)

with col_b:
    render_tactical_board(f"{state['team_b']['name']} (PROPIO)", "beta-text", state['team_b'], f"Prendas encajadas: {state['team_b']['prendas_encajadas']}", is_target=is_beta_target, last_coord=last_coord if is_beta_target else None)

st.markdown("<div style='height: 25px;'></div>", unsafe_allow_html=True)

# st.markdown("<br>", unsafe_allow_html=True) # Eliminado para subir razonamientos

# ──────────────────────────────────────────────────────────────────────────────
# 6. Telemetría Dual (Razonamiento de IA por Equipo - Ultra Stacked)
# ──────────────────────────────────────────────────────────────────────────────
# Telemetría ALPHA
st.markdown(f"""
    <div class="telemetry-box" style="border-left-color: var(--accent-alpha); background: rgba(0, 255, 136, 0.03); margin-bottom: 8px; margin-top:0; padding: 6px 12px;">
        <table style="width:100%; border-collapse: collapse;">
            <tr>
                <td style="width:25%; vertical-align: top; border-right: 1px solid rgba(0, 255, 136, 0.1); padding-right: 12px;">
                    <div style="color:var(--accent-alpha); font-weight:bold; font-size:0.8rem; font-family:Orbitron; margin-bottom:4px; display:flex; align-items:center;">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right:8px;">
                            <path d="M12 5a3 3 0 1 0-5.997.125 4 4 0 0 0-2.526 5.77 4 4 0 0 0 .556 6.588A4 4 0 1 0 12 18Z"/>
                            <path d="M9 13a4.5 4.5 0 0 0 3-4"/>
                            <path d="M6.003 5.125A3 3 0 0 0 6.401 6.5"/>
                            <path d="M3.477 10.896a4 4 0 0 1 .556-6.588"/>
                            <path d="M16 13a3 3 0 1 0 5.997-.125 4 4 0 0 0 2.526-5.77 4 4 0 0 0-.556-6.588A4 4 0 1 0 12 5"/>
                            <path d="M15 13a4.5 4.5 0 0 1-3-4"/>
                            <path d="M17.997 5.125A3 3 0 0 1 17.599 6.5"/>
                            <path d="M20.523 10.896a4 4 0 0 0-.556-6.588"/>
                        </svg>
                        STRATEGY | {state["team_a"]["name"]}
                    </div>
                    <div style="color:#fff; font-size:0.85rem; font-family: 'JetBrains Mono', monospace;">{state['telemetry']['team_a']['strategy']}</div>
                </td>
                <td style="width:75%; vertical-align: top; padding-left: 15px;">
                    <div style="color:var(--accent-alpha); font-weight:bold; font-size:0.75rem; font-family:Orbitron; margin-bottom:4px; opacity:0.8;">RATIONALE</div>
                    <div style="color:#ddd; font-size:0.95rem; line-height:1.4; font-family: 'JetBrains Mono', monospace; font-weight: 400; letter-spacing: 0;">{state['telemetry']['team_a']['reasoning']}</div>
                </td>
            </tr>
        </table>
    </div>
""", unsafe_allow_html=True)

# Telemetría BETA
st.markdown(f"""
    <div class="telemetry-box" style="border-left-color: var(--accent-beta); background: rgba(255, 75, 75, 0.03); margin-bottom: 12px; margin-top:0; padding: 6px 12px;">
        <table style="width:100%; border-collapse: collapse;">
            <tr>
                <td style="width:25%; vertical-align: top; border-right: 1px solid rgba(255, 75, 75, 0.1); padding-right: 12px;">
                    <div style="color:var(--accent-beta); font-weight:bold; font-size:0.8rem; font-family:Orbitron; margin-bottom:4px; display:flex; align-items:center;">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right:8px;">
                            <path d="M12 5a3 3 0 1 0-5.997.125 4 4 0 0 0-2.526 5.77 4 4 0 0 0 .556 6.588A4 4 0 1 0 12 18Z"/>
                            <path d="M9 13a4.5 4.5 0 0 0 3-4"/>
                            <path d="M6.003 5.125A3 3 0 0 0 6.401 6.5"/>
                            <path d="M3.477 10.896a4 4 0 0 1 .556-6.588"/>
                            <path d="M16 13a3 3 0 1 0 5.997-.125 4 4 0 0 0 2.526-5.77 4 4 0 0 0-.556-6.588A4 4 0 1 0 12 5"/>
                            <path d="M15 13a4.5 4.5 0 0 1-3-4"/>
                            <path d="M17.997 5.125A3 3 0 0 1 17.599 6.5"/>
                            <path d="M20.523 10.896a4 4 0 0 0-.556-6.588"/>
                        </svg>
                        STRATEGY | {state["team_b"]["name"]}
                    </div>
                    <div style="color:#fff; font-size:0.85rem; font-family: 'JetBrains Mono', monospace;">{state['telemetry']['team_b']['strategy']}</div>
                </td>
                <td style="width:75%; vertical-align: top; padding-left: 15px;">
                    <div style="color:var(--accent-beta); font-weight:bold; font-size:0.75rem; font-family:Orbitron; margin-bottom:4px; opacity:0.8;">RATIONALE</div>
                    <div style="color:#ddd; font-size:0.95rem; line-height:1.4; font-family: 'JetBrains Mono', monospace; font-weight: 400; letter-spacing: 0;">{state['telemetry']['team_b']['reasoning']}</div>
                </td>
            </tr>
        </table>
    </div>
""", unsafe_allow_html=True)

# Footer Ultra-Compacto
st.markdown("<div style='border-top: 1px solid #1f2428; margin-top: 0px; margin-bottom: 5px;'></div>", unsafe_allow_html=True)
st.caption(f"Status: Playing - {state['team_a']['name']} vs {state['team_b']['name']} | Operational Dashboard v1.3")

# ──────────────────────────────────────────────────────────────────────────────
# Fin de Interface.py
# ──────────────────────────────────────────────────────────────────────────────

