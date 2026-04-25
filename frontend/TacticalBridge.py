import streamlit as st
import streamlit.components.v1 as components
import json

def tactical_telemetry_bridge(game_state: dict):
    """Telemetría Pro con motor de renderizado JS Nativo e inteligencia de persistencia."""
    
    state_json = json.dumps({
        "turn": game_state.get("turn"),
        "turn_agent": game_state.get("turn_agent"),
        "comms": game_state.get("comms", []),
        "telemetry": game_state.get("telemetry", {}),
        "team_a": {"name": game_state.get("team_a", {}).get("name")},
        "team_b": {"name": game_state.get("team_b", {}).get("name")}
    })

    html_content = f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=JetBrains+Mono:wght@400;700&display=swap');
        :root {{ --accent-alpha: #00ff88; --accent-beta: #ff4b4b; }}
        body {{ margin: 0; padding: 0; background: transparent; overflow: hidden; color: #fff; font-family: 'JetBrains Mono', monospace; }}
        .telemetry-container {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
        .panel {{ background: rgba(13, 17, 23, 0.95); border-radius: 12px; padding: 15px; transition: all 0.5s ease; height: 210px; display: flex; flex-direction: column; overflow: hidden; }}
        .panel.active {{ box-shadow: 0 0 25px rgba(255,255,255,0.05); }}
        .header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; border-bottom: 1px solid rgba(255,255,255,0.08); padding-bottom: 6px; font-family: 'Orbitron'; font-size: 0.8rem; font-weight: 700; }}
        .label {{ color: rgba(255,255,255,0.3); font-size: 0.55rem; letter-spacing: 1px; margin-bottom: 3px; font-family: 'Orbitron'; }}
        .content {{ color: #fff; font-size: 0.78rem; line-height: 1.3; margin-bottom: 8px; min-height: 2.6em; }}
        .action-box {{ background: rgba(255,255,255,0.03); padding: 6px 10px; border-radius: 4px; display: flex; justify-content: space-between; align-items: center; font-size: 0.75rem; margin-top: auto; }}
        .typing-cursor {{ border-right: 2px solid currentColor; animation: blink 0.7s infinite; margin-left: 2px; }}
        @keyframes blink {{ 0%, 100% {{ opacity: 1; }} 50% {{ opacity: 0; }} }}
        .active-badge {{ font-size: 0.5rem; padding: 2px 6px; border-radius: 3px; background: currentColor; color: #000; font-weight: 900; }}
    </style>
    <div class="telemetry-container" id="container"></div>
    <script>
        const state = {state_json};
        const container = document.getElementById('container');
        
        // Memoria de sesión para evitar repetir animaciones
        const storageKey = 'gs_telemetry_last';
        const lastData = JSON.parse(sessionStorage.getItem(storageKey) || '{{}}');

        function renderPanel(teamKey, color) {{
            const tel = state.telemetry[teamKey] || {{}};
            const isActive = state.turn_agent === teamKey;
            
            let lastMove = "---";
            const agentId = teamKey === "team_a" ? "A" : "B";
            for (let i = state.comms.length - 1; i >= 0; i--) {{
                if (state.comms[i].agent === agentId) {{
                    lastMove = state.comms[i].coord + " " + state.comms[i].icon + " (" + state.comms[i].result + ")";
                    break;
                }}
            }}

            const panel = document.createElement('div');
            panel.className = 'panel' + (isActive ? ' active' : '');
            panel.style.border = isActive ? '2px solid ' + color : '1px solid rgba(255,255,255,0.1)';
            panel.style.opacity = isActive ? '1' : '0.5';

            panel.innerHTML = `
                <div class="header" style="color: ${{color}}">
                    <span>STRATEGY | ${{state[teamKey].name}}</span>
                    ${{isActive ? `<span class="active-badge" style="background:${{color}}">BRAIN ACTIVE</span>` : ''}}
                </div>
                <div>
                    <div class="label">OBJECTIVE:</div>
                    <div class="content" id="strat_${{teamKey}}"></div>
                </div>
                <div>
                    <div class="label">RATIONALE:</div>
                    <div class="content" id="reason_${{teamKey}}"></div>
                </div>
                <div class="action-box">
                    <div class="label" style="margin:0">LAST ACTION:</div>
                    <div style="color:${{color}}; font-family:Orbitron; font-weight:900; font-size:0.7rem;">${{lastMove}}</div>
                </div>
            `;
            container.appendChild(panel);

            function type(elId, text, speed, force = false) {{
                const el = document.getElementById(elId);
                const prevText = lastData[elId];
                
                // Si el texto es el mismo, no animar
                if (!force && prevText === text) {{
                    el.innerHTML = text;
                    return;
                }}

                let i = 0;
                function step() {{
                    if (i < text.length) {{
                        el.innerHTML = text.substring(0, i + 1) + '<span class="typing-cursor"></span>';
                        i++;
                        setTimeout(step, speed);
                    }} else {{
                        el.innerHTML = text;
                        lastData[elId] = text;
                        sessionStorage.setItem(storageKey, JSON.stringify(lastData));
                    }}
                }}
                step();
            }}

            // Solo animar si es el agente activo O si el texto ha cambiado
            const forceAnim = (isActive && lastData['turn'] !== state.turn);
            type('strat_' + teamKey, tel.strategy || "---", 25, forceAnim);
            setTimeout(() => type('reason_' + teamKey, tel.reasoning || "---", 15, forceAnim), 400);
        }}

        renderPanel('team_a', 'var(--accent-alpha)');
        renderPanel('team_b', 'var(--accent-beta)');
        lastData['turn'] = state.turn;
        sessionStorage.setItem(storageKey, JSON.stringify(lastData));
    </script>
    """
    components.html(html_content, height=230)
