"""Chat en la terminal.

    python -m app.cli              habla con Gemini (gasta cuota)
    python -m app.cli --simulado   habla con el modelo falso (no gasta nada)

Comandos: /fuente, /reset y /salir.
"""
import argparse
import sys

from app.asistente import AVISO_LEGAL, Asistente, Bitacora, construir


def usar_utf8():
    """La consola de Windows no siempre viene en UTF-8 y se come los acentos."""
    for flujo in (sys.stdout, sys.stderr):
        try:
            flujo.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass


def leer_argumentos(argumentos=None):
    analizador = argparse.ArgumentParser(description="Asistente del Reglamento de Estudiantes del TecNM")
    analizador.add_argument("--simulado", action="store_true",
                            help="usa el modelo simulado, sin red ni cuota")
    return analizador.parse_args(argumentos)


def main(argumentos=None):
    usar_utf8()
    opciones = leer_argumentos(argumentos)
    modo = "simulado" if opciones.simulado else "real"

    try:
        asistente = construir(simulado=opciones.simulado)
    except Exception as error:
        print("No se pudo iniciar el asistente: %s" % error)
        return 1

    bitacora = Bitacora(modo=modo)

    print("Asistente del Reglamento de Estudiantes del TecNM  [modo %s]" % modo)
    print(AVISO_LEGAL)
    print("Comandos: /fuente  /reset  /salir")
    print("Bitácora: %s" % bitacora.ruta)
    print()

    turno = 0
    while True:
        try:
            pregunta = input("Tú> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0

        if not pregunta:
            continue

        if pregunta == "/salir":
            return 0
        if pregunta == "/reset":
            asistente.reset()
            print("Listo: la memoria de esta conversación quedó vacía.\n")
            continue
        if pregunta == "/fuente":
            print(asistente.fuente())
            print()
            continue

        turno += 1
        try:
            resultado = asistente.responder(pregunta)
        except Exception as error:
            # Nunca un traceback en la cara del usuario. La pregunta ya salió de
            # la memoria dentro de `responder`, así que la conversación sigue
            # sana y se puede volver a preguntar.
            print("No se pudo responder ahora mismo: %s" % resumen_del_error(error))
            print("La pregunta no se guardó en la memoria; puede intentar de nuevo.\n")
            bitacora.escribir(id="CLI-%d" % turno, pregunta=pregunta, error=str(error))
            continue

        print()
        print(resultado["respuesta"])
        print()

        bitacora.escribir(id="CLI-%d" % turno, pregunta=pregunta, **resultado)


def resumen_del_error(error):
    """Traduce los errores más comunes a algo que se entienda sin leer código."""
    texto = str(error)
    if "GenerateRequestsPerDay" in texto:
        return "se acabó la cuota diaria de este modelo; hay que seguir mañana"
    if "RESOURCE_EXHAUSTED" in texto or "429" in texto:
        return "demasiadas peticiones por minuto; espere un momento y reintente"
    if "503" in texto or "UNAVAILABLE" in texto:
        return "el servidor del modelo está saturado; reintente más tarde"
    if "GEMINI_API_KEY" in texto:
        return texto
    if "getaddrinfo" in texto or "Connection" in texto or "Network" in texto:
        return "no hay conexión a internet"
    return texto


if __name__ == "__main__":
    sys.exit(main())
