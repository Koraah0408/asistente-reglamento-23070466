# Asistente del Reglamento de Estudiantes del TecNM

- **Alumno:** José Ramiro Márquez Aguayo
- **Número de control:** 23070466
- **Asignatura:** Desarrollo de Agentes Inteligentes (ACD-2504), grupo 850P-A
- **Docente:** D. C. C. Alejandro Estrada Padilla
- **Trabajo:** Práctica 3 · Unidad 1
- **Entrega:** 30 de septiembre de 2026

## Qué hace

Responde dudas de estudiantes sobre el Reglamento de Estudiantes del Tecnológico Nacional de México —si hay que traer credencial, qué pasa si alguien entra armado, cuánto tiempo hay para inconformarse contra una sanción— citando el artículo y la fracción exactos. Su única fuente es `data/reglamento_estudiantes_tecnm.json`, la transcripción del cuerpo normativo aprobado el 31 de enero de 2023: 22 artículos, 104 fracciones y dos transitorios. Cuando el tema no está ahí (faltas, calificaciones, extraordinarios, becas, titulación) contesta "No consta en el Reglamento de Estudiantes" y manda al Manual de Lineamientos o a Servicios Escolares, en lugar de inventarse un porcentaje de asistencia.

Lo que lo distingue de pegar el PDF en un chat es que **el prompt pide y el código verifica**. Las instrucciones de sistema le piden al modelo citar con un formato exacto y no inventar artículos, pero eso no garantiza nada: `app/citas.py` extrae con una expresión regular cada cita de la respuesta y la compara contra un índice de 126 claves construido desde el JSON. Si el modelo escribe `Art. 31, fracc. II` —un artículo que no existe— el programa no lo oculta ni lo corrige: muestra la respuesta con un aviso pegado, `[Aviso] Estas citas no existen en el Reglamento: 31.II`, y guarda la cita inválida en la bitácora. Una respuesta fluida con un artículo inventado es la peor respuesta posible, porque un estudiante le creería.

El Reglamento completo (unos 25 mil caracteres) viaja dentro de las instrucciones de sistema en cada llamada. No hay búsqueda ni herramientas: el modelo siempre tiene el documento entero a la vista. El precio de esa sencillez son unos 6,500 tokens de entrada por pregunta, y está medido en `evaluacion/resultados.md`.

## Arquitectura

```
Tú> ¿y cuál es la más grave?
         │
         ▼
  memoria.agregar(historial, "usuario", pregunta)
  memoria.recortar(historial, MAX_MENSAJES) ──► sólo los últimos 6 mensajes
         │                                       (el historial completo se conserva)
         ▼
  modelo.llamar_modelo(enviados, sistema) ─────► UNA llamada, sin herramientas
         │   sistema = prompts/sistema.md con {REGLAMENTO} sustituido
         │             por reglamento.texto_para_prompt()
         ▼
  memoria.agregar(historial, "modelo", texto)   ◄── se guarda lo que dijo el modelo,
         │                                          tal cual, sin el aviso
         ▼
  citas.extraer_citas(texto) ──► citas.validar_citas(citas, indice_de_126)
         │
         │   si hay citas inválidas, el código pega un aviso visible
         ▼
  respuesta en pantalla + una línea JSON en logs/corrida-AAAAMMDD-HHMMSS.jsonl
```

Cuatro ideas lo sostienen:

1. **El modelo no tiene memoria.** Cada llamada es independiente. Si parece recordar la pregunta anterior es porque `app/memoria.py` se la volvió a enviar. Lo que no se envía, no existe para el modelo.
2. **La memoria corta se recorta.** Se mandan sólo los últimos `MAX_MENSAJES` mensajes, porque cada mensaje extra se vuelve a cobrar en tokens en todas las llamadas siguientes.
3. **El prompt pide; el código verifica.** `validar_citas` es lo que garantiza que una cita exista; el prompt sólo lo pide.
4. **Telegram es nada más otro canal.** La terminal y el bot llaman al mismo `Asistente.responder`. `app/bot.py` no arma prompts, no extrae citas y no recorta memoria.

## Requisitos e instalación

Python 3.11 o superior y una clave gratuita de Google AI Studio.

```
git clone https://github.com/USUARIO/asistente-reglamento-23070466.git
cd asistente-reglamento-23070466
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Después abra `.env` y escriba su clave. El modo simulado (`--simulado`) funciona sin clave y sin internet.

En Windows, si `python` en el PATH apunta a otra instalación (por ejemplo la que traen Inkscape o la Microsoft Store), conviene crear el entorno con el lanzador: `py -m venv .venv`. Una vez activado el entorno, `python` ya apunta al del proyecto.

## Variables de entorno

Van en `.env`, que **no se sube al repositorio**: está en `.gitignore` desde antes del primer commit. `.env.example` es la plantilla, con los nombres pero sin valores.

| Variable | Para qué sirve |
|---|---|
| `GEMINI_API_KEY` | Clave de Google AI Studio. Sin ella sólo corre el modo simulado. |
| `GEMINI_MODEL` | Identificador del modelo, `gemini-3.5-flash`. Se lee de aquí para no tenerlo escrito en el código. |
| `MAX_MENSAJES` | Cuántos mensajes de la conversación se le envían al modelo. Por omisión 6. |
| `TELEGRAM_BOT_TOKEN` | Token que entrega @BotFather. Quien lo tenga controla el bot. |
| `TELEGRAM_USUARIOS_PERMITIDOS` | Identificadores numéricos separados por comas. Vacío = el bot no atiende a nadie. |

## Cómo usarlo

**El chat en la terminal**

```
python -m app.cli --simulado
python -m app.cli
```

Comandos: `/fuente` dice qué documento se consulta y su fecha de aprobación, `/reset` borra la memoria de la conversación y `/salir` termina.

**El banco de pruebas**

```
python -m app.lote data/preguntas_prueba.json --simulado
python -m app.lote data/preguntas_prueba.json
python -m app.lote data/preguntas_prueba.json --solo R01,R02,R03,R04,R05,R06
python -m app.lote data/preguntas_prueba.json --solo C1,C2
```

`--solo` acepta preguntas sueltas (`R05`), conversaciones completas (`C1`) o un turno suelto (`C1-2`). Cada pregunta suelta empieza con la memoria vacía; dentro de una conversación la memoria se comparte. Entre llamadas reales espera 4 segundos.

**Las pruebas**

```
python -m pruebas.prueba_citas
```

No usan pytest ni tocan la red: sólo `assert`. Imprimen `OK` al final.

## Bot de Telegram

1. En Telegram, abra una conversación con **@BotFather** (la cuenta oficial, con palomita azul) y mande `/newbot`.
2. Elija un nombre visible y un nombre de usuario que termine en `bot`.
3. BotFather entrega un token con la forma `123456789:AA...`. Cópielo a `TELEGRAM_BOT_TOKEN` en `.env`, **nunca al código, al README ni a una captura**. Si se filtra, en BotFather use `/revoke` y genere otro.
4. Corra el bot y escríbale desde el celular. Como todavía no está en la lista, le va a contestar que es privado y le va a mostrar **su identificador numérico**. Copie ese número a `TELEGRAM_USUARIOS_PERMITIDOS` en `.env` y vuelva a arrancar el bot.

```
python -m app.bot --simulado
python -m app.bot
```

Atiende `/start` (qué hace, aviso de que no es autoridad del plantel y aviso de privacidad), `/fuente`, `/reset` y cualquier texto que no sea comando. La memoria es una por conversación: dos personas no comparten historial. Mientras Gemini responde muestra "escribiendo..." y no se congela, porque la llamada corre en otro hilo con `asyncio.to_thread`. Las respuestas más largas de 4,096 caracteres se parten, de preferencia en un salto de línea.

Sólo puede correr un bot a la vez con el mismo token: si arranca un segundo, Telegram responde `Conflict`.

La captura de una conversación real está en `evidencia/telegram.png`.

## Estructura del proyecto

```
asistente-reglamento-23070466/
├── README.md                   este archivo
├── requirements.txt            google-genai, python-dotenv, python-telegram-bot
├── .env.example                plantilla de variables (el .env real no se sube)
├── .gitignore                  .env, .venv/, __pycache__/
├── verificar_entrega.py        del docente: revisa la forma de la entrega
├── traza_manual.md             Parte E, escrita a mano
├── app/
│   ├── reglamento.py           cargar el JSON, texto para el prompt, índice de 126 citas
│   ├── modelo.py               la ÚNICA función que habla con Gemini
│   ├── modelo_simulado.py      modelo falso con guion fijo, para no gastar cuota
│   ├── memoria.py              agregar y recortar mensajes
│   ├── citas.py                extraer citas con regex, validarlas y avisar
│   ├── asistente.py            une todo: una pregunta → una respuesta revisada, y la bitácora
│   ├── cli.py                  chat en la terminal
│   ├── lote.py                 corre el banco de pruebas
│   └── bot.py                  bot de Telegram: sólo recibe y entrega mensajes
├── prompts/sistema.md          instrucciones de sistema con el marcador {REGLAMENTO}
├── pruebas/prueba_citas.py     pruebas sin red
├── data/                       material del docente, sin modificar
├── evaluacion/                 esperadas.md y resultados.md
├── logs/                       bitácoras jsonl, una línea por turno
└── evidencia/telegram.png      captura de una conversación con el bot
```

## Decisiones de diseño

`texto_para_prompt` escribe **una línea por cita posible**, con el mismo formato con el que el modelo debe citar: `Art. 9.` para el encabezado, `Art. 9, fracc. II.` por fracción y `Art. 9 (párrafo final).` para el cierre. La idea es que el modelo copie la cita de la misma línea donde leyó el dato en vez de reconstruirla de memoria. Los títulos van en mayúsculas y sólo se imprimen cuando cambian. Los incisos 1 a 4 del artículo 14 se tratan igual que las fracciones, usando su id tal como viene en el JSON.

`extraer_citas` usa una sola expresión regular que reconoce `Art. 9`, `Artículo 9`, `art 9`, con o sin coma antes de la fracción, y tanto `fracc. II` como `fracción II` o `numeral 3`. El romano se guarda siempre en mayúsculas y las citas repetidas se descartan. La clave queda como `"9"`, `"9.II"` o `"14.3"`, que es el mismo formato del índice.

`MAX_MENSAJES` vale **6**, o sea tres turnos completos de ida y vuelta. Con menos, una pregunta de seguimiento como "¿y ésa se puede apelar?" se queda sin el contexto que la vuelve entendible; con más, cada llamada se encarece sin ganar nada, porque las conversaciones del banco no pasan de tres turnos.

**Cuando una cita es inválida**, la respuesta se muestra completa con el aviso pegado por el código, y las citas inválidas se registran aparte en la bitácora. En la memoria, en cambio, queda lo que dijo el modelo tal cual: el aviso es un agregado para quien lee, no algo que el modelo haya escrito.

**Cuando la llamada falla** (sin red, cuota agotada, servidor saturado), el usuario ve un mensaje en español —`resumen_del_error` distingue el 429 diario del 429 por minuto y del 503— y nunca un traceback. La pregunta sin respuesta sale de la memoria, para que la conversación no se quede con un turno a medias. En el lote, un turno que falla se anota en la bitácora y el lote sigue; si el que falla es un turno de una conversación, los siguientes de esa conversación se omiten, porque sin el turno anterior en la memoria ya no probarían lo que debían probar.

## Resultados

COMPLETAR después de la corrida real, con los números de `evaluacion/resultados.md`:

- respuestas correctas de 18;
- citas inválidas en total;
- tokens de entrada promedio por llamada y total de la corrida;
- la estimación para el Manual de Lineamientos (334 mil caracteres).

## Límites y ética

Este asistente **no es autoridad del Tecnológico**. No sanciona, no autoriza y no resuelve casos: sólo explica qué dice el Reglamento de Estudiantes, y quien decide es la autoridad del plantel. No sustituye a Servicios Escolares ni a la Dirección.

Su única fuente es el Reglamento de Estudiantes. **No** sabe nada de faltas, calificaciones, exámenes extraordinarios, bajas de materias, becas, residencias ni titulación: eso es materia del Manual de Lineamientos Académico-Administrativos, y ante esas preguntas contesta que no consta.

Ante un caso personal o delicado explica la norma general con sus citas, pero no juzga el caso ni dice quién tiene razón, porque no conoce las pruebas. Recomienda presentarlo por escrito ante la Dirección del plantel, y si hay riesgo para la integridad de alguien, avisar de inmediato a las autoridades.

No guarda datos personales. En la bitácora del bot nunca se escribe el identificador de Telegram ni el nombre de quien pregunta: sólo los primeros 10 caracteres del SHA-256 del identificador, que alcanzan para distinguir a dos personas sin saber quiénes son. El `/start` del bot avisa que los mensajes pasan por Telegram y por Google, y pide no escribir datos personales. El bot sólo atiende a la lista de `TELEGRAM_USUARIOS_PERMITIDOS`; con la lista vacía no atiende a nadie.

## Declaración de uso de IA

COMPLETAR al final, con lo que realmente haya pasado. Como referencia de lo que va aquí: qué herramienta se usó, para qué parte y qué hubo que corregirle. La traza de la Parte E y las respuestas esperadas de `evaluacion/esperadas.md` no se generaron con un asistente.
