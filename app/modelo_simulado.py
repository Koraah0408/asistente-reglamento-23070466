"""Un modelo falso, con guion fijo, para desarrollar sin gastar cuota.

Tiene la misma firma y devuelve el mismo diccionario que `modelo.llamar_modelo`,
pero no toca la red. Con él se pueden probar la memoria, la extracción de citas,
el aviso, la bitácora y el lote completo cuantas veces haga falta.

El guion tiene a propósito los tres casos que el resto del programa debe saber
manejar:

1. una respuesta correcta, con una cita que sí existe;
2. una respuesta de "no consta", sin citas;
3. una respuesta con una cita inventada, que la validación debe marcar.
"""

GUION = [
    (
        "Respuesta: Sí. Entre las obligaciones de la comunidad estudiantil está portar la "
        "credencial vigente que te identifica como estudiante y mostrarla cuando te la pidan.\n"
        "Fundamento: Art. 7, fracc. XV\n"
        "Confianza: alta"
    ),
    (
        "Respuesta: Ese tema no lo trata el Reglamento de Estudiantes. Las faltas, las "
        "calificaciones y los exámenes son materia del Manual de Lineamientos "
        "Académico-Administrativos del TecNM; conviene preguntarlo en Servicios Escolares.\n"
        "Fundamento: no consta en el Reglamento de Estudiantes\n"
        "Confianza: alta"
    ),
    (
        "Respuesta: El Reglamento prevé que en ese caso se levante un acta y se turne al "
        "Comité Académico dentro de los tres días hábiles siguientes.\n"
        "Fundamento: Art. 31, fracc. II\n"
        "Confianza: media"
    ),
]


class ModeloSimulado:
    """Invocable con la misma firma que `llamar_modelo`.

    Va entregando las respuestas del guion en orden y vuelve a empezar cuando se
    acaban, de modo que un lote largo pasa varias veces por los tres casos.
    """

    def __init__(self, guion=None):
        self.guion = list(guion) if guion else list(GUION)
        self.llamadas = 0

    def __call__(self, historial, sistema):
        texto = self.guion[self.llamadas % len(self.guion)]
        self.llamadas += 1

        # Los tokens no se pueden saber sin la API, así que se estiman con la
        # regla de un token por cada cuatro caracteres. Sirven para probar que
        # la bitácora guarda números, no para comparar con la corrida real.
        caracteres_de_entrada = len(sistema) + sum(len(mensaje["texto"]) for mensaje in historial)

        return {
            "texto": texto,
            "tokens_entrada": caracteres_de_entrada // 4,
            "tokens_salida": len(texto) // 4,
            "modelo": "simulado",
        }
