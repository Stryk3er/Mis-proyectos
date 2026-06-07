"""
Mini-SIEM - Módulo 6: Monitor Continuo
Autor: Julian Eduardo
Descripción: Orquesta la recolección de logs y el motor de alertas
             en un ciclo continuo. Diseñado para correr como tarea
             programada de Windows cada X minutos.

             Incluye auto-monitoreo: el sistema revisa su propio log
             en busca de errores y los reporta como eventos internos.
"""

import sys
import os
import re
import sqlite3
from datetime import datetime, timedelta

# Asegurar que los imports relativos funcionen desde cualquier ruta
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(SCRIPT_DIR)
sys.path.insert(0, SCRIPT_DIR)

from log_collector import inicializar_db, recolectar_logs_windows, simular_eventos, guardar_evento
from alert_engine  import inicializar_tabla_alertas, correr_motor
from notifier      import enviar_notificacion

# ── Configuración ─────────────────────────────────────────────────────────────
LOG_FILE          = "monitor.log"
MAX_LOG_LINES     = 10000   # Rotar log si supera este tamaño
VENTANA_AUTOCHECK = 30      # Minutos hacia atrás que revisa el auto-monitoreo

# Patrones que indican problemas en el log
PATRONES_ERROR = [
    (r"\[-\] Error",              "CRITICO", "Error crítico en el monitor"),
    (r"\[-\] No se encontró",     "MEDIA",   "Configuración faltante en el monitor"),
    (r"Traceback",                "CRITICO", "Excepción no manejada en el monitor"),
    (r"\[-\] pywin32 no",         "BAJA",    "pywin32 no disponible — corriendo en simulación"),
    (r"Error de autenticación",   "ALTA",    "Fallo de autenticación en notificaciones"),
]

# ── Logger simple ─────────────────────────────────────────────────────────────
def log(mensaje):
    """Escribe en consola y en archivo de log."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    linea = f"[{timestamp}] {mensaje}"
    print(linea)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(linea + "\n")

def rotar_log():
    """Si el log es muy grande, guarda una copia y lo reinicia."""
    if not os.path.exists(LOG_FILE):
        return
    with open(LOG_FILE, encoding="utf-8") as f:
        lineas = f.readlines()
    if len(lineas) > MAX_LOG_LINES:
        backup = LOG_FILE.replace(".log", f"_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
        os.rename(LOG_FILE, backup)
        log(f"Log rotado → {backup}")

# ── Auto-monitoreo ────────────────────────────────────────────────────────────
def analizar_log_propio():
    """
    Lee el monitor.log de los últimos VENTANA_AUTOCHECK minutos
    y busca patrones de error. Si encuentra alguno, lo guarda
    en la base de datos como evento interno del sistema.
    """
    if not os.path.exists(LOG_FILE):
        return

    ahora   = datetime.now()
    ventana = ahora - timedelta(minutes=VENTANA_AUTOCHECK)
    ts_fmt  = "%Y-%m-%d %H:%M:%S"

    problemas_encontrados = []

    with open(LOG_FILE, encoding="utf-8") as f:
        for linea in f:
            # Extraer timestamp de la línea: [2026-06-06 10:00:00]
            match_ts = re.match(r"\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]", linea)
            if not match_ts:
                continue
            try:
                ts_linea = datetime.strptime(match_ts.group(1), ts_fmt)
            except ValueError:
                continue

            if ts_linea < ventana:
                continue  # Fuera de la ventana de revisión

            for patron, nivel, descripcion in PATRONES_ERROR:
                if re.search(patron, linea):
                    problemas_encontrados.append((
                        ts_linea.strftime(ts_fmt),
                        9999,           # EventID interno del Mini-SIEM
                        descripcion,
                        "MINI-SIEM",
                        "LOCAL",
                        nivel,
                        "Local",
                        linea.strip()
                    ))
                    break  # Un match por línea es suficiente

    if problemas_encontrados:
        log(f"[AUTO-MONITOR] {len(problemas_encontrados)} problema(s) detectado(s) en el log del sistema.")
        conn = sqlite3.connect("siem_eventos.db")
        cursor = conn.cursor()
        for ev in problemas_encontrados:
            try:
                cursor.execute("""
                    INSERT INTO eventos
                    (timestamp, event_id, descripcion, usuario, computador, nivel, ip_origen, raw_data)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, ev)
                log(f"  [{ev[5]}] {ev[2]}")
            except Exception as e:
                log(f"  Error guardando evento interno: {e}")
        conn.commit()
        conn.close()
    else:
        log("[AUTO-MONITOR] Sin problemas detectados en el log del sistema.")

# ── Ciclo principal ───────────────────────────────────────────────────────────
def ejecutar_ciclo():
    """Un ciclo completo: recolectar → analizar → auto-monitoreo → notificar."""
    rotar_log()
    log("=" * 55)
    log("Mini-SIEM Monitor — Inicio de ciclo")

    # 1. Inicializar DB
    inicializar_db()
    inicializar_tabla_alertas()

    # 2. Recolectar logs
    log("Recolectando eventos del sistema...")
    exito = recolectar_logs_windows(max_eventos=100)
    if not exito:
        log("pywin32 no disponible — usando simulación")
        simular_eventos()

    # 3. Auto-monitoreo: revisar el log propio antes de analizar
    log("Ejecutando auto-monitoreo del sistema...")
    analizar_log_propio()

    # 4. Correr motor de alertas
    log("Ejecutando motor de alertas...")
    correr_motor()

    # 5. Enviar notificaciones si hay alertas críticas
    log("Verificando alertas para notificación...")
    enviar_notificacion()

    log("Ciclo completado.")
    log("=" * 55)

# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    ejecutar_ciclo()
