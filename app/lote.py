"""Corre el banco de pruebas y deja una bitácora con los resultados.

    python -m app.lote data/preguntas_prueba.json --simulado
    python -m app.lote data/preguntas_prueba.json --solo R01,R02,R03
    python -m app.lote data/preguntas_prueba.json --solo C1,C2

El banco son 12 preguntas sueltas y 2 conversaciones de 3 turnos: 18 llamadas.
Con la capa gratuita de Gemini eso es casi toda la cuota del día, así que la
corrida real conviene repartirla en dos días con --solo.

Cada pregunta suelta empieza con la memoria vacía. Dentro de una conversación,
en cambio, la memoria se comparte: por eso el turno 2 puede decir "¿y cuál es la
más grave?" y entenderse.
"""
import argparse
import json
import sys
import time
from pathlib import Path

from app.asistente import Bitacora, construir
from app.cli import resumen_del_error, usar_utf8

SEGUNDOS_ENTRE_LLAMADAS_REALES = 4


def leer_argumentos(argumentos=None):
    analizador = argparse.ArgumentParser(description="Banco de pruebas del asistente del Reglamento")
    analizador.add_argument("banco", help="ruta de data/preguntas_prueba.json")
    analizador.add_argument("--simulado", action="store_true",
                            help="usa el modelo simulado, sin red ni cuota")
    analizador.add_argument("--solo", default="",
                            help="identificadores separados por comas: R05, C1 (la conversación "
                                 "completa) o C1-2 (un solo turno)")
    return analizador.parse_args(argumentos)


def seleccionados(texto):
    """Convierte "R05, C1" en el conjunto {"R05", "C1"}. Vacío = todo el banco."""
    return {parte.strip().upper() for parte in texto.split(",") if parte.strip()}


def pedida(identificador, filtro):
    """¿Hay que correr este turno? Sin filtro, sí. Con filtro, C1 incluye C1-1, C1-2 y C1-3."""
    if not filtro:
        return True
    if identificador in filtro:
        return True
    return identificador.split("-")[0] in filtro


def imprimir_turno(identificador, pregunta, resultado):
    print("[%s] %s" % (identificador, pregunta))
    print("      citas=%s  inválidas=%s  no_consta=%s  enviados=%d  tokens=%d/%d  %.2fs" % (
        resultado["citas"] or "-",
        resultado["citas_invalidas"] or "-",
        "sí" if resultado["no_consta"] else "no",
        resultado["mensajes_enviados"],
        resultado["tokens_entrada"],
        resultado["tokens_salida"],
        resultado["segundos"],
    ))


def main(argumentos=None):
    usar_utf8()
    opciones = leer_argumentos(argumentos)
    modo = "simulado" if opciones.simulado else "real"
    filtro = seleccionados(opciones.solo)

    banco = json.loads(Path(opciones.banco).read_text(encoding="utf-8"))
    bitacora = Bitacora(modo=modo)

    print("Banco: %s  [modo %s]" % (opciones.banco, modo))
    print("Bitácora: %s" % bitacora.ruta)
    if filtro:
        print("Sólo: %s" % ", ".join(sorted(filtro)))
    print()

    asistente = construir(simulado=opciones.simulado)
    primera = True
    hechos = fallados = 0

    def esperar():
        """Un respiro entre llamadas reales, para no chocar con el límite por minuto."""
        nonlocal primera
        if not primera and not opciones.simulado:
            time.sleep(SEGUNDOS_ENTRE_LLAMADAS_REALES)
        primera = False

    # --- Las 12 preguntas sueltas: cada una con la memoria vacía -------------
    for entrada in banco["preguntas"]:
        if not pedida(entrada["id"], filtro):
            continue
        asistente.reset()
        esperar()
        try:
            resultado = asistente.responder(entrada["pregunta"])
        except Exception as error:
            # Un turno que falla no detiene el lote: se anota y se sigue con el
            # siguiente. Después se repite lo que faltó con --solo.
            print("[%s] ERROR: %s" % (entrada["id"], resumen_del_error(error)))
            bitacora.escribir(id=entrada["id"], pregunta=entrada["pregunta"], error=str(error))
            fallados += 1
            continue
        imprimir_turno(entrada["id"], entrada["pregunta"], resultado)
        bitacora.escribir(id=entrada["id"], pregunta=entrada["pregunta"], **resultado)
        hechos += 1

    # --- Las 2 conversaciones: la memoria se comparte entre sus turnos -------
    for conversacion in banco["conversaciones"]:
        if not any(pedida("%s-%d" % (conversacion["id"], n), filtro)
                   for n in range(1, len(conversacion["turnos"]) + 1)):
            continue
        asistente.reset()
        for numero, pregunta in enumerate(conversacion["turnos"], start=1):
            identificador = "%s-%d" % (conversacion["id"], numero)
            if not pedida(identificador, filtro):
                continue
            esperar()
            try:
                resultado = asistente.responder(pregunta)
            except Exception as error:
                # Si se cae un turno, los siguientes de ESTA conversación se
                # omiten: sin el turno anterior en la memoria, el de después ya
                # no probaría lo que debía probar.
                print("[%s] ERROR: %s" % (identificador, resumen_del_error(error)))
                print("      se omite el resto de la conversación %s" % conversacion["id"])
                bitacora.escribir(id=identificador, pregunta=pregunta, error=str(error))
                fallados += 1
                break
            imprimir_turno(identificador, pregunta, resultado)
            bitacora.escribir(id=identificador, pregunta=pregunta, **resultado)
            hechos += 1

    print()
    print("Turnos con respuesta: %d   con error: %d" % (hechos, fallados))
    print("Bitácora: %s" % bitacora.ruta)
    return 0


if __name__ == "__main__":
    sys.exit(main())
