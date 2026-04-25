import streamlit as st
import streamlit.components.v1 as components
import json

def _json_cleaner(obj):
    if isinstance(obj, dict):
        return {str(k): _json_cleaner(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_json_cleaner(i) for i in obj]
    return obj

def tactical_telemetry_bridge(game_state: dict):
    """
    Telemetría dual con estilo original (border-left, table layout).
    Integra WebSocket para actualizaciones en tiempo real.
    """
    tel = game_state.get("telemetry", {})
    tel_a = tel.get("team_a", {})
    tel_b = tel.get("team_b", {})

    # Telemetría ALPHA (Estilo original con tabla)
    brain_svg = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right:8px;"><path d="M12 5a3 3 0 1 0-5.997.125 4 4 0 0 0-2.526 5.77 4 4 0 0 0 .556 6.588A4 4 0 1 0 12 18Z"/><path d="M9 13a4.5 4.5 0 0 0 3-4"/><path d="M6.003 5.125A3 3 0 0 0 6.401 6.5"/><path d="M3.477 10.896a4 4 0 0 1 .556-6.588"/><path d="M16 13a3 3 0 1 0 5.997-.125 4 4 0 0 0 2.526-5.77 4 4 0 0 0-.556-6.588A4 4 0 1 0 12 5"/><path d="M15 13a4.5 4.5 0 0 1-3-4"/><path d="M17.997 5.125A3 3 0 0 1 17.599 6.5"/><path d="M20.523 10.896a4 4 0 0 0-.556-6.588"/></svg>'

    st.markdown(f"""
    <div class="telemetry-box" style="border-left-color: var(--accent-alpha); background: rgba(0, 255, 136, 0.03); margin-bottom: 8px; margin-top:0; padding: 6px 12px;">
        <table style="width:100%; border-collapse: collapse;">
            <tr>
                <td style="width:25%; vertical-align: top; border-right: 1px solid rgba(0, 255, 136, 0.1); padding-right: 12px;">
                    <div style="color:var(--accent-alpha); font-weight:bold; font-size:0.8rem; font-family:Orbitron; margin-bottom:4px; display:flex; align-items:center;">
                        {brain_svg}
                        STRATEGY | {game_state["team_a"]["name"]}
                    </div>
                    <div style="color:#fff; font-size:0.85rem; font-family: 'JetBrains Mono', monospace;">{tel_a.get('strategy', 'Procesando...')}</div>
                </td>
                <td style="width:75%; vertical-align: top; padding-left: 15px;">
                    <div style="color:var(--accent-alpha); font-weight:bold; font-size:0.75rem; font-family:Orbitron; margin-bottom:4px; opacity:0.8;">RATIONALE</div>
                    <div style="color:#ddd; font-size:0.95rem; line-height:1.4; font-family: 'JetBrains Mono', monospace; font-weight: 400; letter-spacing: 0;">{tel_a.get('reasoning', 'Esperando datos...')}</div>
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
                        {brain_svg}
                        STRATEGY | {game_state["team_b"]["name"]}
                    </div>
                    <div style="color:#fff; font-size:0.85rem; font-family: 'JetBrains Mono', monospace;">{tel_b.get('strategy', 'Procesando...')}</div>
                </td>
                <td style="width:75%; vertical-align: top; padding-left: 15px;">
                    <div style="color:var(--accent-beta); font-weight:bold; font-size:0.75rem; font-family:Orbitron; margin-bottom:4px; opacity:0.8;">RATIONALE</div>
                    <div style="color:#ddd; font-size:0.95rem; line-height:1.4; font-family: 'JetBrains Mono', monospace; font-weight: 400; letter-spacing: 0;">{tel_b.get('reasoning', 'Esperando datos...')}</div>
                </td>
            </tr>
        </table>
    </div>
    """, unsafe_allow_html=True)

    # WebSocket bridge invisible para refrescos automáticos
    ws_html = f"""
    <script>
        let currentTurn = {game_state.get('turn', 0)};
        function connectWS() {{
            try {{
                const socket = new WebSocket('ws://' + window.location.hostname + ':8000/ws/tactical');
                socket.onmessage = (event) => {{
                    const newState = JSON.parse(event.data);
                    if (newState.turn !== currentTurn) {{
                        currentTurn = newState.turn;
                        window.parent.postMessage({{type: 'streamlit:setComponentValue', value: newState}}, '*');
                    }}
                }};
                socket.onclose = () => setTimeout(connectWS, 2000);
            }} catch(e) {{}}
        }}
        connectWS();
    </script>
    """
    components.html(ws_html, height=0)
