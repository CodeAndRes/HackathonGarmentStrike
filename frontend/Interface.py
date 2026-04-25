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

# Polling manejado internamente por el panel táctico
# st_autorefresh(interval=5000, limit=None, key="data_polling")

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
    label_team_class = "label-alpha" if "alpha" in color_class.lower() else "label-beta"
    board_glow_class = "board-alpha" if "alpha" in color_class.lower() else "board-beta"
    grid_html = f'<div class="tactical-grid {board_glow_class} holo-wireframe" style="grid-template-columns: var(--coord-num-width) repeat({max_cols}, 1fr); grid-template-rows: var(--coord-let-height) repeat({max_rows}, 1fr);">'
    grid_html += f'<div class="cell label {label_team_class}"></div>'
    for c in cols: grid_html += f'<div class="cell label {label_team_class}">{c}</div>'
    for row in range(max_rows):
        grid_html += f'<div class="cell label {label_team_class}">{row+1}</div>'
        for col in range(max_cols):
            try: sym = rows[row][col]
            except (IndexError, KeyError): sym = "~"
            fleet = team_data.get('fleet', {})
            ship_id = fleet.get((row, col), "NONE")
            cell_class = "cell holo-cell"
            content = ""
            team_color = "#00ff88" if "alpha" in color_class.lower() else "#ff4b4b"
            ship_syms = ["#", "X", "👕", "📦"]
            is_ship = sym in ship_syms
            cell_style = f"--team-neon: {team_color};"
            if is_ship: cell_style += " border: none !important;"
            conn = {"top": False, "bottom": False, "left": False, "right": False}
            sealed = False
            if is_ship and ship_id != "NONE":
                if row > 0 and rows[row-1][col] in ship_syms and fleet.get((row-1, col)) == ship_id: conn["top"] = True
                if row < max_rows - 1 and rows[row+1][col] in ship_syms and fleet.get((row+1, col)) == ship_id: conn["bottom"] = True
                if col > 0 and rows[row][col-1] in ship_syms and fleet.get((row, col-1)) == ship_id: conn["left"] = True
                if col < max_cols - 1 and rows[row][col+1] in ship_syms and fleet.get((row, col+1)) == ship_id: conn["right"] = True
                if sym in ["X", "👕", "📦"]:
                    sealed = True
                    for (r, c), sid in fleet.items():
                        if sid == ship_id and rows[r][c] not in ["X", "👕", "📦"]:
                            sealed = False
                            break
            if sym == "#": content = get_holo_box_svg("IDLE", team_color, conn)
            elif sym in ["X", "👕", "📦"]: content = get_holo_box_svg("LOAD", team_color, conn, sealed)
            elif sym in ["O", "❔"]: content = get_holo_miss_svg()
            grid_html += f'<div class="{cell_class}" style="{cell_style}">{content}</div>'
    grid_html += '</div>'
    st.markdown(grid_html, unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# 5. Dashboard UI (Cabecera Optimizada Compacta)
# ──────────────────────────────────────────────────────────────────────────────
header_html = f"""<div style="display: flex; justify-content: space-between; align-items: center; width: 100%; border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 15px; margin-bottom: 60px; gap: 15px;">
<h3 style="font-family: Orbitron; font-weight: 900; letter-spacing: 5px; color: white; margin: 0; padding: 0; flex-shrink: 0;">⚡ GARMENT STRIKE</h3>
<div style="display: flex; align-items: center; gap: 15px; background: rgba(255,255,255,0.02); padding: 3px 12px; border-radius: 4px; border: 1px solid rgba(255,255,255,0.05); font-family: 'JetBrains Mono', monospace; font-size: 0.7rem; color: #e6edf3; flex-shrink: 0;">
<div style="display: flex; align-items: center; border-right: 1px solid #333; padding-right: 12px; gap: 6px;"><span class="led-red"></span><span style="color:#ff4b4b; font-family:Orbitron; font-weight:bold; font-size:0.65rem;">LIVE</span></div>
<div style="border-right: 1px solid #333; padding-right: 12px;">TURNO: <b style="color:#00d4ff;">#{state['turn']}</b></div>
<div style="border-right: 1px solid #333; padding-right: 12px;"><span class="alpha-text">{state['team_a']['name']}</span>: <b>{state['team_a']['pedidos_encajados']}/{state['team_a']['total_pedidos']}</b></div>
<div><span class="beta-text">{state['team_b']['name']}</span>: <b>{state['team_b']['pedidos_encajados']}/{state['team_b']['total_pedidos']}</b></div></div></div>"""
st.markdown(header_html, unsafe_allow_html=True)

col_a, col_mid, col_b = st.columns([32, 36, 32])
with col_a: render_tactical_board(f"{state['team_a']['name']} (PROPIO)", "alpha-text", state['team_a'], f"Prendas encajadas: {state['team_a'].get('prendas_encajadas', 0)}")
with col_mid:
    s_a, s_b = state['team_a']['pedidos_encajados'], state['team_b']['pedidos_encajados']
    turn_text = f"TURNO #{state['turn']}"
    st.markdown(f"""<div class="central-scoreboard"><div class="turn-badge">{turn_text}</div>
<div style="display:flex; justify-content:center; align-items:center; gap:20px;"><div style="--team-neon: var(--accent-alpha);"><div class="score-number">{s_a}</div>
<div style="font-size:0.6rem; opacity:0.5; color:var(--accent-alpha); margin-top:5px; font-family:Orbitron;">{state['team_a']['name']}</div></div>
<div class="score-divider">VS</div><div style="--team-neon: var(--accent-beta);"><div class="score-number">{s_b}</div>
<div style="font-size:0.6rem; opacity:0.5; color:var(--accent-beta); margin-top:5px; font-family:Orbitron;">{state['team_b']['name']}</div></div></div></div>""", unsafe_allow_html=True)
    st.markdown('<div class="log-title"><i class="fa-solid fa-terminal" style="margin-right:10px;"></i>MOVIMIENTOS</div>', unsafe_allow_html=True)
    if state['comms']:
        last_m = state['comms'][-1]
        c_last = "var(--accent-alpha)" if "A" in last_m['agent'] else "var(--accent-beta)"
        st.markdown(f"""<div style="background: rgba(255,255,255,0.03); border: 1px solid {c_last}; border-radius: 6px; padding: 12px; margin-bottom: 15px; position: relative; overflow: hidden;"><div style="position: absolute; top: 0; left: 0; width: 4px; height: 100%; background: {c_last};"></div>
<div style="font-family: Orbitron; font-size: 0.6rem; color: {c_last}; letter-spacing: 2px; margin-bottom: 5px; font-weight: 900;">LAST OPERATION REGISTERED</div>
<div style="display: flex; align-items: center; gap: 15px;"><span style="font-family: Orbitron; font-size: 1.5rem; font-weight: 900; color: #fff;">{last_m['coord']}</span>
<span style="font-size: 1.2rem;">{last_m['icon']}</span><div style="flex-grow: 1;"><div style="font-family: 'JetBrains Mono'; font-size: 0.75rem; color: {c_last}; font-weight: bold;">{last_m['result']}</div>
<div style="font-family: 'JetBrains Mono'; font-size: 0.65rem; color: #888; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 250px;">{last_m.get('reasoning', '')}</div></div>
<div style="font-family: Orbitron; font-size: 0.8rem; color: rgba(255,255,255,0.2);">T{last_m['turn']}</div></div></div>""", unsafe_allow_html=True)
    logs_html = '<div class="log-scroll-area">'
    for move in state['comms'][:-16:-1]:
        color_agent = "var(--accent-alpha)" if "ALPHA" in move['agent'] or "A" == move['agent'] else "var(--accent-beta)"
        log_entry = f'<div style="border-left: 2px solid {color_agent}; margin-bottom: 2px; background: rgba(255,255,255,0.02); padding: 2px 8px; border-radius: 2px; display: flex; align-items: center; gap: 6px; overflow: hidden; line-height: 1;"><span style="color:#666; font-size:0.7rem; flex-shrink: 0; font-family: \'JetBrains Mono\', monospace;">[T{move["turn"]}]</span><span style="color:#ccc; font-size:0.75rem; flex-shrink: 0; font-family: \'JetBrains Mono\', monospace; font-weight: 700; letter-spacing: 0px;">{move["coord"]}</span><span style="flex-shrink: 0; font-size: 0.8rem;">{move["icon"]}</span><span style="color:#999; font-size:0.7rem; font-family: \'JetBrains Mono\', monospace; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; opacity: 0.8;">- {move.get("reasoning", "")}</span></div>'
        logs_html += log_entry
    logs_html += "</div>"
    st.markdown(logs_html, unsafe_allow_html=True)
with col_b: render_tactical_board(f"{state['team_b']['name']} (PROPIO)", "beta-text", state['team_b'], f"Prendas encajadas: {state['team_b'].get('prendas_encajadas', 0)}")
st.markdown("<div style='height: 20px; border-top: 1px solid rgba(255,255,255,0.05); margin-top: 10px;'></div>", unsafe_allow_html=True)
tactical_telemetry_bridge(state)
st.markdown("<div style='border-top: 1px solid #1f2428; margin-top: 0px; margin-bottom: 5px;'></div>", unsafe_allow_html=True)
st.caption(f"Status: Playing - {state['team_a']['name']} vs {state['team_b']['name']} | Operational Dashboard v2.0")
