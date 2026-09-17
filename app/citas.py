"""Citas: extraerlas de una respuesta y comprobar que existen.

Ésta es la parte que sostiene la regla de oro de la práctica. Las instrucciones
de sistema *piden* al modelo que cite con un formato exacto y que no invente
artículos, pero pedirlo no garantiza nada: una respuesta fluida con un artículo
inventado es la peor respuesta posible, porque un estudiante le creería.

Lo que garantiza que no pase es este módulo, que revisa cada cita contra el
índice del Reglamento y avisa cuando una es falsa.
"""
import re

# Reconoce las tres formas de la sección 8.1 del documento, sin importar
# mayúsculas ni acentos en "articulo":
#
#   Art. 9 / Artículo 9 / art 9 / artículos 9      -> "9"
#   Art. 9, fracc. II / Artículo 9 fracción II     -> "9.II"
#   Art. 14, numeral 3 / art. 14 numeral 3         -> "14.3"
#
# La parte de la fracción es opcional; la coma entre el número y "fracc"
# también, porque el modelo no siempre escribe igual.
_PATRON_CITA = re.compile(
    r"\bart(?:[íi]culo)?s?\.?\s*(\d{1,3})"
    r"(?:\s*[,;]?\s*(?:fracc\w*|numeral\w*)\.?\s*([IVXLCDM]+|\d{1,2})\b)?",
    re.IGNORECASE,
)

AVISO = "[Aviso] Estas citas no existen en el Reglamento: %s"


def extraer_citas(texto):
    """Devuelve las citas de un texto, en orden de aparición y sin repetir.

    Las claves tienen el mismo formato que el índice: "9" para un artículo y
    "9.II" o "14.3" para una fracción. El número romano se guarda siempre en
    mayúsculas, aunque el modelo lo haya escrito en minúsculas.
    """
    citas = []
    for numero, detalle in _PATRON_CITA.findall(texto or ""):
        clave = "%s.%s" % (numero, detalle.upper()) if detalle else numero
        if clave not in citas:
            citas.append(clave)
    return citas


def validar_citas(citas, indice):
    """Separa las citas en las que existen en el Reglamento y las que no."""
    return {
        "validas": [cita for cita in citas if cita in indice],
        "invalidas": [cita for cita in citas if cita not in indice],
    }


def aviso_citas_invalidas(invalidas):
    """Texto del aviso que el código agrega a la respuesta, o "" si no hace falta.

    La respuesta del modelo no se oculta ni se corrige: se muestra tal cual con
    el aviso pegado, para que quien lee sepa exactamente qué no se pudo
    comprobar.
    """
    if not invalidas:
        return ""
    return AVISO % ", ".join(invalidas)
