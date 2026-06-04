"""
Mini-SIEM - Módulo 2: Motor de Alertas
Autor: Julian Eduardo
Descripción: Analiza eventos recolectados y detecta patrones sospechosos,
             generando alertas con nivel de severidad.
"""

import sqlite3
from datetime import datetime, timedelta

DB_PATH = "siem_eventos.db"

# ── Base de datos ─────────────────────────────────────────────────────────────
def inicializar_tabla_alertas():
    """Crea la tabla de alertas si no existe."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alertas (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp   TEXT NOT NULL,
            tipo        TEXT,
            severidad   TEXT,
            usuario     TEXT,
            computador  TEXT,
            detalle     TEXT
        )
    """)
    conn.commit()
    conn.close()
    print("[+] Tabla de alertas inicializada.")

def guardar_alerta(tipo, severidad, usuario, computador, detalle):
    """Inserta una alerta en la base de datos."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO alertas (timestamp, tipo, severidad, usuario, computador, detalle)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (timestamp, tipo, severidad, usuario, computador, detalle))
    conn.commit()
    conn.close()

def obtener_eventos():
    """Recupera todos los eventos de la base de datos."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT timestamp, event_id, descripcion, usuario, computador, nivel FROM eventos ORDER BY timestamp")
    eventos = cursor.fetchall()
    conn.close()
    return eventos

# ── Reglas de detección ───────────────────────────────────────────────────────
def detectar_fuerza_bruta(eventos, umbral=3, ventana_minutos=1):
    """
    Detecta múltiples logins fallidos (4625) del mismo usuario
    en una ventana de tiempo corta.
    """
    alertas = []
    fallidos = {}  # {usuario: [timestamps]}

    for ev in eventos:
        timestamp, event_id, _, usuario, computador, _ = ev
        if event_id != 4625:
            continue

        try:
            ts = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            # Formato alternativo del Event Log real de Windows
            try:
                ts = datetime.strptime(timestamp, "%c")
            except ValueError:
                continue

        if usuario not in fallidos:
            fallidos[usuario] = []
        fallidos[usuario].append((ts, computador))

    for usuario, intentos in fallidos.items():
        intentos.sort()
        for i in range(len(intentos) - umbral + 1):
            t_inicio = intentos[i][0]
            t_fin = intentos[i + umbral - 1][0]
            if (t_fin - t_inicio).total_seconds() <= ventana_minutos * 60:
                computador = intentos[i][1]
                detalle = (f"{umbral} logins fallidos en "
                           f"{(t_fin - t_inicio).total_seconds():.0f}s "
                           f"entre {t_inicio} y {t_fin}")
                alertas.append(("FUERZA BRUTA", "ALTA", usuario, computador, detalle))
                break  # Una alerta por usuario es suficiente

    return alertas

def detectar_bloqueo_tras_fuerza_bruta(eventos):
    """
    Detecta cuenta bloqueada (4740) precedida de logins fallidos (4625).
    """
    alertas = []
    usuarios_con_fallos = set()

    for ev in eventos:
        _, event_id, _, usuario, computador, _ = ev
        if event_id == 4625:
            usuarios_con_fallos.add(usuario)
        elif event_id == 4740 and usuario in usuarios_con_fallos:
            detalle = f"Cuenta bloqueada tras múltiples logins fallidos en {computador}"
            alertas.append(("CUENTA BLOQUEADA POST ATAQUE", "CRITICA", usuario, computador, detalle))

    return alertas

def detectar_servicio_nuevo(eventos):
    """
    Alerta inmediata por instalación de nuevo servicio (7045).
    Puede indicar persistencia de malware.
    """
    alertas = []
    for ev in eventos:
        timestamp, event_id, _, usuario, computador, _ = ev
        if event_id == 7045:
            detalle = f"Nuevo servicio instalado a las {timestamp} por {usuario}"
            alertas.append(("SERVICIO NUEVO INSTALADO", "CRITICA", usuario, computador, detalle))
    return alertas

def detectar_privilegios_fuera_horario(eventos, hora_inicio=22, hora_fin=6):
    """
    Detecta privilegios especiales (4672) asignados fuera del horario laboral.
    """
    alertas = []
    for ev in eventos:
        timestamp, event_id, _, usuario, computador, _ = ev
        if event_id != 4672:
            continue

        try:
            ts = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            try:
                ts = datetime.strptime(timestamp, "%c")
            except ValueError:
                continue

        hora = ts.hour
        if hora >= hora_inicio or hora < hora_fin:
            detalle = f"Privilegios elevados asignados a las {ts.strftime('%H:%M')} (fuera de horario)"
            alertas.append(("PRIVILEGIOS FUERA DE HORARIO", "MEDIA", usuario, computador, detalle))

    return alertas

# ── Motor principal ───────────────────────────────────────────────────────────
def correr_motor():
    """Ejecuta todas las reglas de detección y guarda las alertas."""
    print("\n🔍 Mini-SIEM - Motor de Alertas v1.0")
    print("=" * 50)

    inicializar_tabla_alertas()
    eventos = obtener_eventos()
    print(f"[*] Analizando {len(eventos)} eventos...")

    todas_alertas = []
    todas_alertas += detectar_fuerza_bruta(eventos)
    todas_alertas += detectar_bloqueo_tras_fuerza_bruta(eventos)
    todas_alertas += detectar_servicio_nuevo(eventos)
    todas_alertas += detectar_privilegios_fuera_horario(eventos)

    if not todas_alertas:
        print("[+] Sin alertas detectadas.")
    else:
        print(f"\n⚠️  {len(todas_alertas)} ALERTA(S) DETECTADA(S):\n")
        for alerta in todas_alertas:
            tipo, severidad, usuario, computador, detalle = alerta
            guardar_alerta(*alerta)
            print(f"  [{severidad}] {tipo}")
            print(f"           Usuario:    {usuario}")
            print(f"           Equipo:     {computador}")
            print(f"           Detalle:    {detalle}")
            print()

    print("=" * 50)
    print(f"[+] Alertas guardadas en: {DB_PATH}")
    print("[*] Próximo módulo: Dashboard visual\n")

# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    correr_motor()
