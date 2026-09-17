"""Pruebas sin red de reglamento.py, memoria.py y citas.py.

Se corren con:  python -m pruebas.prueba_citas

No usan pytest ni tocan la red: sólo `assert`. Si una falla, el programa se
detiene ahí y dice cuál. Si todas pasan, imprime OK.
"""
from app.citas import aviso_citas_invalidas, extraer_citas, validar_citas
from app.memoria import agregar, recortar
from app.reglamento import RUTA_POR_OMISION, cargar_reglamento, indice_citas, texto_para_prompt

reglamento = cargar_reglamento(RUTA_POR_OMISION)
indice = indice_citas(reglamento)
texto = texto_para_prompt(reglamento)
lineas = texto.split("\n")

# --- El índice de citas -------------------------------------------------
# 22 artículos + 104 fracciones. Si este número cambia, algo se rompió al
# recorrer el JSON y la validación de citas dejaría de ser confiable.
assert len(indice) == 126, "el índice debe tener 126 claves, tiene %d" % len(indice)
assert "9" in indice
assert "9.II" in indice
assert "14.3" in indice, "los incisos 1 a 4 del artículo 14 también son claves"
assert "23" not in indice, "el Reglamento sólo llega al artículo 22"
assert "7.XXV" not in indice, "el artículo 7 tiene 23 fracciones, no llega a la XXV"

# --- El texto que se inserta en el prompt --------------------------------
assert lineas[0] == "REGLAMENTO DE ESTUDIANTES DEL TECNOLÓGICO NACIONAL DE MÉXICO"
assert "TÍTULO TERCERO. DE LAS SANCIONES" in lineas, "los títulos van en mayúsculas"
assert "Art. 9, fracc. I. Amonestación verbal o por escrito de la conducta o acto cometido;" in lineas
assert "Art. 9. Cualquier estudiante que incurra en las conductas prohibidas previstas en el presente Reglamento se hará acreedor, según corresponda, a las siguientes sanciones:" in lineas
assert any(l.startswith("Art. 9 (párrafo final).") for l in lineas), "falta el cierre del artículo 9"
assert "TRANSITORIOS" in lineas
assert any(l.startswith("PRIMERO.") for l in lineas)

# --- Extraer citas ------------------------------------------------------
assert extraer_citas("") == [], "un texto vacío no tiene citas"
assert extraer_citas("no consta en el Reglamento de Estudiantes") == []
assert extraer_citas("Art. 9, fracc. II") == ["9.II"]
assert extraer_citas("art. 9, fracc. ii") == ["9.II"], "el romano se guarda en mayúsculas"
assert extraer_citas("Artículo 9 fracción II") == ["9.II"], "sin coma y con la palabra completa"
assert extraer_citas("Art. 14, numeral 3") == ["14.3"], "el artículo 14 usa numerales"
assert extraer_citas("Art. 9, fracc. II; Art. 9, fracc. II") == ["9.II"], "sin repetir"
assert extraer_citas("Art. 15 y luego Art. 8") == ["15", "8"], "en orden de aparición"

# --- Validar citas ------------------------------------------------------
resultado = validar_citas(["9.II", "31.II", "15"], indice)
assert resultado["validas"] == ["9.II", "15"]
assert resultado["invalidas"] == ["31.II"], "el artículo 31 no existe"
assert validar_citas([], indice) == {"validas": [], "invalidas": []}
assert aviso_citas_invalidas([]) == "", "sin citas inválidas no hay aviso"
assert "31.II" in aviso_citas_invalidas(["31.II"]), "el aviso nombra la cita falsa"

# --- La memoria ---------------------------------------------------------
historial = []
agregar(historial, "usuario", "¿debo traer credencial?")
agregar(historial, "modelo", "Respuesta: ...")
assert historial == [{"rol": "usuario", "texto": "¿debo traer credencial?"},
                     {"rol": "modelo", "texto": "Respuesta: ..."}]
assert recortar(historial, 0) == [], "con 0 no se envía nada"
assert len(historial) == 2, "recortar NO modifica el historial original"
assert recortar(historial, 1) == [], "si el único mensaje es del modelo, se descarta"
assert len(recortar(historial, 5)) == 2, "si caben todos, se envían todos"
try:
    agregar(historial, "sistema", "x")
    assert False, "un rol inválido debe fallar"
except ValueError:
    pass

# ------------------------------------------------------------------------
# PENDIENTE (Parte E · sección 8.3 del documento)
#
# Aquí faltan dos bloques que la práctica pide explícitamente y que NO se
# pueden escribir antes de hacer la traza a mano, porque son justamente la
# respuesta que traza_manual.md pide predecir:
#
#   1. Los cuatro recortes de la traza E.1 (max_mensajes = 4, con la secuencia
#      u1, m1, u2, m2, u3, m3, u4, m4).
#   2. Los seis textos T1 a T6 de la traza E.2, con lo que devuelve
#      extraer_citas y qué queda inválido en cada uno.
#
# El orden correcto es: predecir a mano en traza_manual.md -> escribir aquí el
# assert con esa predicción -> correr. Si el assert falla, ya se encontró una
# diferencia real entre lo que uno creía y lo que hace el código, y eso es lo
# que la traza pide documentar.
# ------------------------------------------------------------------------

# Las tres funciones puras del bot (sección 12.3) se prueban aquí también,
# cuando exista app/bot.py: leer_permitidos, partir_mensaje y usuario_anonimo.

print("OK")
