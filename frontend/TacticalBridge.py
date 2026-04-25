import streamlit as st
import streamlit.components.v1 as components
import json

def tactical_telemetry_bridge(game_state: dict):
    """Telemetría Pro 7.1: Estabilidad Total y Polling Ultra-Rápido."""
    
    html_content = f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=JetBrains+Mono:wght@400;700&display=swap');
        :root {{ --accent-alpha: #00ff88; --accent-beta: #ff4b4b; }}
        body {{ margin: 0; padding: 0; background: transparent; overflow: hidden; color: #fff; font-family: 'JetBrains Mono', monospace; }}
        .telemetry-container {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
        
        .panel {{ 
            background: rgba(10, 12, 16, 0.98); border-radius: 4px; padding: 20px; 
            transition: all 0.2s ease; min-height: 250px; max-height: 310px; 
            display: flex; flex-direction: column; border: 1px solid rgba(255,255,255,0.1);
            opacity: 0.2; transform: scale(0.98);
        }}
        .panel.active {{ opacity: 1; transform: scale(1); border-color: rgba(255,255,255,0.4); box-shadow: 0 0 40px rgba(0,0,0,0.8); }}

        .header {{ 
            display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; 
            border-bottom: 2px solid currentColor; padding-bottom: 10px; font-family: 'Orbitron'; 
            font-size: 0.9rem; font-weight: 900;
        }}
        .active-badge {{ 
            font-size: 0.55rem; padding: 3px 10px; border-radius: 2px; 
            background: currentColor; color: #000 !important; font-weight: 900; 
            box-shadow: 0 0 15px currentColor; display: none;
        }}
        .panel.active .active-badge {{ display: inline-block; animation: blink 0.8s infinite; }}
        @keyframes blink {{ 0%, 100% {{ opacity: 1; }} 50% {{ opacity: 0.5; }} }}

        .label {{ color: rgba(255,255,255,0.4); font-size: 0.65rem; letter-spacing: 1px; margin-bottom: 5px; font-family: 'Orbitron'; }}
        .content {{ color: #fff; font-size: 0.85rem; line-height: 1.4; margin-bottom: 12px; min-height: 1.4em; }}
        
        .action-box {{ 
            background: rgba(255,255,255,0.05); padding: 12px 15px; border-radius: 4px; 
            display: flex; justify-content: space-between; align-items: center; 
            margin-top: auto; border: 1px solid rgba(255,255,255,0.1); transition: all 0.3s ease;
            box-shadow: inset 0 0 10px rgba(0,0,0,0.5);
        }}
        
        .coord-display {{ font-family: 'Orbitron'; font-weight: 900; font-size: 1.2rem; }}
        .result-display {{ font-family: 'Orbitron'; font-weight: 700; font-size: 0.8rem; letter-spacing: 1px; }}
    </style>
    <div class="telemetry-container" id="main-container"></div>
    <script>
        const container = document.getElementById('main-container');
        let currentLayoutKey = "";

        function createLayout(state) {{
            const key = state.turn_agent + "_" + state.turn;
            if (currentLayoutKey === key) return;
            container.innerHTML = '';
            ['team_a', 'team_b'].forEach(tk => {{
                const color = tk === 'team_a' ? 'var(--accent-alpha)' : 'var(--accent-beta)';
                const isActive = (state.turn_agent === tk);
                const panel = document.createElement('div');
                panel.id = 'panel_' + tk;
                panel.className = 'panel' + (isActive ? ' active' : '');
                panel.style.color = color;
                panel.innerHTML = `
                    <div class="header">
                        <span>DATA LINK | ${{state[tk].name}}</span>
                        <span class="active-badge">BRAIN ACTIVE</span>
                    </div>
                    <div><div class="label">OBJETIVO:</div><div class="content" id="strat_${{tk}}"></div></div>
                    <div><div class="label">ANALISIS:</div><div class="content" id="reason_${{tk}}"></div></div>
                    <div class="action-box" id="box_${{tk}}" style="opacity:0">
                        <div class="label" style="margin:0;">RESULTADO:</div>
                        <div style="display:flex; align-items:center; gap:12px;">
                            <span class="coord-display" id="coord_${{tk}}">--</span>
                            <span class="result-display" id="info_${{tk}}">...</span>
                        </div>
                    </div>
                `;
                container.appendChild(panel);
            }});
            currentLayoutKey = key;
        }}

        function updateUI(state) {{
            if (!state || state.error) return;
            createLayout(state);
            const activeTeam = state.turn_agent;
            const telData = state.telemetry || {{}};

            ['team_a', 'team_b'].forEach(tk => {{
                const isActive = (activeTeam === tk);
                const teamTel = telData[tk] || {{}};
                const p = document.getElementById('panel_' + tk);
                if (p) p.className = 'panel' + (isActive ? ' active' : '');

                const stratEl = document.getElementById('strat_' + tk);
                const reasonEl = document.getElementById('reason_' + tk);
                const boxEl = document.getElementById('box_' + tk);

                if (isActive) {{
                    if (teamTel.cursor === 'focus') {{
                        stratEl.innerHTML = "";
                        reasonEl.innerHTML = "";
                        boxEl.style.opacity = "0";
                    }} else {{
                        stratEl.innerHTML = teamTel.strategy || "";
                        reasonEl.innerHTML = teamTel.reasoning || "";
                        const showResult = !(['focus', 'strategy', 'reasoning'].includes(teamTel.cursor));
                        boxEl.style.opacity = showResult ? "1" : "0";
                    }}
                }} else {{
                    boxEl.style.opacity = "1";
                }}

                const agentId = tk === 'team_a' ? 'A' : 'B';
                const lastMove = state.comms.filter(m => m.agent === agentId).pop();
                if (lastMove) {{
                    document.getElementById('coord_' + tk).innerText = lastMove.coord;
                    document.getElementById('info_' + tk).innerText = (lastMove.icon || "") + " " + lastMove.result.toUpperCase();
                }}
            }});
        }}

        async function pollState() {{
            try {{
                const response = await fetch('http://' + (window.location.hostname || '127.0.0.1') + ':8000/api/state');
                if (!response.ok) return;
                const state = await response.json();
                updateUI(state);
            }} catch (e) {{ }}
        }}

        setInterval(pollState, 50); // Polling ultra-rápido (20 veces por segundo)
        pollState();
    </script>
    """
    components.html(html_content, height=400)
