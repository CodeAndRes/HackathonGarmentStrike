#!/usr/bin/env python3
"""
test_llm_fast.py
───────────────
Test rápido del LLM para verificar que Ollama responde.
"""
from core.llm_client import LLMClient

print("[*] Probando conexión a Ollama...")

try:
    client = LLMClient(model="ollama/llama3:latest", max_retries=1)
    
    # Test: Move decision (similar a lo que haría en una partida)
    print("\n[1] Test move decision:")
    agent_md = "Soy un agente estratégico. Disparo de izquierda a derecha."
    board_text = """    A  B  C  D  E  F  G  H  I  J
 1  ~  ~  ~  ~  ~  ~  ~  ~  ~  ~
 2  ~  ~  ~  ~  ~  ~  ~  ~  ~  ~"""
    
    test_move = client.get_move(
        agent_md=agent_md,
        opponent_board_text=board_text,
        move_history=[],
        my_name="Alpha",
        opponent_name="Beta"
    )
    print(f"    ✓ Respuesta generada!")
    print(f"    Coordenada: {test_move.coordenada}")
    print(f"    Razonamiento: {test_move.razonamiento[:60]}...")
    
except TimeoutError as e:
    print(f"    ✗ TIMEOUT: {e}")
    print("    → Ollama está en timeout. Verifica que está activo.")
except Exception as e:
    print(f"    ✗ ERROR: {type(e).__name__}: {e}")
