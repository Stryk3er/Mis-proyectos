"""
Mini-SIEM - Módulo 1: Recolector de Logs
Autor: Julian Eduardo
Descripción: Recolecta eventos de seguridad del Event Log de Windows
             y los almacena en una base de datos SQLite local.
             Incluye extracción de IP de origen para eventos de login.
"""

import sqlite3
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

# Índices de IP y usuario en StringInserts por EventID
# Referencia: https://docs.microsoft.com/en-us/windows/security/threat-protection/auditing/
INDICES_EVENTO = {
    4624: {"usuario": 5,  "ip": 18},  # Logon exitoso
    4625: {"usuario": 5,  "ip": 19},  # Logon fallido
    4648: {"usuario": 1,  "ip": 12},  # Logon con credenciales explícitas
    4634: {"usuario": 1,  "ip": None},
    4672: {"usuario": 1,  "ip": None},
    4688: {"usuario": 1,  "ip": None},
    4698: {"usuario": 1,  "ip": None},
    4720: {"usuario": 0,  "ip": None},
    4726: {"usuario": 0,  "ip": None},
    4740: {"usuario": 0,  "ip": None},
    7045: {"usuario": 0,  "ip": None},
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
            ip_origen   TEXT,
            raw_data    TEXT
        )
    """)
    # Agregar columna ip_origen si ya existía la tabla sin ella
    try:
        cursor.execute("ALTER TABLE eventos ADD COLUMN ip_origen TEXT")
    except Exception:
        pass  # Ya existe
    conn.commit()
    conn.close()
    print(f"[+] Base de datos inicializada: {DB_PATH}")

def guardar_evento(timestamp, event_id, descripcion, usuario, computador, nivel, ip_origen="N/A", raw=""):
    """Inserta un evento en la base de datos."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO eventos (timestamp, event_id, descripcion, usuario, computador, nivel, ip_origen, raw_data)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (timestamp, event_id, descripcion, usuario, computador, nivel, ip_origen, raw))
    conn.commit()
    conn.close()

# ── Extracción de campos del Event Log ───────────────────────────────────────
def extraer_campo(inserts, indice, default="N/A"):
    """Extrae un campo de StringInserts de forma segura."""
    if not inserts or indice is None:
        return default
    try:
        valor = inserts[indice] if indice < len(inserts) else default
        return valor if valor and valor.strip() not in ("", "-", "%%1833") else default
    except Exception:
        return default

def es_ip_valida(ip):
    """Filtra IPs vacías, locales irrelevantes o placeholders."""
    if not ip or ip in ("N/A", "-", "::1", "127.0.0.1", "%%1833"):
        return False
    return True

# ── Recolección de logs ───────────────────────────────────────────────────────
def recolectar_logs_windows(max_eventos=100):
    """Lee los últimos eventos del Security Event Log de Windows en lotes pequeños."""
    if not WINDOWS_AVAILABLE:
        print("[-] pywin32 no instalado. Corriendo en modo simulación.")
        return False

    print(f"[*] Leyendo últimos {max_eventos} eventos de seguridad...")
    try:
        hand  = win32evtlog.OpenEventLog(None, "Security")
        flags = win32evtlog.EVENTLOG_BACKWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ

        conteo = 0
        while conteo < max_eventos:
            lote = win32evtlog.ReadEventLog(hand, flags, 0)
            if not lote:
                break

            for evento in lote:
                if conteo >= max_eventos:
                    break

                event_id = evento.EventID & 0xFFFF
                if event_id not in EVENTOS_CRITICOS:
                    continue

                inserts    = evento.StringInserts
                indices    = INDICES_EVENTO.get(event_id, {"usuario": 0, "ip": None})
                timestamp  = evento.TimeGenerated.Format()
                usuario    = extraer_campo(inserts, indices["usuario"])
                computador = evento.ComputerName
                nivel      = "CRITICO" if event_id in [4625, 4740, 7045] else "INFO"
                descripcion = EVENTOS_CRITICOS[event_id]
                ip_origen  = extraer_campo(inserts, indices["ip"])
                ip_origen  = ip_origen if es_ip_valida(ip_origen) else "Local"

                guardar_evento(timestamp, event_id, descripcion, usuario, computador, nivel, ip_origen)
                ip_str = f" | IP: {ip_origen}" if ip_origen != "Local" else ""
                print(f"  [{nivel}] {timestamp} | EventID {event_id} | {descripcion} | Usuario: {usuario}{ip_str}")
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
        ("2026-06-03 08:01:00", 4624, "Login exitoso",                  "julian.eduardo",  "LAPTOP-DEACERO", "INFO",    "192.168.1.105"),
        ("2026-06-03 08:15:00", 4625, "Login fallido",                   "admin",           "LAPTOP-DEACERO", "CRITICO", "10.0.0.47"),
        ("2026-06-03 08:15:10", 4625, "Login fallido",                   "admin",           "LAPTOP-DEACERO", "CRITICO", "10.0.0.47"),
        ("2026-06-03 08:15:20", 4625, "Login fallido",                   "admin",           "LAPTOP-DEACERO", "CRITICO", "10.0.0.47"),
        ("2026-06-03 08:16:00", 4740, "Cuenta bloqueada",                "admin",           "LAPTOP-DEACERO", "CRITICO", "Local"),
        ("2026-06-03 09:00:00", 4672, "Privilegios especiales asignados","julian.eduardo",  "LAPTOP-DEACERO", "INFO",    "Local"),
        ("2026-06-03 09:30:00", 4688, "Nuevo proceso creado",            "SYSTEM",          "LAPTOP-DEACERO", "INFO",    "Local"),
        ("2026-06-03 10:00:00", 4720, "Cuenta de usuario creada",        "julian.eduardo",  "LAPTOP-DEACERO", "INFO",    "Local"),
        ("2026-06-03 11:00:00", 7045, "Nuevo servicio instalado",        "SYSTEM",          "LAPTOP-DEACERO", "CRITICO", "Local"),
        ("2026-06-03 11:30:00", 4648, "Login con credenciales explícitas","julian.eduardo", "LAPTOP-DEACERO", "INFO",    "172.16.0.23"),
    ]
    for ev in eventos_demo:
        guardar_evento(*ev)
        ip_str = f" | IP: {ev[6]}" if ev[6] != "Local" else ""
        print(f"  [{ev[5]}] {ev[0]} | EventID {ev[1]} | {ev[2]} | Usuario: {ev[3]}{ip_str}")
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

    cursor.execute("""
        SELECT ip_origen, COUNT(*) as total FROM eventos
        WHERE ip_origen NOT IN ('Local', 'N/A')
        GROUP BY ip_origen ORDER BY total DESC LIMIT 5
    """)
    top_ips = cursor.fetchall()

    conn.close()

    print("\n" + "="*55)
    print("              RESUMEN MINI-SIEM")
    print("="*55)
    print(f"  Total eventos:    {total}")
    print(f"  Eventos críticos: {criticos}")
    print("\n  Top eventos detectados:")
    for ev in top_eventos:
        print(f"    EventID {ev[0]} | {ev[1]:<35} | {ev[2]}x")
    if top_ips:
        print("\n  Top IPs de origen:")
        for ip in top_ips:
            print(f"    {ip[0]:<20} | {ip[1]}x")
    print("="*55)

# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n🔐 Mini-SIEM - Recolector de Logs v2.0")
    print("="*55)

    inicializar_db()

    if not recolectar_logs_windows(max_eventos=50):
        simular_eventos()

    mostrar_resumen()
    print(f"\n[+] Datos guardados en: {os.path.abspath(DB_PATH)}")
    print("[*] Próximo módulo: Motor de alertas y detección de patrones\n")
