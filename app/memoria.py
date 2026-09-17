"""La memoria corta de la conversación.

El modelo no recuerda nada entre llamadas: cada petición es independiente. Si
el modelo "recuerda" la pregunta anterior es sólo porque este código se la
volvió a enviar. Lo que no se envía, no existe para el modelo.

El historial completo se conserva en el programa; al modelo se le manda nada
más el recorte de los últimos mensajes, porque cada mensaje extra se vuelve a
cobrar en tokens de entrada en todas las llamadas siguientes.
"""

ROLES = ("usuario", "modelo")


def agregar(historial, rol, texto):
    """Agrega un mensaje al final del historial. No devuelve nada: modifica la lista."""
    if rol not in ROLES:
        raise ValueError("rol inválido: %r (se esperaba 'usuario' o 'modelo')" % (rol,))
    historial.append({"rol": rol, "texto": texto})


def recortar(historial, max_mensajes):
    """Devuelve una lista NUEVA con los últimos `max_mensajes` mensajes.

    No modifica el historial original: si se le borraran mensajes, el programa
    perdería la conversación aunque el modelo siguiera respondiendo.

    Aplica además una regla: si el primer mensaje del recorte es del modelo, se
    descarta, porque una conversación enviada al modelo debe empezar con un
    mensaje del usuario. Por eso un recorte puede devolver menos mensajes que
    `max_mensajes`.

    Con `max_mensajes` igual a 0 (o menos) devuelve una lista vacía.
    """
    if max_mensajes <= 0:
        return []

    recorte = list(historial[-max_mensajes:])

    if recorte and recorte[0]["rol"] == "modelo":
        recorte = recorte[1:]

    return recorte
