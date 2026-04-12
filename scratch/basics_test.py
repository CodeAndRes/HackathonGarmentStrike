import litellm
import json
import os
from dotenv import load_dotenv

load_dotenv() # Carga tu GEMINI_API_KEY desde el .env

# Configuracion del modelo
MODELO = os.getenv("DEFAULT_MODEL", "gemini/gemini-3-flash-preview")

# 1. REGLAS BASICAS (Se envian como SYSTEM PROMPT para que no se "olviden")
SYSTEM_PROMPT = """
Eres un estratega en 'Garment Strike'. 
- Tablero: 10x10 (A-J, 1-10).
- Objetivo: Hundir 5 cajas (5, 4, 3, 3, 2 celdas).
- Si aciertas, repites turno.
- Tu respuesta DEBE ser exclusivamente un JSON: {"coord": "B5", "razon": "..."}
"""

def test_move(manifesto, historial_tablero):
    print(f"\n[Pensando...] Enviando jugada a {MODELO}...")
    
    # Construimos el mensaje de usuario con lo minimo necesario
    user_content = f"""
    ESTRATEGIA DEL EQUIPO:
    {manifesto}

    ESTADO ACTUAL DEL TABLERO:
    {historial_tablero}

    ¿Cuál es tu siguiente movimiento?
    """

    try:
        response = litellm.completion(
            model=MODELO,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content}
            ],
            temperature=0.2 # Baja temperatura = mas precision, menos "creatividad"
        )
        
        raw_res = response.choices[0].message.content
        print(f"\n--- RESPUESTA DEL LLM ---")
        print(raw_res)
        print(f"--------------------------")
        
    except Exception as e:
        print(f"Error en la comunicacion: {e}")

# --- SIMULACION DE PRUEBA ---
mi_manifesto_corto = "Dispara en forma de X empezando por las esquinas. Si aciertas, busca arriba."
tablero_ficticio = "Fila 1: O O ~ ~ | Fila 2: ~ X ~ ~ (X=Acierto, O=Agua, ~=Desconocido)"

test_move(mi_manifesto_corto, tablero_ficticio)
