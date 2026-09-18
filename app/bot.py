"""El bot de Telegram: segundo canal, cero lógica propia.

    python -m app.bot --simulado    para desarrollar, sin gastar cuota
    python -m app.bot               con el modelo real

Este archivo no arma prompts, no extrae citas y no recorta memoria: recibe el
texto, se lo pasa al mismo `Asistente.responder` que usa la terminal, escribe la
bitácora y devuelve la respuesta. Si mañana se cambiara Telegram por WhatsApp o
por una página web, éste sería el único archivo que habría que reescribir.
"""
import argparse
import asyncio
import hashlib
import logging
import os
import sys

from app.asistente import AVISO_LEGAL, Bitacora, cargar_entorno, construir
from app.cli import resumen_del_error, usar_utf8

LIMITE_DE_TELEGRAM = 4096

AVISO_DE_PRIVACIDAD = (
    "Aviso de privacidad: sus mensajes pasan por Telegram y por Google para poder "
    "responderse. No escriba datos personales, ni suyos ni de nadie más: ni nombres "
    "completos, ni números de control, ni domicilios."
)


# --------------------------------------------------------------------------
# Funciones puras: sin red, sin Telegram. Se prueban en pruebas/prueba_citas.py
# --------------------------------------------------------------------------

def leer_permitidos(texto):
    """Convierte "123, 456" en {123, 456}.

    Lo que no sea un número se ignora. Con la lista vacía el bot no atiende a
    nadie, y eso es a propósito: un bot abierto se lo encuentra cualquiera por
    su nombre y le gastaría la cuota del día.
    """
    permitidos = set()
    for parte in (texto or "").replace(";", ",").split(","):
        parte = parte.strip()
        if parte.lstrip("-").isdigit():
            permitidos.add(int(parte))
    return permitidos


def partir_mensaje(texto, limite=LIMITE_DE_TELEGRAM):
    """Parte un texto en trozos que Telegram acepte, de preferencia en un salto de línea."""
    if limite <= 0:
        raise ValueError("el límite debe ser mayor que cero")
    if len(texto) <= limite:
        return [texto]

    partes = []
    resto = texto
    while len(resto) > limite:
        # Se busca el último salto de línea que quepa; si no hay, el último
        # espacio; si tampoco, se corta a la mala justo en el límite.
        corte = resto.rfind("\n", 0, limite + 1)
        if corte <= 0:
            corte = resto.rfind(" ", 0, limite + 1)
        if corte <= 0:
            corte = limite
        partes.append(resto[:corte].rstrip())
        resto = resto[corte:].lstrip("\n")
    if resto:
        partes.append(resto)
    return partes


def usuario_anonimo(user_id):
    """Los primeros 10 caracteres del SHA-256 del identificador.

    En la bitácora nunca se guarda el identificador real ni el nombre: alcanza
    con poder distinguir a dos personas sin saber quiénes son.
    """
    return hashlib.sha256(str(user_id).encode()).hexdigest()[:10]


# --------------------------------------------------------------------------
# El bot
# --------------------------------------------------------------------------

def leer_argumentos(argumentos=None):
    analizador = argparse.ArgumentParser(description="Bot de Telegram del asistente del Reglamento")
    analizador.add_argument("--simulado", action="store_true",
                            help="usa el modelo simulado, sin red ni cuota de Gemini")
    return analizador.parse_args(argumentos)


def main(argumentos=None):
    usar_utf8()
    opciones = leer_argumentos(argumentos)
    cargar_entorno()

    try:
        from telegram.constants import ChatAction
        from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
    except ImportError:
        print("Falta python-telegram-bot. Instale con: pip install -r requirements.txt")
        return 1

    logging.basicConfig(level=logging.WARNING, format="%(asctime)s  %(message)s")
    # En nivel INFO, httpx imprime cada URL de Telegram, y la URL lleva el token.
    logging.getLogger("httpx").setLevel(logging.WARNING)

    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        print("Falta TELEGRAM_BOT_TOKEN en el .env. Créelo con @BotFather (sección 12.1).")
        return 1

    permitidos = leer_permitidos(os.environ.get("TELEGRAM_USUARIOS_PERMITIDOS", ""))
    modo = "simulado" if opciones.simulado else "real"
    bitacora = Bitacora(modo=modo)
    estado = {"asistentes": {}, "turno": 0}

    def asistente_de(chat_id):
        """Una memoria por conversación: dos personas no comparten historial."""
        if chat_id not in estado["asistentes"]:
            estado["asistentes"][chat_id] = construir(simulado=opciones.simulado)
        return estado["asistentes"][chat_id]

    def autorizado(update):
        return update.effective_user is not None and update.effective_user.id in permitidos

    async def rechazar(update):
        await update.effective_message.reply_text(
            "Este bot es privado y sólo atiende a las personas autorizadas.\n"
            "Su identificador de Telegram es: %s" % update.effective_user.id
        )

    async def responder_en_partes(mensaje, texto):
        for parte in partir_mensaje(texto):
            if parte.strip():
                await mensaje.reply_text(parte)

    async def con_escribiendo(chat, funcion, *args):
        """Corre la llamada al modelo en otro hilo para que el bot no se congele.

        Mientras tanto se manda "escribiendo...", que en Telegram dura unos
        cinco segundos: por eso se repite hasta que la tarea termina.
        """
        tarea = asyncio.ensure_future(asyncio.to_thread(funcion, *args))
        while not tarea.done():
            try:
                await chat.send_action(ChatAction.TYPING)
            except Exception:
                # El aviso es cosmético: si la red de Telegram se tarda en
                # aceptarlo, no hay razón para tirar una respuesta que el
                # modelo ya está preparando (y que ya costó una llamada).
                pass
            await asyncio.wait([tarea], timeout=4)
        return tarea.result()

    async def inicio(update, context):
        if not autorizado(update):
            return await rechazar(update)
        await update.effective_message.reply_text(
            "Asistente del Reglamento de Estudiantes del TecNM.\n\n"
            "Pregúnteme qué dice el Reglamento y le respondo con el artículo y la "
            "fracción exactos. Si el tema no está en el Reglamento se lo digo, en vez "
            "de inventarlo.\n\n"
            + AVISO_LEGAL + "\n\n" + AVISO_DE_PRIVACIDAD + "\n\n"
            "Comandos: /fuente para ver qué documento consulto, /reset para borrar la "
            "memoria de esta conversación."
        )

    async def fuente(update, context):
        if not autorizado(update):
            return await rechazar(update)
        await update.effective_message.reply_text(asistente_de(update.effective_chat.id).fuente())

    async def reset(update, context):
        if not autorizado(update):
            return await rechazar(update)
        asistente_de(update.effective_chat.id).reset()
        await update.effective_message.reply_text("Listo: la memoria de esta conversación quedó vacía.")

    async def pregunta(update, context):
        if not autorizado(update):
            return await rechazar(update)

        mensaje = update.effective_message
        texto = (mensaje.text or "").strip()
        if not texto:
            return

        asistente = asistente_de(update.effective_chat.id)
        estado["turno"] += 1
        identificador = "TG-%d" % estado["turno"]
        anonimo = usuario_anonimo(update.effective_user.id)

        try:
            resultado = await con_escribiendo(update.effective_chat, asistente.responder, texto)
        except Exception as error:
            await mensaje.reply_text(
                "No pude responder ahora mismo: %s\n"
                "Su pregunta no se guardó en la memoria; puede intentar de nuevo."
                % resumen_del_error(error)
            )
            bitacora.escribir(id=identificador, pregunta=texto, error=str(error),
                              canal="telegram", usuario=anonimo)
            return

        await responder_en_partes(mensaje, resultado["respuesta"])
        bitacora.escribir(id=identificador, pregunta=texto, canal="telegram",
                          usuario=anonimo, **resultado)

    # Los tiempos de espera por omisión de la librería son de unos pocos
    # segundos. Con una red lenta eso basta para que falle hasta un aviso de
    # "escribiendo...", así que se dan más holgados.
    aplicacion = (
        ApplicationBuilder()
        .token(token)
        .connect_timeout(20.0)
        .read_timeout(20.0)
        .write_timeout(20.0)
        .pool_timeout(20.0)
        .build()
    )
    aplicacion.add_handler(CommandHandler("start", inicio))
    aplicacion.add_handler(CommandHandler("fuente", fuente))
    aplicacion.add_handler(CommandHandler("reset", reset))
    aplicacion.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, pregunta))

    print("Bot en marcha [modo %s]." % modo)
    print("Autorizados: %s" % (", ".join(str(u) for u in sorted(permitidos)) or "NADIE (revise el .env)"))
    print("Bitácora: %s" % bitacora.ruta)
    print("Ctrl+C para detenerlo. Sólo puede correr un bot a la vez con el mismo token.")
    aplicacion.run_polling()
    return 0


if __name__ == "__main__":
    sys.exit(main())
