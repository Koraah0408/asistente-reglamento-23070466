"""El Reglamento: cargarlo, volverlo texto de prompt y saber qué citas existen.

Este módulo no sabe nada del modelo de lenguaje. Sólo hace dos cosas con el
JSON del docente: producir el texto que se inserta en las instrucciones de
sistema, y producir el conjunto de citas que existen de verdad, contra el que
`app.citas` valida lo que responde el modelo.
"""
import json
from pathlib import Path

RUTA_POR_OMISION = "data/reglamento_estudiantes_tecnm.json"


def cargar_reglamento(ruta=RUTA_POR_OMISION):
    """Lee el JSON del Reglamento y lo devuelve como diccionario.

    Se lee siempre en UTF-8: el texto trae acentos y el original conserva la
    ortografía del documento oficial.
    """
    return json.loads(Path(ruta).read_text(encoding="utf-8"))


def texto_para_prompt(reglamento):
    """Devuelve el Reglamento como texto plano, una línea por cita posible.

    El formato de cada línea es el mismo formato con el que el modelo debe
    citar (`Art. N.` / `Art. N, fracc. R.`). La idea es que el modelo copie la
    cita de la misma línea donde leyó el dato, en vez de reconstruirla de
    memoria: así inventar una cita es mucho menos probable.
    """
    lineas = [reglamento["documento"].upper()]
    titulo_anterior = None

    for articulo in reglamento["articulos"]:
        # El título sólo se imprime cuando cambia, en mayúsculas.
        if articulo["titulo"] != titulo_anterior:
            titulo_anterior = articulo["titulo"]
            lineas.append("")
            lineas.append(titulo_anterior.upper())

        numero = articulo["numero"]
        lineas.append("Art. %s. %s" % (numero, articulo["encabezado"]))

        # `fracciones` sólo existe en los artículos que la tienen. El artículo
        # 14 numera sus incisos con "1" a "4" en vez de números romanos; aquí
        # da igual, porque se usa el id tal como viene en el JSON.
        for fraccion in articulo.get("fracciones", []):
            lineas.append("Art. %s, fracc. %s. %s" % (numero, fraccion["id"], fraccion["texto"]))

        # `cierre` es el párrafo que va después de las fracciones.
        if "cierre" in articulo:
            lineas.append("Art. %s (párrafo final). %s" % (numero, articulo["cierre"]))

    lineas.append("")
    lineas.append("TRANSITORIOS")
    for transitorio in reglamento["transitorios"]:
        lineas.append("%s. %s" % (transitorio["id"], transitorio["texto"]))

    return "\n".join(lineas)


def indice_citas(reglamento):
    """Devuelve el conjunto de citas que existen: "9" por artículo, "9.II" por fracción.

    Con el Reglamento completo son 22 + 104 = 126 claves. Los transitorios no
    entran: no se citan como artículo.
    """
    indice = set()
    for articulo in reglamento["articulos"]:
        numero = str(articulo["numero"])
        indice.add(numero)
        for fraccion in articulo.get("fracciones", []):
            indice.add("%s.%s" % (numero, fraccion["id"]))
    return indice
