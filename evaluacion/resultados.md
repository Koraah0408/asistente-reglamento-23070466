# Resultados de la corrida real

Corrida del banco completo contra `gemini-3.5-flash`, repartida en dos días por la cuota
de la capa gratuita. Todo lo que sigue sale de `logs/corrida-*.jsonl`; nada está escrito
a mano.

- Día 1 (17 de septiembre): `corrida-20260917-193714.jsonl`, R01 a R04. R05 y R06 se
  cortaron con un `429 RESOURCE_EXHAUSTED`.
- Día 2 (20 de septiembre): `corrida-20260920-140602.jsonl` con R05 a R12, y
  `corrida-20260920-141149.jsonl` con las dos conversaciones.

## 1. Los 18 turnos

Una respuesta es **correcta** si cita lo esperado y no trae citas inválidas, o si dice
«no consta» cuando debía.

| # | Cita esperada | Citas obtenidas | Citas inválidas | ¿Correcta? | Tokens de entrada |
|---|---|---|---|---|---|
| R01 | Art. 7, fracc. XV | 7.XV | - | sí | 6761 |
| R02 | Art. 8, fracc. VIII; Art. 9 | 8.VIII, 9, 12 | - | sí | 6763 |
| R03 | Art. 9, fracc. II | 9.II | - | sí | 6764 |
| R04 | Art. 15 | 15 | - | sí | 6766 |
| R05 | Art. 12 | 12, 2.X | - | sí | 6759 |
| R06 | Art. 2, fracc. XIII; Art. 3 | 2.XIII, 3 | - | sí | 6762 |
| R07 | Art. 19, fracc. III; Art. 20 | 19.III, 20 | - | sí | 6766 |
| R08 | no consta | no consta | - | sí | 6763 |
| R09 | no consta | no consta | - | sí | 6759 |
| R10 | no consta | no consta | - | sí | 6758 |
| R11 | Art. 8, fracc. VI; Art. 13 | 7.XVIII, 7.XXI, 8.VI, 13 | - | sí | 6767 |
| R12 | Art. 7, fracc. XX | 7.XX | - | sí | 6769 |
| C1-1 | Art. 9, fracc. I; Art. 9, fracc. II; Art. 9, fracc. III; Art. 9, fracc. IV; Art. 9, fracc. V | 9.I, 9.II, 9.III, 9.IV, 9.V | - | sí | 6754 |
| C1-2 | Art. 9, fracc. V | 9.V | - | sí | 6895 |
| C1-3 | Art. 15 | 15 | - | sí | 6951 |
| C2-1 | Art. 8, fracc. II | 8.II | - | sí | 6759 |
| C2-2 | Art. 8, fracc. II | 8.II | - | sí | 6829 |
| C2-3 | Art. 10 | 10.I, 10.II, 10.III, 10.IV, 10.V | - | sí | 6929 |

**Cómo se comparó:** un artículo esperado se da por citado si el modelo citó el artículo
o cualquiera de sus fracciones. Esto sólo aplicó en C2-3: yo esperaba `Art. 10` y el
modelo desglosó `10.I` a `10.V`, que son los criterios de ese mismo artículo. Contarlo
como fallo habría sido un error de medición, no del asistente.

## 2. Totales

| | |
|---|---|
| Turnos evaluados | 18 de 18 |
| Correctas | **18** |
| Parciales | 0 |
| Incorrectas | 0 |
| Citas inválidas en total | **0** |

El asistente acertó en los 18 turnos y **no inventó una sola cita** en toda la corrida.

Eso tiene una consecuencia que conviene decir en voz alta: el aviso de citas inválidas de
`app/citas.py` **nunca se disparó con el modelo real**. La única vez que se le ha visto
funcionar es con `modelo_simulado.py`, cuyo guion incluye un `Art. 31, fracc. II`
inventado a propósito. Que no haya hecho falta es buena señal del prompt, pero no es
prueba de que el modelo no pueda inventar: es prueba de que en estos 18 turnos no lo hizo.

## 3. Tokens

| | |
|---|---|
| Tokens de entrada, promedio por llamada | **6,793.0** |
| Tokens de entrada, mínimo / máximo | 6754 / 6951 |
| Tokens de entrada, total de la corrida | 122,274 |
| Tokens de salida, total de la corrida | 15,777 |

El promedio casi no se mueve (6754 a 6951) porque el Reglamento completo viaja en
cada llamada y es casi todo lo que se envía: el prompt de sistema ocupa 28,224
caracteres. Lo único que varía es la pregunta y, en las conversaciones, la memoria: C1-1
envió 6,754 tokens con la memoria vacía y C1-3 envió 6,951 con dos turnos cargados
atrás. Esos ~200 tokens de diferencia son el precio de la memoria corta.

## 4. Estimación: ¿y si agregara el Manual de Lineamientos?

Proporción medida en esta corrida:

- 6,793.0 tokens de entrada en promedio ÷ 28,224 caracteres de prompt =
  **0.2407 tokens por caracter**
- o sea, aproximadamente **4.15 caracteres por token**

El Manual de Lineamientos Académico-Administrativos tiene unos 334,000 caracteres. Con esa
proporción:

- El Manual solo costaría unos **80,388 tokens** de entrada.
- Cada pregunta, por sencilla que sea, pasaría de ~6,793 a
  **~87,181 tokens de entrada**: unas **13 veces más**.

### Dos problemas que aparecerían

**1. El costo se vuelve prohibitivo y la cuota se acaba antes de empezar.** Esta corrida de
18 turnos gastó 122,274 tokens de entrada; con el Manual gastaría cerca de 1.57
millones, y eso para responder preguntas cuya respuesta cabe en tres renglones. Ya con el
Reglamento solo se agotó la cuota diaria a la mitad del banco y hubo que partir la corrida
en dos días. Se paga el documento entero en cada pregunta, aunque la respuesta esté en una
sola línea.

**2. La aguja se pierde en el pajar.** El modelo tendría que encontrar la línea correcta
entre ~360,000 caracteres en vez de ~28,000, y además distinguir cuál de los dos documentos
aplica. Las citas inventadas y las cruzadas —citar el Reglamento cuando la norma es del
Manual— se vuelven mucho más probables. La latencia también crece: en esta corrida ya hubo
turnos de 98 segundos con 6,800 tokens.

### Qué alternativa de diseño los evita

Dejar de mandar el documento completo y **mandar sólo los fragmentos que hacen falta**:
indexar los artículos, buscar los que se parecen a la pregunta y meter en el prompt nada
más ésos; o darle al modelo una herramienta con la que pueda consultar el documento él
mismo en vez de recibirlo entero. Cada pregunta viajaría con unos cuantos cientos de tokens
de contexto en lugar de ochenta mil, y el índice de citas seguiría sirviendo igual para
verificar lo que responde.

Es exactamente el salto que anuncia el documento de la práctica para el proyecto de la
unidad: los 22,900 negocios del DENUE no caben en ningún prompt, y ahí el modelo tendrá que
pedir los datos con herramientas.

## 5. La respuesta más débil de la corrida

Siendo las 18 correctas, la más floja es **R05** («¿quién decide qué sanción le toca a un
estudiante?»):

```
Respuesta: La decisión de aplicar una sanción le corresponde al director o directora de tu
plantel, quien la emite tomando en cuenta una propuesta que previamente elabora el Comité
Académico.
Fundamento: Art. 12; Art. 2, fracc. X
Confianza: alta
```

La respuesta es correcta y el `Art. 12` es exactamente la norma que la sostiene. El problema
es la segunda cita: el `Art. 2, fracc. X` es la **definición** de qué es el Comité Académico,
no la norma que establece quién decide. Citarla como «fundamento» es relleno: si un
estudiante va a buscar ahí por qué manda el Director, no va a encontrar nada.

**¿De quién fue el problema?** Del prompt. Mis instrucciones de sistema piden que toda
afirmación normativa lleve cita, pero nunca dicen que la cita debe ser la norma que resuelve
la pregunta y no una definición del glosario. El modelo cumplió la regla al pie de la letra.

No fue del código, y eso es lo interesante: `validar_citas` comprobó que `2.X` existe —y
existe— así que la dio por buena. El código sabe si una cita **existe**, no si **viene al
caso**. Para arreglarlo habría que agregar una regla al prompt, algo como «no cites el
artículo de definiciones como fundamento, salvo que la pregunta sea qué significa un
término».

## 6. Qué garantiza mi código y qué sólo le pide el prompt al modelo

**Lo garantiza el código:** que cada cita de la respuesta exista de verdad en el Reglamento,
porque `extraer_citas` las saca con una expresión regular y `validar_citas` las compara
contra el índice de 126 claves construido desde el JSON; que el modelo no vea más de
`MAX_MENSAJES` mensajes, porque `recortar` decide qué se envía y qué no; que el documento que
viaja en el prompt sea el JSON del docente y no otra cosa; y que cada turno quede registrado
con sus tokens y sus citas en la bitácora.

**Sólo se lo pide el prompt:** que la cita elegida sea la que de verdad responde la pregunta
—R05 muestra que no siempre lo es—, que diga «no consta» en vez de inventar, que respete el
formato de tres renglones, que no juzgue casos personales y que escriba una cita por fracción
en lugar de «fracciones XVIII y XXI». Nada de eso lo puede comprobar el código: son cosas que
el modelo cumple porque se le pidieron, y el día que deje de cumplirlas, el programa no se va
a enterar.
