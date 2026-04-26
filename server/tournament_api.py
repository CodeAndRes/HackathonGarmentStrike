from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from core.bracket_engine import BracketEngine
from core.llm_client import LLMClient
import os
import yaml
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Garment Strike Tournament API")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = BracketEngine()
# Try to load existing state
engine.load_state()

# Auto-setup if no state exists to show something to the user immediately
if not engine.matches:
    print("No bracket state found. Auto-initializing with random agents...")
    engine.setup_tournament()

def get_settings():
    path = Path("settings.yaml")
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f).get("engine", {})
    return {}

@app.get("/bracket")
def get_bracket():
    engine.load_state() # Refresh from disk
    return engine.matches

@app.post("/setup")
def setup_tournament():
    engine.setup_tournament()
    return {"status": "Tournament setup complete", "matches": engine.matches}

@app.post("/run/{match_id}")
def run_match_task(match_id: str, background_tasks: BackgroundTasks):
    engine.load_state()
    match = engine.matches.get(match_id)
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    if match.status == "finished":
        raise HTTPException(status_code=400, detail="Match already finished")
    if match.status == "running":
        raise HTTPException(status_code=400, detail="Match already running")
    
    settings = get_settings()
    model = os.getenv("DEFAULT_MODEL", "gemini/gemini-1.5-flash")
    
    client = LLMClient(
        model=model,
        temperature=float(settings.get("temperature", 0.7)),
        max_tokens=int(settings.get("max_tokens", 150))
    )
    
    # We pass the engine method to background tasks
    background_tasks.add_task(engine.run_bracket_match, match_id, client)
    return {"status": f"Match {match_id} started"}

from fastapi.responses import HTMLResponse

@app.get("/", response_class=HTMLResponse)
def get_index():
    html_path = Path("frontend/tournament.html")
    if html_path.exists():
        return html_path.read_text(encoding="utf-8")
    return "<h1>Frontend not found</h1>"

@app.get("/reset")
def reset_tournament():
    if os.path.exists("logs/bracket_state.json"):
        os.remove("logs/bracket_state.json")
    engine.matches = {}
    return {"status": "Tournament reset"}

# Mount static files for the frontend if needed
# app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
