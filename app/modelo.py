"""La única función del programa que habla con Gemini.

Todo lo demás (memoria, citas, bitácora, chat, lote, bot) no sabe qué proveedor
hay detrás: sólo conoce la firma de `llamar_modelo` y el diccionario que
devuelve. Si mañana el curso cambiara de proveedor, este archivo sería el único
que habría que reescribir, y por eso es el único que importa el SDK.
"""
import os

from google import genai
from google.genai import types

# "usuario"/"modelo" son los roles de nuestro historial; el SDK usa otros.
ROLES_DEL_SDK = {"usuario": "user", "modelo": "model"}

MODELO_POR_OMISION = "gemini-3.5-flash"

_cliente = None


def _obtener_cliente():
    """Crea el cliente una sola vez y lo reutiliza en las llamadas siguientes."""
    global _cliente
    if _cliente is None:
        clave = os.environ.get("GEMINI_API_KEY", "").strip()
        if not clave:
            raise RuntimeError(
                "Falta GEMINI_API_KEY. Copie .env.example a .env y escriba su clave, "
                "o corra el programa con --simulado."
            )
        _cliente = genai.Client(
            api_key=clave,
            # Ante un 503 (servidor saturado) o un 429 por límite POR MINUTO, el
            # SDK reintenta solo, esperando cada vez más. Un 429 que dice
            # GenerateRequestsPerDay es la cuota del día: ése no se arregla
            # esperando, hay que seguir al día siguiente.
            http_options=types.HttpOptions(
                retry_options=types.HttpRetryOptions(attempts=5, initial_delay=2.0, max_delay=30.0)
            ),
        )
    return _cliente


def llamar_modelo(historial, sistema):
    """Manda al modelo el historial YA recortado y las instrucciones de sistema.

    `historial` es la lista de mensajes {"rol", "texto"} que devolvió
    `memoria.recortar`; `sistema` es el texto de prompts/sistema.md con el
    Reglamento ya sustituido.

    Devuelve {"texto", "tokens_entrada", "tokens_salida", "modelo"}.
    """
    cliente = _obtener_cliente()
    nombre_del_modelo = os.environ.get("GEMINI_MODEL", MODELO_POR_OMISION)

    contenidos = [
        types.Content(role=ROLES_DEL_SDK[mensaje["rol"]], parts=[types.Part(text=mensaje["texto"])])
        for mensaje in historial
    ]

    respuesta = cliente.models.generate_content(
        model=nombre_del_modelo,
        contents=contenidos,
        config=types.GenerateContentConfig(system_instruction=sistema),
    )

    uso = respuesta.usage_metadata
    tokens_entrada = (uso.prompt_token_count or 0) if uso else 0
    # Los modelos actuales "piensan" antes de responder y esos tokens también se
    # cobran contra la cuota, así que se suman a los de salida.
    tokens_salida = ((uso.candidates_token_count or 0) + (uso.thoughts_token_count or 0)) if uso else 0

    return {
        "texto": respuesta.text or "",
        "tokens_entrada": tokens_entrada,
        "tokens_salida": tokens_salida,
        "modelo": nombre_del_modelo,
    }
