"""
Mini-SIEM - Módulo 1: Recolector de Logs
Autor: Julian Eduardo
Descripción: Recolecta eventos de seguridad del Event Log de Windows
             y los almacena en una base de datos SQLite local.
"""
 
import sqlite3
import json
import os
from datetime import datetime
 
# ── Intentar importar librería de Windows Event Log ──────────────────────────
try:
    import win32evtlog
    import win32evtlogutil
    import win32con
    WINDOWS_AVAILABLE = True
except ImportError:
    WINDOWS_AVAILABLE = False
 
# ── Configuración ─────────────────────────────────────────────────────────────
DB_PATH = "siem_eventos.db"
 
# IDs de eventos de seguridad importantes
EVENTOS_CRITICOS = {
    4624: "Login exitoso",
    4625: "Login fallido",
    4634: "Cierre de sesión",
    4648: "Login con credenciales explícitas",
    4672: "Privilegios especiales asignados",
    4688: "Nuevo proceso creado",
    4698: "Tarea programada creada",
    4720: "Cuenta de usuario creada",
    4726: "Cuenta de usuario eliminada",
    4740: "Cuenta bloqueada",
    7045: "Nuevo servicio instalado",
}
 
# ── Base de datos ─────────────────────────────────────────────────────────────
def inicializar_db():
    """Crea la base de datos y tabla de eventos si no existen."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS eventos (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp   TEXT NOT NULL,
            event_id    INTEGER,
            descripcion TEXT,
            usuario     TEXT,
            computador  TEXT,
            nivel       TEXT,
            raw_data    TEXT
        )
    """)
    conn.commit()
    conn.close()
    print(f"[+] Base de datos inicializada: {DB_PATH}")
 
def guardar_evento(timestamp, event_id, descripcion, usuario, computador, nivel, raw=""):
    """Inserta un evento en la base de datos."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO eventos (timestamp, event_id, descripcion, usuario, computador, nivel, raw_data)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (timestamp, event_id, descripcion, usuario, computador, nivel, raw))
    conn.commit()
    conn.close()
 
# ── Recolección de logs ───────────────────────────────────────────────────────
def recolectar_logs_windows(max_eventos=100):
    """Lee los últimos eventos del Security Event Log de Windows en lotes pequeños."""
    if not WINDOWS_AVAILABLE:
        print("[-] pywin32 no instalado. Corriendo en modo simulación.")
        return False
 
    print(f"[*] Leyendo últimos {max_eventos} eventos de seguridad...")
    try:
        hand = win32evtlog.OpenEventLog(None, "Security")
        flags = win32evtlog.EVENTLOG_BACKWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ
 
        conteo = 0
        # FIX: leer en lotes para evitar saturar la memoria RAM
        while conteo < max_eventos:
            lote = win32evtlog.ReadEventLog(hand, flags, 0)
            if not lote:
                break  # No hay más eventos
 
            for evento in lote:
                if conteo >= max_eventos:
                    break
 
                event_id = evento.EventID & 0xFFFF
                if event_id in EVENTOS_CRITICOS:
                    timestamp = evento.TimeGenerated.Format()
                    usuario = evento.StringInserts[0] if evento.StringInserts else "N/A"
                    computador = evento.ComputerName
                    nivel = "CRITICO" if event_id in [4625, 4740, 7045] else "INFO"
                    descripcion = EVENTOS_CRITICOS.get(event_id, "Evento desconocido")
 
                    guardar_evento(timestamp, event_id, descripcion, usuario, computador, nivel)
                    print(f"  [{nivel}] {timestamp} | EventID {event_id} | {descripcion} | Usuario: {usuario}")
                    conteo += 1
 
        win32evtlog.CloseEventLog(hand)
        print(f"[+] {conteo} eventos recolectados y guardados.")
        return True
 
    except Exception as e:
        print(f"[-] Error leyendo Event Log: {e}")
        print("    Asegúrate de correr el script como Administrador.")
        return False
 
def simular_eventos():
    """Genera eventos de prueba para desarrollo/demo."""
    print("[*] Generando eventos simulados para demo...")
    eventos_demo = [
        ("2026-06-03 08:01:00", 4624, "Login exitoso",                  "julian.eduardo",  "LAPTOP-DEACERO", "INFO"),
        ("2026-06-03 08:15:00", 4625, "Login fallido",                   "admin",           "LAPTOP-DEACERO", "CRITICO"),
        ("2026-06-03 08:15:10", 4625, "Login fallido",                   "admin",           "LAPTOP-DEACERO", "CRITICO"),
        ("2026-06-03 08:15:20", 4625, "Login fallido",                   "admin",           "LAPTOP-DEACERO", "CRITICO"),
        ("2026-06-03 08:16:00", 4740, "Cuenta bloqueada",                "admin",           "LAPTOP-DEACERO", "CRITICO"),
        ("2026-06-03 09:00:00", 4672, "Privilegios especiales asignados","julian.eduardo",  "LAPTOP-DEACERO", "INFO"),
        ("2026-06-03 09:30:00", 4688, "Nuevo proceso creado",            "SYSTEM",          "LAPTOP-DEACERO", "INFO"),
        ("2026-06-03 10:00:00", 4720, "Cuenta de usuario creada",        "julian.eduardo",  "LAPTOP-DEACERO", "INFO"),
        ("2026-06-03 11:00:00", 7045, "Nuevo servicio instalado",        "SYSTEM",          "LAPTOP-DEACERO", "CRITICO"),
        ("2026-06-03 11:30:00", 4648, "Login con credenciales explícitas","julian.eduardo", "LAPTOP-DEACERO", "INFO"),
    ]
    for ev in eventos_demo:
        guardar_evento(*ev)
        print(f"  [{ev[5]}] {ev[0]} | EventID {ev[1]} | {ev[2]} | Usuario: {ev[3]}")
    print(f"[+] {len(eventos_demo)} eventos simulados guardados.")
 
# ── Resumen de eventos ────────────────────────────────────────────────────────
def mostrar_resumen():
    """Muestra estadísticas básicas de los eventos recolectados."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
 
    cursor.execute("SELECT COUNT(*) FROM eventos")
    total = cursor.fetchone()[0]
 
    cursor.execute("SELECT COUNT(*) FROM eventos WHERE nivel = 'CRITICO'")
    criticos = cursor.fetchone()[0]
 
    cursor.execute("""
        SELECT event_id, descripcion, COUNT(*) as total
        FROM eventos GROUP BY event_id ORDER BY total DESC LIMIT 5
    """)
    top_eventos = cursor.fetchall()
 
    conn.close()
 
    print("\n" + "="*50)
    print("         RESUMEN MINI-SIEM")
    print("="*50)
    print(f"  Total eventos:    {total}")
    print(f"  Eventos críticos: {criticos}")
    print("\n  Top eventos detectados:")
    for ev in top_eventos:
        print(f"    EventID {ev[0]} | {ev[1]:<35} | {ev[2]}x")
    print("="*50)
 
# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n🔐 Mini-SIEM - Recolector de Logs v1.0")
    print("="*50)
 
    inicializar_db()
 
    # Intenta leer logs reales; si falla, usa simulación
    if not recolectar_logs_windows(max_eventos=50):
        simular_eventos()
 
    mostrar_resumen()
    print(f"\n[+] Datos guardados en: {os.path.abspath(DB_PATH)}")
    print("[*] Próximo módulo: Motor de alertas y detección de patrones\n")