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
| 1 | `[u1]` | 1 | `[u1]` | Sí |
| 2 | `[u1, m1, u2]` | 3 | `[u1, m1, u2]` | Sí |
| 3 | `[u2, m2, u3]` | 3 | `[u2, m2, u3]` | Sí |
| 4 | `[u3, m3, u4]` | 3 | `[u3, m3, u4]` | Sí |

**Mensajes del historial completo al terminar:** 8 mensajes (`[u1, m1, u2, m2, u3, m3, u4, m4]`).

**¿Qué recortes cambian por la regla «si el primero es del modelo, se descarta»? ¿Qué habría recibido el modelo sin ella?**

Las llamadas 3 y 4. Sin esa regla, la llamada 3 habría recibido `[m1, u2, m2, u3]` (4 mensajes) comenzando por una respuesta del modelo `m1` huérfana de su pregunta `u1`. Con la regla, se descarta `m1` y se envían 3 mensajes (`[u2, m2, u3]`), garantizando que la conversación enviada al modelo comience siempre con un mensaje del usuario.

**En el turno 4, «¿y eso a quién aplica?» se refiere a `u1`. ¿Lo puede entender el modelo? ¿Por qué?**

No. En la llamada 4 el modelo únicamente recibe `[u3, m3, u4]`. Como `u1` y `m1` ya fueron recortados del contexto enviado, para el modelo `u1` no existe en la conversación actual y no podrá entender la referencia.

## E.2 Las citas

| Texto | `extraer_citas` (predicción) | Inválidas (predicción) | Lo que dio el programa | ¿Coincide? |
|---|---|---|---|---|
| T1 | `['9.II']` | `[]` | `['9.II']` / `[]` | Sí |
| T2 | `['15', '8.VIII']` | `[]` | `['15', '8.VIII']` / `[]` | Sí |
| T3 | `['7.XXV', '23']` | `['7.XXV', '23']` | `['7.XXV', '23']` / `['7.XXV', '23']` | Sí |
| T4 | `[]` | `[]` | `[]` / `[]` | Sí |
| T5 | `['14.3']` | `[]` | `['14.3']` / `[]` | Sí |
| T6 | `['7.XVIII']` | `[]` | `['7.XVIII']` / `[]` | Sí |

**¿Qué hace su código con T6? ¿Su verificación detecta el problema? ¿Qué parte del sistema debería evitar que el modelo escriba así?**

La expresión regular sólo extrae la primera fracción (`['7.XVIII']`) y omite `XXI` porque está unida con la conjunción «y» en lugar de repetir la estructura `Art. 7, fracc. XXI`. Como la cita `7.XXI` no fue extraída, la función `validar_citas` no la procesa y no detecta el problema.
La parte del sistema que debe evitar que el modelo redacte de esta forma son las **instrucciones de sistema (`prompts/sistema.md`)**, las cuales obligan al modelo a citar cada fracción por separado usando el formato exacto `Art. N, fracc. R; Art. N, fracc. R` separadas por punto y coma.

## E.3 Los tokens de la conversación C1

| Turno | Mensajes enviados | Tokens de entrada | Tokens de salida |
|---|---|---|---|
| C1-1 | 1 | 6,754 | 1,050 |
| C1-2 | 3 | 6,895 | 648 |
| C1-3 | 5 | 6,951 | 586 |

**¿Por qué crecen los tokens de entrada? ¿Qué parte de ellos es el Reglamento?**

Crecen porque en cada nuevo turno se acumulan en el contexto recortado los mensajes anteriores de la conversación (preguntas del usuario y respuestas del modelo). El Reglamento representa la inmensa mayoría de los tokens de entrada (aprox. 6,500 a 6,700 tokens en la instrucción de sistema).

**¿Qué pasaría en el turno 10 de una conversación larga si `recortar` no existiera?**

El historial acumularía los 19 mensajes previos (9 preguntas y 10 respuestas). Esto incrementaría constantemente el consumo de tokens de entrada en cada llamada posterior, elevando los costos y agotando más rápidamente la cuota diaria del API de Gemini.
