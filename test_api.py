# test_api.py
import os
from litellm import completion

# ==============================================
# 1. Configura tu API Key (elige UN método)
# ==============================================

# Opción A (recomendada): Usa un archivo .env
# Crea un archivo .env en la misma carpeta con:
# OPENAI_API_KEY=tu_clave_aqui
# Luego descomenta estas dos líneas:
from dotenv import load_dotenv
load_dotenv()

# Opción B (manual): Escribe tu clave directamente aquí (solo para prueba)
# os.environ["OPENAI_API_KEY"] = "tu_clave_aqui"

# ==============================================
# 2. Prueba la llamada a la API
# ==============================================

try:
    response = completion(
        model="gemini/gemini-2.5-flash",  # Puedes cambiar a "gemini/gemini-1.5-flash" si usas Gemini
        messages=[{"role": "user", "content": "Responde SOLO con la palabra: OK"}],
        temperature=0.0,
        max_tokens=5
    )
    print("✅ Respuesta de la API:", response.choices[0].message.content)
    print("✅ Conexión exitosa. Tu API Key funciona.")
except Exception as e:
    print("❌ Error:", e)
    print("❌ No se pudo conectar. Revisa tu API Key y el modelo.")