# Traza a mano · Práctica 3

> Esta parte **no se hace con un asistente de IA**.
>
> 1. Primero prediga a mano, leyendo su propio código.
> 2. Después ejecute su programa y compare.
>
> Si su predicción no coincidió, déjela como estaba y explique la diferencia.

## E.1 La memoria (`max_mensajes = 4`)

Mensajes que se agregan: `u1`, `m1`, `u2`, `m2`, `u3`, `m3`, `u4` y `m4`.

| Llamada | Lista que recibe el modelo (predicción) | Cantidad | Lo que dio el programa | ¿Coincide? |
|---|---|---|---|---|
| 1 | (escriba aquí) | | | |
| 2 | (escriba aquí) | | | |
| 3 | (escriba aquí) | | | |
| 4 | (escriba aquí) | | | |

**Mensajes del historial completo al terminar:** (escriba aquí)

**¿Qué recortes cambian por la regla «si el primero es del modelo, se descarta»? ¿Qué habría recibido el modelo sin ella?**

(escriba aquí)

**En el turno 4, «¿y eso a quién aplica?» se refiere a `u1`. ¿Lo puede entender el modelo? ¿Por qué?**

(escriba aquí)

## E.2 Las citas

| Texto | `extraer_citas` (predicción) | Inválidas (predicción) | Lo que dio el programa | ¿Coincide? |
|---|---|---|---|---|
| T1 | (escriba aquí) | | | |
| T2 | (escriba aquí) | | | |
| T3 | (escriba aquí) | | | |
| T4 | (escriba aquí) | | | |
| T5 | (escriba aquí) | | | |
| T6 | (escriba aquí) | | | |

**¿Qué hace su código con T6? ¿Su verificación detecta el problema? ¿Qué parte del sistema debería evitar que el modelo escriba así?**

(escriba aquí)

## E.3 Los tokens de la conversación C1

| Turno | Mensajes enviados | Tokens de entrada | Tokens de salida |
|---|---|---|---|
| C1-1 | | | |
| C1-2 | | | |
| C1-3 | | | |

**¿Por qué crecen los tokens de entrada? ¿Qué parte de ellos es el Reglamento?**

(escriba aquí)

**¿Qué pasaría en el turno 10 de una conversación larga si `recortar` no existiera?**

(escriba aquí)
