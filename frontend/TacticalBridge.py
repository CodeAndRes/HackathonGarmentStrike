import streamlit as st
import streamlit.components.v1 as components
import json

def tactical_telemetry_bridge(game_state: dict):
    """Telemetría de Foco: Solo muestra el razonamiento del agente activo. El otro queda en Standby."""
    
    # Preparar el payload sin persistencia compleja (más robusto)
    tel = game_state.get("telemetry", {})
    active_key = game_state.get("turn_agent", "team_a")
    
    payload = {
        "turn": game_state.get("turn"),
        "active": active_key,
        "teams": {
            "team_a": {
                "name": game_state.get("team_a", {}).get("name", "ALPHA"),
                "strat": tel.get("team_a", {}).get("strategy", ""),
                "reason": tel.get("team_a", {}).get("reasoning", "")
            },
            "team_b": {
                "name": game_state.get("team_b", {}).get("name", "BETA"),
                "strat": tel.get("team_b", {}).get("strategy", ""),
                "reason": tel.get("team_b", {}).get("reasoning", "")
            }
        },
        "comms": game_state.get("comms", [])
    }

    html_content = f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=JetBrains+Mono:wght@400;700&display=swap');
        :root {{ --accent-alpha: #00ff88; --accent-beta: #ff4b4b; }}
        body {{ margin: 0; padding: 0; background: transparent; overflow: hidden; color: #fff; font-family: 'JetBrains Mono', monospace; }}
        .telemetry-container {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
        .panel {{ background: rgba(13, 17, 23, 0.95); border-radius: 12px; padding: 18px; transition: all 0.4s ease; min-height: 220px; max-height: 280px; display: flex; flex-direction: column; overflow: hidden; border: 1px solid rgba(255,255,255,0.05); }}
        .header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; border-bottom: 1px solid rgba(255,255,255,0.08); padding-bottom: 8px; font-family: 'Orbitron'; font-size: 0.85rem; font-weight: 700; }}
        .label {{ color: rgba(255,255,255,0.3); font-size: 0.6rem; letter-spacing: 1px; margin-bottom: 4px; font-family: 'Orbitron'; }}
        .content {{ color: #fff; font-size: 0.8rem; line-height: 1.4; margin-bottom: 12px; }}
        .standby {{ color: rgba(255,255,255,0.15); font-style: italic; font-size: 0.75rem; }}
        .action-box {{ background: rgba(255,255,255,0.03); padding: 8px 12px; border-radius: 6px; display: flex; justify-content: space-between; align-items: center; font-size: 0.75rem; margin-top: auto; }}
        .typing-cursor {{ border-right: 2px solid currentColor; animation: blink 0.7s infinite; margin-left: 2px; }}
        @keyframes blink {{ 0%, 100% {{ opacity: 1; }} 50% {{ opacity: 0; }} }}
        .active-badge {{ font-size: 0.5rem; padding: 2px 6px; border-radius: 3px; background: currentColor; color: #000; font-weight: 900; letter-spacing: 1px; }}
    </style>
    <div class="telemetry-container" id="main-container"></div>
    <script>
        const data = {json.dumps(payload)};
        const container = document.getElementById('main-container');

        function renderPanel(teamKey, color) {{
            const team = data.teams[teamKey];
            const isActive = (data.active === teamKey);
            
            // Buscar último movimiento
            let lastMove = "---";
            const agentId = teamKey === "team_a" ? "A" : "B";
            for (let i = data.comms.length - 1; i >= 0; i--) {{
                if (data.comms[i].agent === agentId) {{
                    lastMove = data.comms[i].coord + " " + data.comms[i].icon + " (" + data.comms[i].result + ")";
                    break;
                }}
            }}

            const panel = document.createElement('div');
            panel.className = 'panel';
            panel.style.opacity = isActive ? '1' : '0.4';
            panel.style.border = isActive ? '2px solid ' + color : '1px solid rgba(255,255,255,0.05)';
            if (isActive) panel.style.boxShadow = '0 0 20px ' + color + '33';

            panel.innerHTML = `
                <div class="header" style="color: ${{color}}">
                    <span>STRATEGY | ${{team.name}}</span>
                    ${{isActive ? `<span class="active-badge" style="background:${{color}}">BRAIN ACTIVE</span>` : ''}}
                </div>
                <div>
                    <div class="label">OBJECTIVE:</div>
                    <div class="content" id="strat_${{teamKey}}"></div>
                </div>
                <div>
                    <div class="label">ANALYSIS:</div>
                    <div class="content" id="reason_${{teamKey}}"></div>
                </div>
                <div class="action-box">
                    <div class="label" style="margin:0">LAST ACTION:</div>
                    <div style="color:${{color}}; font-family:Orbitron; font-weight:900; font-size:0.7rem;">${{lastMove}}</div>
                </div>
            `;
            container.appendChild(panel);

            if (isActive) {{
                const sText = team.strat || "Stabilizing strategy...";
                const rText = team.reason || "Analyzing board vulnerabilities...";
                
                function type(elId, text, speed) {{
                    const el = document.getElementById(elId);
                    let i = 0;
                    function step() {{
                        if (i < text.length) {{
                            el.innerHTML = text.substring(0, i + 1) + '<span class="typing-cursor"></span>';
                            i++;
                            setTimeout(step, speed);
                        }} else {{
                            el.innerHTML = text;
                        }}
                    }}
                    step();
                }}
                type('strat_' + teamKey, sText, 25);
                setTimeout(() => type('reason_' + teamKey, rText, 15), 500);
            }} else {{
                document.getElementById('strat_' + teamKey).innerHTML = '<span class="standby">SYSTEM IN STANDBY...</span>';
                document.getElementById('reason_' + teamKey).innerHTML = '<span class="standby">Awaiting telemetry from agent...</span>';
            }}
        }}

        renderPanel('team_a', 'var(--accent-alpha)');
        renderPanel('team_b', 'var(--accent-beta)');
    </script>
    """
    components.html(html_content, height=320)
