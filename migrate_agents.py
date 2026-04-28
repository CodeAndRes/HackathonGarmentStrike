import os
from pathlib import Path
import shutil

def migrate():
    source_dir = Path("agentes")
    target_dir = Path("torneo")
    target_dir.mkdir(exist_ok=True)
    
    print(f"Migrando de {source_dir} a {target_dir}...")
    
    for agent_folder in source_dir.iterdir():
        if not agent_folder.is_dir():
            continue
            
        agent_name = agent_folder.name
        strategy_file = agent_folder / "agent.md"
        # Find any almacen file
        almacen_files = list(agent_folder.glob("almacen*.md"))
        
        if strategy_file.exists():
            new_strategy = target_dir / f"{agent_name}.md"
            shutil.copy2(strategy_file, new_strategy)
            print(f"  {agent_name}.md OK")
            
        if almacen_files:
            # Take the first one found
            new_almacen = target_dir / f"{agent_name}.almacen.md"
            shutil.copy2(almacen_files[0], new_almacen)
            print(f"  {agent_name}.almacen.md OK")

if __name__ == "__main__":
    migrate()
