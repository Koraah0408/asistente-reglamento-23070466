"""Verificador de entrega · Práctica 3, Unidad 1 · ACD-2504

Uso, en la raíz de su repositorio:   python verificar_entrega.py

Revisa la FORMA de la entrega (estructura, secretos, datos intactos, pruebas, bitácora,
orden de los commits). No revisa la calidad: eso lo hace el docente con la rúbrica.
"""
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
HASHES = {
    "data/reglamento_estudiantes_tecnm.json": "76c88e3544f17d96c07e5abd5d1911e1bea59464fcab9df3d634cf6f44b211a3",
    "data/preguntas_prueba.json": "cbbd70b15ab899bb26d9c70d2ec9f0411363c60f9dd671abc21fdefe6824db0e",
}
IDS = ["R%02d" % i for i in range(1, 13)] + ["C%d-%d" % (c, t) for c in (1, 2) for t in (1, 2, 3)]
ARCHIVOS = [
    "README.md", "requirements.txt", ".env.example", ".gitignore", "traza_manual.md",
    "app/__init__.py", "app/reglamento.py", "app/modelo.py", "app/modelo_simulado.py",
    "app/memoria.py", "app/citas.py", "app/asistente.py", "app/cli.py", "app/lote.py", "app/bot.py",
    "prompts/sistema.md", "pruebas/__init__.py", "pruebas/prueba_citas.py",
    "data/reglamento_estudiantes_tecnm.json", "data/preguntas_prueba.json",
    "evaluacion/esperadas.md", "evaluacion/resultados.md",
]
CAMPOS_BITACORA = ["ts", "corrida", "modo", "id", "pregunta", "respuesta", "citas", "citas_invalidas",
                   "no_consta", "mensajes_enviados", "tokens_entrada", "tokens_salida", "modelo", "segundos"]

resultados = []


def informe(estado, texto):
    resultados.append(estado)
    print("[%s] %s" % (estado.ljust(5), texto))


def git(*args):
    r = subprocess.run(["git", *args], cwd=RAIZ, capture_output=True, text=True, encoding="utf-8")
    return r.stdout.strip() if r.returncode == 0 else None


def primer_commit(ruta):
    """Hash del primer commit que agregó la ruta, o None."""
    salida = git("log", "--diff-filter=A", "--follow", "--format=%H", "--", ruta)
    return salida.splitlines()[-1] if salida else None


def antes(commit_a, commit_b):
    """True si commit_a es un ancestro estricto de commit_b en el historial."""
    return commit_a != commit_b and git("merge-base", "--is-ancestor", commit_a, commit_b) is not None


def sha256(ruta):
    # Se normalizan los finales de línea: Git en Windows puede convertir LF en CRLF.
    return hashlib.sha256((RAIZ / ruta).read_bytes().replace(b"\r\n", b"\n")).hexdigest()


# 1. Estructura
faltan = [a for a in ARCHIVOS if not (RAIZ / a).exists()]
informe("OK" if not faltan else "FALTA", "Estructura de archivos" + ("" if not faltan else ": " + ", ".join(faltan)))

# 2. Secretos
es_repo = git("rev-parse", "--is-inside-work-tree") == "true"
if not es_repo:
    informe("FALTA", "La carpeta no es un repositorio de Git")
else:
    rastreados = git("ls-files").splitlines()
    if ".env" in rastreados:
        informe("FALTA", ".env está en el repositorio: revoque su clave y quítelo del historial")
    else:
        informe("OK", ".env no está en el repositorio")
    con_clave = [a for a in rastreados if (RAIZ / a).is_file() and (RAIZ / a).stat().st_size < 5_000_000
                 and re.search(r"AIza[0-9A-Za-z_\-]{30,}", (RAIZ / a).read_text(encoding="utf-8", errors="ignore"))]
    informe("OK" if not con_clave else "FALTA",
            "Sin claves de API en archivos rastreados" + ("" if not con_clave else ": " + ", ".join(con_clave)))
gitignore = (RAIZ / ".gitignore").read_text(encoding="utf-8", errors="ignore") if (RAIZ / ".gitignore").exists() else ""
informe("OK" if re.search(r"^\.env\s*$", gitignore, re.M) else "FALTA", ".gitignore contiene .env")

# Bot de Telegram: token, variables y reglas de diseño
if es_repo:
    con_token = [a for a in rastreados if (RAIZ / a).is_file() and (RAIZ / a).stat().st_size < 5_000_000
                 and re.search(r"\b\d{8,10}:[A-Za-z0-9_\-]{35}\b", (RAIZ / a).read_text(encoding="utf-8", errors="ignore"))]
    informe("OK" if not con_token else "FALTA",
            "Sin tokens de Telegram en archivos rastreados" + ("" if not con_token else ": " + ", ".join(con_token)))
ejemplo = (RAIZ / ".env.example").read_text(encoding="utf-8", errors="ignore") if (RAIZ / ".env.example").exists() else ""
informe("OK" if "TELEGRAM_BOT_TOKEN" in ejemplo and "TELEGRAM_USUARIOS_PERMITIDOS" in ejemplo else "FALTA",
        ".env.example declara TELEGRAM_BOT_TOKEN y TELEGRAM_USUARIOS_PERMITIDOS")
bot = (RAIZ / "app/bot.py").read_text(encoding="utf-8", errors="ignore") if (RAIZ / "app/bot.py").exists() else ""
if bot:
    informe("OK" if "TELEGRAM_USUARIOS_PERMITIDOS" in bot else "FALTA", "app/bot.py usa la lista de usuarios permitidos")
    informe("OK" if re.search(r"to_thread|run_in_executor", bot) else "FALTA",
            "app/bot.py corre el agente en otro hilo (asyncio.to_thread)")
    informe("OK" if not re.search(r"google\.genai|from google import genai", bot) else "FALTA",
            "app/bot.py no llama a Gemini directamente")
imagenes = [p for p in (RAIZ / "evidencia").glob("telegram*") if p.suffix.lower() in (".png", ".jpg", ".jpeg")] \
    if (RAIZ / "evidencia").exists() else []
informe("OK" if imagenes else "FALTA", "Captura de Telegram en evidencia/")


# 3. Datos del docente intactos
for ruta, esperado in HASHES.items():
    if (RAIZ / ruta).exists():
        informe("OK" if sha256(ruta) == esperado else "FALTA", "%s sin modificar" % ruta)

# 4. Contratos que se pueden revisar sin ejecutar el modelo
if (RAIZ / "prompts/sistema.md").exists():
    informe("OK" if "{REGLAMENTO}" in (RAIZ / "prompts/sistema.md").read_text(encoding="utf-8") else "FALTA",
            "prompts/sistema.md contiene el marcador {REGLAMENTO}")
importan = [p.name for p in (RAIZ / "app").glob("*.py")
            if re.search(r"from google import genai|import google\.genai|from google\.genai import",
                         p.read_text(encoding="utf-8", errors="ignore"))]
informe("OK" if importan == ["modelo.py"] else "FALTA",
        "Sólo app/modelo.py importa google.genai (encontrado en: %s)" % (", ".join(importan) or "ninguno"))

# 5. Pruebas
if (RAIZ / "pruebas/prueba_citas.py").exists():
    n = len(re.findall(r"^\s*assert\b", (RAIZ / "pruebas/prueba_citas.py").read_text(encoding="utf-8"), re.M))
    informe("OK" if n >= 15 else "FALTA", "pruebas/prueba_citas.py tiene %d comprobaciones (mínimo 15)" % n)
    r = subprocess.run([sys.executable, "-m", "pruebas.prueba_citas"], cwd=RAIZ, capture_output=True,
                       text=True, encoding="utf-8", errors="replace", timeout=120)
    informe("OK" if r.returncode == 0 else "FALTA",
            "Las pruebas pasan" + ("" if r.returncode == 0 else ": " + (r.stderr.strip().splitlines() or ["?"])[-1]))

# 6. Bitácora real
reales, archivos_reales, malas, telegram = {}, [], 0, 0
for ruta in sorted((RAIZ / "logs").glob("corrida-*.jsonl")):
    real_en_archivo = False
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        try:
            ev = json.loads(linea)
        except json.JSONDecodeError:
            malas += 1
            continue
        if ev.get("modo") == "real" and ev.get("modelo") not in (None, "simulado") and "error" not in ev:
            real_en_archivo = True
            reales[ev.get("id")] = ev
            if ev.get("canal") == "telegram" and not str(ev.get("usuario", "")).isdigit():
                telegram += 1
            if any(c not in ev for c in CAMPOS_BITACORA):
                malas += 1
    if real_en_archivo:
        archivos_reales.append(ruta)
informe("OK" if telegram >= 5 else "FALTA", "Turnos reales desde Telegram con usuario anónimo: %d (mínimo 5)" % telegram)
faltan_ids = [i for i in IDS if i not in reales]
informe("OK" if not faltan_ids else "FALTA",
        "Bitácora real con los 18 turnos" + ("" if not faltan_ids else "; faltan: " + ", ".join(faltan_ids)))
informe("OK" if malas == 0 else "FALTA", "Líneas de bitácora con todos los campos del contrato (%d con problemas)" % malas)
modelos = sorted({ev["modelo"] for ev in reales.values()})
if modelos:
    informe("OK" if len(modelos) == 1 else "AVISO", "Modelos usados en la corrida real: %s" % ", ".join(modelos))

# 7. Esperadas antes que la bitácora real
for ruta in ("evaluacion/esperadas.md", "evaluacion/resultados.md"):
    if (RAIZ / ruta).exists():
        texto = (RAIZ / ruta).read_text(encoding="utf-8", errors="ignore")
        sin = [i for i in IDS if i not in texto]
        informe("OK" if not sin else "FALTA", "%s menciona los 18 identificadores" % ruta + ("" if not sin else "; faltan: " + ", ".join(sin)))
if es_repo and (RAIZ / "evaluacion/esperadas.md").exists() and archivos_reales:
    t_esp = primer_commit("evaluacion/esperadas.md")
    t_logs = [primer_commit(str(p.relative_to(RAIZ)).replace("\\", "/")) for p in archivos_reales]
    t_logs = [t for t in t_logs if t is not None]
    if t_esp is None or not t_logs:
        informe("FALTA", "esperadas.md y la bitácora real deben estar en commits")
    else:
        informe("OK" if all(antes(t_esp, t) for t in t_logs) else "FALTA",
                "esperadas.md tiene un commit anterior a la bitácora real")

# 8. Traza y README
if (RAIZ / "traza_manual.md").exists():
    texto = (RAIZ / "traza_manual.md").read_text(encoding="utf-8", errors="ignore")
    informe("OK" if "(escriba aquí)" not in texto and len(texto) > 3000 else "FALTA",
            "traza_manual.md llena (sin marcas «(escriba aquí)»)")
if (RAIZ / "README.md").exists():
    texto = (RAIZ / "README.md").read_text(encoding="utf-8", errors="ignore")
    informe("OK" if "COMPLETAR" not in texto else "FALTA", "README.md sin marcas COMPLETAR de la plantilla")
if es_repo:
    n = len((git("log", "--format=%h") or "").splitlines())
    informe("OK" if n >= 5 else "AVISO", "%d commits en el historial (se esperan varios)" % n)

print()
print("Resultado: %d OK, %d FALTA, %d AVISO" % (resultados.count("OK"), resultados.count("FALTA"), resultados.count("AVISO")))
sys.exit(1 if "FALTA" in resultados else 0)
