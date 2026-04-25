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

state = get_game_state()

# Polling inteligente: 0.5s en partida, 5s en espera para detectar resets automáticos
refresh_interval = 500 if not state.get('finished') else 5000
st_autorefresh(interval=refresh_interval, limit=None, key="data_polling")

# --- DETECTOR DE NUEVA PARTIDA ---
if 'prev_turn' not in st.session_state:
    st.session_state.prev_turn = -1

# Si detectamos que el turno ha vuelto a empezar, reseteamos el estado visual
if state.get('turn', 0) < st.session_state.prev_turn:
    st.session_state.winner_celebrated = False
    if state.get('turn', 0) == 0:
        state['finished'] = False

st.session_state.prev_turn = state.get('turn', 0)
# ---------------------------------

inject_styles()
st.markdown("""
<style>
    @keyframes blink {
      0%, 100% { opacity: 1; }
      50% { opacity: 0; }
    }
    .cursor {
        display: inline-block;
        width: 10px;
        height: 1.2em;
        background: currentColor;
        margin-left: 4px;
        vertical-align: middle;
        animation: blink 1s step-end infinite;
    }
</style>
""", unsafe_allow_html=True)
state = get_game_state()

# ── GESTIÓN DE SONIDOS (NEW) ──
import base64
from pathlib import Path

def get_audio_b64(file_name):
    try:
        path = Path("frontend/assets/sounds") / file_name
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except Exception:
        return ""

if 'last_turn_sound' not in st.session_state:
    st.session_state.last_turn_sound = -1

if state.get('turn', 0) > st.session_state.last_turn_sound:
    if state.get('comms'):
        icon = state['comms'][-1]['icon']
        sound_file = ""
        if icon == "📦": sound_file = "sink.wav" # Sunk
        elif icon in ["👕", "X"]: sound_file = "hit.wav" # Hit
        else: sound_file = "miss.wav" # Miss
        
        b64 = get_audio_b64(sound_file)
        if b64:
            st.markdown(f'<audio autoplay style="display:none;"><source src="data:audio/wav;base64,{b64}" type="audio/wav"></audio>', unsafe_allow_html=True)
    st.session_state.last_turn_sound = state['turn']

# ── PANTALLA DE FIN DE PARTIDA (NEW) ──
if state.get('finished'):
    if not st.session_state.get('winner_celebrated'):
        st.balloons()
        st.session_state.winner_celebrated = True

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
<div style="display: flex; justify-content: space-between; align-items: center; width: 100%; margin-bottom: 25px;">
    <div style="display: flex; align-items: center; gap: 15px;">
        <svg width="38" height="38" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="color:white; filter: drop-shadow(0 0 8px rgba(255,255,255,0.3));">
            <path d="M20.38 3.46L16 2a4 4 0 01-8 0L3.62 3.46a2 2 0 00-1.34 2.23l.58 3.47a1 1 0 00.99.84H6v10c0 1.1.9 2 2 2h8a2 2 0 002-2V10h2.15a1 1 0 00.99-.84l.58-3.47a2 2 0 00-1.34-2.23z"/>
        </svg>
        <h3 style="font-family: Orbitron; font-weight: 900; font-size: 2.2rem; letter-spacing: 7px; color: white; margin: 0; padding: 0; text-shadow: 0 0 20px rgba(255,255,255,0.1);">GARMENT STRIKE</h3>
    </div>
    <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; color: #666; letter-spacing: 1px;">
        TACTICAL OPERATIONS DASHBOARD
    </div>
</div>""".strip()

st.markdown(header_html, unsafe_allow_html=True)

# Layout Principal (Boards)
# 30% Tablero A - 40% Logs/Score - 30% Tablero B
col_a, col_mid, col_b = st.columns([30, 40, 30])

# Lógica de Highlight Táctico y Cursor Dinámico
is_alpha_target = False
is_beta_target = False
last_coord = None

if state.get('comms'):
    last_move = state['comms'][-1]
    last_agent = last_move['agent'].upper()
    last_coord = last_move['coord']
    
    # El glow solo se activa si el movimiento NO es pending (es decir, ya ocurrió)
    if last_move.get('result') != 'PENDING' and last_move.get('result') != 'WAITING':
        if "ALPHA" in last_agent or last_agent == "A":
            is_beta_target = True  # Alpha disparó a Beta
        else:
            is_alpha_target = True # Beta disparó a Alpha

# Extracción de cursores de telemetría
t_a = state['telemetry']['team_a']
t_b = state['telemetry']['team_b']
cursor_strat_a = '<span class="cursor"></span>' if t_a.get('cursor') == "strategy" else ""
cursor_reason_a = '<span class="cursor"></span>' if t_a.get('cursor') == "reasoning" else ""
cursor_strat_b = '<span class="cursor"></span>' if t_b.get('cursor') == "strategy" else ""
cursor_reason_b = '<span class="cursor"></span>' if t_b.get('cursor') == "reasoning" else ""

with col_a:
    st.markdown('<div style="margin-top: 60px;"></div>', unsafe_allow_html=True)
    
    # Glow condicional si es el equipo activo + Corona si es el ganador
    alpha_glow = "text-shadow: 0 0 20px var(--accent-alpha), 0 0 40px rgba(0, 255, 136, 0.4);" if is_alpha_target else ""
    display_name_a = state["team_a"]["name"].upper()
    if state.get('finished') and state.get('winner') == state["team_a"]["name"]:
        display_name_a = f"👑 {display_name_a}"
        
    st.markdown(f'<div style="text-align: right; color: var(--accent-alpha); font-family: Orbitron; font-weight: 900; font-size: 2.2rem; letter-spacing: 3px; margin-bottom: -5px; line-height: 1; {alpha_glow}">{display_name_a}</div>', unsafe_allow_html=True)
    
    # Quitamos is_target del tablero
    render_tactical_board("", "alpha-text", state['team_a'], "", is_target=False, last_coord=last_coord if is_alpha_target else None)

with col_mid:
    # ── NUEVO PANEL DE RESULTADOS (SCOREBOARD CENTRAL) ──
    scoreboard_html = f"""<div class="central-scoreboard" style="padding: 15px 10px 5px 10px; margin-bottom: 10px; position: relative;">
        <div style="position: absolute; top: 8px; left: 12px; display: flex; align-items: center; gap: 6px;">
            <div class="led-red" style="background-color: {'#ff4b4b' if not state.get('finished') else '#888'}; box-shadow: 0 0 8px {'#ff4b4b' if not state.get('finished') else '#444'}; animation: {'pulse-red 1s infinite ease-in-out' if not state.get('finished') else 'none'};"></div>
            <span style="color: {'#ff4b4b' if not state.get('finished') else '#888'}; font-family: Orbitron; font-size: 0.65rem; font-weight: 900; letter-spacing: 2px;">{'LIVE' if not state.get('finished') else 'MATCH OVER'}</span>
        </div>
        <div class="turn-badge" style="top: -12px; font-size: 0.75rem; background: #00d4ff; color: #000; padding: 2px 15px; border-radius: 10px; box-shadow: 0 0 15px rgba(0, 212, 255, 0.4);">TURNO {state['turn']}</div>
        <div style="display: flex; justify-content: center; align-items: baseline; gap: 40px;">
            <div style="display: flex; align-items: baseline; gap: 10px;">
                <div class="score-number" style="color: var(--accent-alpha); font-size: 4.5rem; text-shadow: 0 0 30px rgba(0, 255, 136, 0.5); line-height: 1;">{state['team_b']['pedidos_encajados']}</div>
                <div style="text-align: left; line-height: 1.2;">
                    <span style="font-family: 'JetBrains Mono'; font-size: 0.75rem; color: #666; text-transform: uppercase; letter-spacing: 1px;">/{state['team_b']['total_pedidos']} PEDIDOS</span><br>
                    <span style="font-family: 'JetBrains Mono'; font-size: 0.85rem; color: var(--accent-alpha); opacity: 0.9; font-weight: bold;">{state['team_b']['prendas_encajadas']} PRENDAS</span>
                </div>
            </div>
            <div style="font-family: 'Orbitron'; font-size: 1rem; color: rgba(255,255,255,0.2); font-weight: 900; align-self: center; margin-bottom: 20px;">VS</div>
            <div style="display: flex; align-items: baseline; gap: 10px;">
                <div class="score-number" style="color: var(--accent-beta); font-size: 4.5rem; text-shadow: 0 0 30px rgba(255, 75, 75, 0.5); line-height: 1;">{state['team_a']['pedidos_encajados']}</div>
                <div style="text-align: left; line-height: 1.2;">
                    <span style="font-family: 'JetBrains Mono'; font-size: 0.75rem; color: #666; text-transform: uppercase; letter-spacing: 1px;">/{state['team_a']['total_pedidos']} PEDIDOS</span><br>
                    <span style="font-family: 'JetBrains Mono'; font-size: 0.85rem; color: var(--accent-beta); opacity: 0.9; font-weight: bold;">{state['team_a']['prendas_encajadas']} PRENDAS</span>
                </div>
            </div>
        </div>
    </div>"""
    st.markdown(scoreboard_html, unsafe_allow_html=True)

    # ── PANEL-01: ACCIÓN EN TIEMPO REAL ──
    if state['comms']:
        last_move = state['comms'][-1]
        is_alpha_move = "ALPHA" in last_move['agent'].upper() or "A" == last_move['agent'].upper()
        action_color = "var(--accent-alpha)" if is_alpha_move else "var(--accent-beta)"
        action_team = state['team_a']['name'] if is_alpha_move else state['team_b']['name']
        target_color = "var(--accent-beta)" if is_alpha_move else "var(--accent-alpha)"
        
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

        is_sunk = icon == "📦"
        bg_tint = "rgba(0, 255, 136, 0.08)" if is_alpha_move else "rgba(255, 75, 75, 0.08)"
        box_shadow = f"0 0 15px {action_color}" if is_sunk else "0 4px 6px rgba(0,0,0,0.3)"
        border_width = "4px" if is_sunk else "2px"

        action_html = f"""<div style="background: {bg_tint}; border-left: {border_width} solid {action_color}; padding: 8px 15px; margin-bottom: 10px; border-radius: 4px; display: flex; justify-content: space-between; align-items: center; box-shadow: {box_shadow}; margin-top: 15px;">
            <div style="display: flex; align-items: center; gap: 10px;">
                <div style="color: {action_color}; font-weight: 700; font-family: 'JetBrains Mono'; font-size: 0.9rem;">{action_team.lower()} <span style="color: #fff; font-size: 0.8rem; margin: 0 5px;">→</span> <span style="color: {target_color};">{last_move['coord']}</span></div>
            </div>
            <div style="text-align: right;">
                <div style="color: {result_color}; font-weight: 800; font-family: Orbitron; font-size: 0.75rem; letter-spacing: 1px;">{result_text}</div>
            </div>
        </div>
        """
        st.markdown(action_html, unsafe_allow_html=True)

    # st.markdown('<div class="log-title"><i class="fa-solid fa-terminal" style="margin-right:10px;"></i>MOVIMIENTOS</div>', unsafe_allow_html=True)
    
    logs_html = '<div class="log-scroll-area" style="max-height: 42vh; overflow: hidden;">'
    # Mostramos los movimientos previos (hasta 50 para aprovechar pantallas grandes, excluyendo el más reciente)
    prev_moves = state['comms'][-51:-1] if len(state['comms']) > 1 else []
    for move in reversed(prev_moves):
        is_sunk = move['icon'] == "📦"
        color_agent = "var(--accent-alpha)" if "ALPHA" in move['agent'] or "A" == move['agent'] else "var(--accent-beta)"
        
        # Highlight si es un pedido encajado (HUNDIDO)
        bg_style = "rgba(0, 255, 136, 0.15)" if is_sunk and color_agent == "var(--accent-alpha)" else \
                   "rgba(255, 75, 75, 0.15)" if is_sunk and color_agent == "var(--accent-beta)" else \
                   "rgba(255,255,255,0.02)"
        
        border_style = f"3px solid {color_agent}" if is_sunk else f"2px solid {color_agent}"
        font_weight = "800" if is_sunk else "400"
        
        log_entry = (
            f'<div style="border-left: {border_style}; margin-bottom: 2px; background: {bg_style}; '
            f'padding: 4px 8px; border-radius: 2px; display: flex; align-items: center; gap: 6px; overflow: hidden; line-height: 1;">'
            f'<span style="color:#666; font-size:0.8rem; flex-shrink: 0; font-family: \'JetBrains Mono\', monospace;">[T{move["turn"]}]</span>'
            f'<span style="color:#ccc; font-size:0.85rem; flex-shrink: 0; font-family: \'JetBrains Mono\', monospace; font-weight: {font_weight}; letter-spacing: 0px;">{move["coord"]}</span>'
            f'<span style="flex-shrink: 0; font-size: 0.95rem;">{move["icon"]}</span>'
            f'<span style="color:#aaa; font-size:0.8rem; font-family: \'JetBrains Mono\', monospace; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; opacity: 0.9;">- {move["reasoning"]}</span>'
            f'</div>'
        )
        logs_html += log_entry
    logs_html += "</div>"
    st.markdown(logs_html, unsafe_allow_html=True)

with col_b:
    st.markdown('<div style="margin-top: 60px;"></div>', unsafe_allow_html=True)
    
    # Glow condicional si es el equipo activo + Corona si es el ganador
    beta_glow = "text-shadow: 0 0 20px var(--accent-beta), 0 0 40px rgba(255, 75, 75, 0.4);" if is_beta_target else ""
    display_name_b = state["team_b"]["name"].upper()
    if state.get('finished') and state.get('winner') == state["team_b"]["name"]:
        display_name_b = f"{display_name_b} 👑"

    st.markdown(f'<div style="text-align: left; color: var(--accent-beta); font-family: Orbitron; font-weight: 900; font-size: 2.2rem; letter-spacing: 3px; margin-bottom: -5px; line-height: 1; {beta_glow}">{display_name_b}</div>', unsafe_allow_html=True)
    
    # Quitamos is_target del tablero
    render_tactical_board("", "beta-text", state['team_b'], "", is_target=False, last_coord=last_coord if is_beta_target else None)

st.markdown("<div style='height: 25px;'></div>", unsafe_allow_html=True)

# st.markdown("<br>", unsafe_allow_html=True) # Eliminado para subir razonamientos

# ──────────────────────────────────────────────────────────────────────────────
# 6. Telemetría Dual (Razonamiento de IA por Equipo - Ultra Stacked)
# ──────────────────────────────────────────────────────────────────────────────
# Telemetría ALPHA
alpha_box_glow = f"box-shadow: 0 0 25px rgba(0, 255, 136, 0.3); border: 1px solid var(--accent-alpha);" if is_alpha_target else "border: 1px solid rgba(255,255,255,0.05);"
st.markdown(f"""
    <div class="telemetry-box" style="border-left: 4px solid var(--accent-alpha); {alpha_box_glow} background: rgba(0, 255, 136, 0.04); margin-bottom: 8px; margin-top:0; padding: 10px 15px; border-radius: 4px;">
        <div style="display: flex; gap: 20px; align-items: flex-start;">
            <div style="flex: 0 0 25%; border-right: 1px solid rgba(0, 255, 136, 0.1); padding-right: 15px;">
                <div style="color:var(--accent-alpha); font-weight:bold; font-size:0.75rem; font-family:Orbitron; margin-bottom:6px; display:flex; align-items:center; text-transform: uppercase; letter-spacing: 1px;">
                    <span style="margin-right:8px;">🚀</span>STRATEGY | {state["team_a"]["name"].lower()}
                </div>
                <div style="color:#fff; font-size:0.8rem; font-family: 'JetBrains Mono', monospace; font-weight: 400;">{t_a['strategy']}{cursor_strat_a}</div>
            </div>
            <div style="flex: 1;">
                <div style="color:var(--accent-alpha); font-weight:bold; font-size:0.7rem; font-family:Orbitron; margin-bottom:6px; opacity:0.6; text-transform: uppercase; letter-spacing: 1px;">RATIONALE</div>
                <div style="color:#ccc; font-size:0.85rem; line-height:1.4; font-family: 'JetBrains Mono', monospace;">{t_a['reasoning']}{cursor_reason_a}</div>
            </div>
        </div>
    </div>
""", unsafe_allow_html=True)

# Telemetría BETA
beta_box_glow = f"box-shadow: 0 0 25px rgba(255, 75, 75, 0.3); border: 1px solid var(--accent-beta);" if is_beta_target else "border: 1px solid rgba(255,255,255,0.05);"
st.markdown(f"""
    <div class="telemetry-box" style="border-left: 4px solid var(--accent-beta); {beta_box_glow} background: rgba(255, 75, 75, 0.04); margin-bottom: 15px; margin-top:0; padding: 10px 15px; border-radius: 4px;">
        <div style="display: flex; gap: 20px; align-items: flex-start;">
            <div style="flex: 0 0 25%; border-right: 1px solid rgba(255, 75, 75, 0.1); padding-right: 15px;">
                <div style="color:var(--accent-beta); font-weight:bold; font-size:0.75rem; font-family:Orbitron; margin-bottom:6px; display:flex; align-items:center; text-transform: uppercase; letter-spacing: 1px;">
                    <span style="margin-right:8px;">🎯</span>STRATEGY | {state["team_b"]["name"].lower()}
                </div>
                <div style="color:#fff; font-size:0.8rem; font-family: 'JetBrains Mono', monospace; font-weight: 400;">{t_b['strategy']}{cursor_strat_b}</div>
            </div>
            <div style="flex: 1;">
                <div style="color:var(--accent-beta); font-weight:bold; font-size:0.7rem; font-family:Orbitron; margin-bottom:6px; opacity:0.6; text-transform: uppercase; letter-spacing: 1px;">RATIONALE</div>
                <div style="color:#ccc; font-size:0.85rem; line-height:1.4; font-family: 'JetBrains Mono', monospace;">{t_b['reasoning']}{cursor_reason_b}</div>
            </div>
        </div>
    </div>
""", unsafe_allow_html=True)

# Footer Ultra-Compacto
st.markdown("<div style='border-top: 1px solid #1f2428; margin-top: 0px; margin-bottom: 5px;'></div>", unsafe_allow_html=True)
st.caption(f"Status: Playing - {state['team_a']['name']} vs {state['team_b']['name']} | Operational Dashboard v1.3")

# ──────────────────────────────────────────────────────────────────────────────
# Fin de Interface.py
# ──────────────────────────────────────────────────────────────────────────────

