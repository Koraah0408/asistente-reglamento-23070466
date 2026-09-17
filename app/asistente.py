"""Une todas las piezas: una pregunta entra, una respuesta revisada sale.

El recorrido es siempre el mismo, y es el de la sección 4 del documento:

    agregar la pregunta al historial
    recortar el historial            -> sólo esos mensajes ve el modelo
    llamar al modelo                 -> una sola llamada, sin herramientas
    agregar la respuesta al historial
    extraer las citas y validarlas   -> si alguna no existe, se agrega un aviso
    escribir una línea en la bitácora

Tanto la terminal como el bot de Telegram usan este mismo `Asistente.responder`.
"""
import json
import os
import time
from datetime import datetime
from pathlib import Path

from app.citas import aviso_citas_invalidas, extraer_citas, validar_citas
from app.memoria import agregar, recortar
from app.reglamento import (
    RUTA_POR_OMISION,
    cargar_reglamento,
    indice_citas,
    texto_para_prompt,
)

RUTA_SISTEMA = "prompts/sistema.md"
MARCADOR = "{REGLAMENTO}"
MAX_MENSAJES_POR_OMISION = 6

AVISO_LEGAL = (
    "Este asistente es informativo y se basa sólo en el Reglamento de Estudiantes "
    "del TecNM. No es autoridad del plantel ni sustituye a Servicios Escolares."
)


def cargar_entorno():
    """Lee el .env si python-dotenv está instalado. Sin él, el programa igual corre."""
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    load_dotenv()


def construir_sistema(reglamento, ruta=RUTA_SISTEMA):
    """Sustituye {REGLAMENTO} en la plantilla por el texto completo del Reglamento."""
    plantilla = Path(ruta).read_text(encoding="utf-8")
    if MARCADOR not in plantilla:
        raise ValueError("%s no contiene el marcador %s" % (ruta, MARCADOR))
    return plantilla.replace(MARCADOR, texto_para_prompt(reglamento))


class Bitacora:
    """Escribe una línea JSON por turno en logs/corrida-AAAAMMDD-HHMMSS.jsonl."""

    def __init__(self, modo, carpeta="logs", corrida=None):
        self.modo = modo
        self.corrida = corrida or datetime.now().strftime("%Y%m%d-%H%M%S")
        carpeta = Path(carpeta)
        carpeta.mkdir(parents=True, exist_ok=True)
        self.ruta = carpeta / ("corrida-%s.jsonl" % self.corrida)

    def escribir(self, **campos):
        """Agrega un turno. `ts`, `corrida` y `modo` los pone la bitácora."""
        linea = {
            "ts": datetime.now().isoformat(timespec="seconds"),
            "corrida": self.corrida,
            "modo": self.modo,
        }
        linea.update(campos)
        # Se abre y se cierra en cada turno: si el programa se cae a media
        # corrida, lo escrito hasta ahí ya está en el disco.
        with open(self.ruta, "a", encoding="utf-8") as archivo:
            archivo.write(json.dumps(linea, ensure_ascii=False) + "\n")


class Asistente:
    """Una conversación: su historial, su memoria corta y su verificación de citas."""

    def __init__(self, llamar, sistema, indice, max_mensajes=MAX_MENSAJES_POR_OMISION, reglamento=None):
        self.llamar = llamar
        self.sistema = sistema
        self.indice = indice
        self.max_mensajes = max_mensajes
        self.reglamento = reglamento or {}
        self.historial = []

    def reset(self):
        """Borra la memoria de la conversación. El Reglamento y el prompt no cambian."""
        self.historial = []

    def fuente(self):
        """Qué documento se está consultando, para el comando /fuente."""
        return "\n".join(
            [
                "Documento: %s" % self.reglamento.get("documento", "(desconocido)"),
                "Aprobación: %s" % self.reglamento.get("aprobacion", "(desconocida)"),
                "Difusión: %s" % self.reglamento.get("difusion", "(desconocida)"),
                "Fuente: %s" % self.reglamento.get("fuente", "(desconocida)"),
                "Artículos y fracciones citables: %d" % len(self.indice),
                "Memoria corta: los últimos %d mensajes" % self.max_mensajes,
            ]
        )

    def responder(self, pregunta):
        """Contesta una pregunta y devuelve todo lo que hace falta para la bitácora.

        Si la llamada al modelo falla, la pregunta sin respuesta sale de la
        memoria y la excepción sube a quien llamó: la conversación no se queda
        con un turno a medias.
        """
        agregar(self.historial, "usuario", pregunta)
        enviados = recortar(self.historial, self.max_mensajes)

        inicio = time.time()
        try:
            salida = self.llamar(enviados, self.sistema)
        except Exception:
            self.historial.pop()
            raise
        segundos = round(time.time() - inicio, 2)

        texto = salida["texto"]
        # En la memoria queda lo que dijo el modelo, tal cual. El aviso es un
        # agregado del código para quien lee, no algo que el modelo haya escrito.
        agregar(self.historial, "modelo", texto)

        encontradas = extraer_citas(texto)
        revision = validar_citas(encontradas, self.indice)
        aviso = aviso_citas_invalidas(revision["invalidas"])
        texto_mostrado = texto + "\n\n" + aviso if aviso else texto

        return {
            "respuesta": texto_mostrado,
            "citas": revision["validas"],
            "citas_invalidas": revision["invalidas"],
            "no_consta": "no consta" in texto.lower(),
            "mensajes_enviados": len(enviados),
            "tokens_entrada": salida["tokens_entrada"],
            "tokens_salida": salida["tokens_salida"],
            "modelo": salida["modelo"],
            "segundos": segundos,
        }


def construir(simulado=False, ruta_reglamento=RUTA_POR_OMISION, ruta_sistema=RUTA_SISTEMA, max_mensajes=None):
    """Arma un Asistente listo para usar. Es el punto de entrada de cli, lote y bot."""
    cargar_entorno()
    reglamento = cargar_reglamento(ruta_reglamento)

    if max_mensajes is None:
        max_mensajes = int(os.environ.get("MAX_MENSAJES", str(MAX_MENSAJES_POR_OMISION)))

    if simulado:
        from app.modelo_simulado import ModeloSimulado

        llamar = ModeloSimulado()
    else:
        # Se importa aquí y no arriba a propósito: así el modo simulado funciona
        # aunque el SDK de Gemini no esté instalado todavía.
        from app.modelo import llamar_modelo

        llamar = llamar_modelo

    return Asistente(
        llamar=llamar,
        sistema=construir_sistema(reglamento, ruta_sistema),
        indice=indice_citas(reglamento),
        max_mensajes=max_mensajes,
        reglamento=reglamento,
    )
