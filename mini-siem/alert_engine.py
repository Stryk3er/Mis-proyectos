"""
Mini-SIEM - Módulo 2: Motor de Alertas
Autor: Julian Eduardo
Descripción: Analiza eventos recolectados y detecta patrones sospechosos,
             generando alertas con nivel de severidad.
             Soporta configuración de umbrales y whitelist de usuarios.
"""

import sqlite3
from datetime import datetime

DB_PATH = "siem_eventos.db"

# ── Configuración de umbrales (ajustable sin tocar el código) ─────────────────
CONFIG = {
    # Fuerza bruta: número de fallos y ventana de tiempo
    "fuerza_bruta_umbral": 5,          # intentos fallidos para disparar alerta
    "fuerza_bruta_ventana_min": 5,     # ventana de tiempo en minutos
    "fuerza_bruta_severidad_baja": 3,  # fallos para alerta MEDIA (usuario olvidadizo)

    # Horario laboral (fuera de este rango = sospechoso)
    "hora_inicio_laboral": 7,
    "hora_fin_laboral": 22,

    # Whitelist: usuarios que NUNCA generan alerta de fuerza bruta
    # (ej. cuentas de servicio o usuarios con historial de olvidos frecuentes)
    "whitelist_usuarios": [
        "SYSTEM",
        "S-1-5-18",
    ],
}

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

def parsear_timestamp(timestamp):
    """Intenta parsear el timestamp en múltiples formatos."""
    for fmt in ("%Y-%m-%d %H:%M:%S", "%c"):
        try:
            return datetime.strptime(timestamp, fmt)
        except ValueError:
            continue
    return None

# ── Reglas de detección ───────────────────────────────────────────────────────
def detectar_fuerza_bruta(eventos):
    """
    Detecta múltiples logins fallidos (4625) del mismo usuario.

    - Si supera fuerza_bruta_umbral en la ventana → alerta ALTA
    - Si supera fuerza_bruta_severidad_baja pero no el umbral alto → alerta MEDIA
      (posible usuario olvidadizo, requiere revisión humana antes de actuar)
    - Usuarios en whitelist son ignorados
    """
    umbral_alto  = CONFIG["fuerza_bruta_umbral"]
    umbral_bajo  = CONFIG["fuerza_bruta_severidad_baja"]
    ventana_min  = CONFIG["fuerza_bruta_ventana_min"]
    whitelist    = CONFIG["whitelist_usuarios"]

    alertas  = []
    fallidos = {}  # {usuario: [(ts, computador)]}

    for ev in eventos:
        timestamp, event_id, _, usuario, computador, _ = ev
        if event_id != 4625:
            continue
        if usuario in whitelist:
            continue

        ts = parsear_timestamp(timestamp)
        if ts is None:
            continue

        fallidos.setdefault(usuario, []).append((ts, computador))

    for usuario, intentos in fallidos.items():
        intentos.sort()

        # Buscar ventana con umbral alto (ALTA)
        alerta_generada = False
        for i in range(len(intentos) - umbral_alto + 1):
            t_inicio = intentos[i][0]
            t_fin    = intentos[i + umbral_alto - 1][0]
            if (t_fin - t_inicio).total_seconds() <= ventana_min * 60:
                detalle = (f"{umbral_alto} logins fallidos en "
                           f"{(t_fin - t_inicio).total_seconds():.0f}s — "
                           f"posible ataque automatizado")
                alertas.append(("FUERZA BRUTA", "ALTA", usuario, intentos[i][1], detalle))
                alerta_generada = True
                break

        # Si no llegó al umbral alto pero sí al bajo → alerta MEDIA (usuario olvidadizo)
        if not alerta_generada and len(intentos) >= umbral_bajo:
            for i in range(len(intentos) - umbral_bajo + 1):
                t_inicio = intentos[i][0]
                t_fin    = intentos[i + umbral_bajo - 1][0]
                if (t_fin - t_inicio).total_seconds() <= ventana_min * 60:
                    detalle = (f"{len(intentos)} logins fallidos detectados — "
                               f"puede ser usuario olvidadizo, revisar antes de actuar")
                    alertas.append(("POSIBLE USUARIO OLVIDADIZO", "MEDIA", usuario, intentos[i][1], detalle))
                    break

    return alertas

def detectar_bloqueo_tras_fuerza_bruta(eventos):
    """
    Detecta cuenta bloqueada (4740) precedida de logins fallidos (4625).
    """
    alertas = []
    usuarios_con_fallos = set()

    for ev in eventos:
        _, event_id, _, usuario, computador, _ = ev
        if usuario in CONFIG["whitelist_usuarios"]:
            continue
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

def detectar_privilegios_fuera_horario(eventos):
    """
    Detecta privilegios especiales (4672) asignados fuera del horario laboral.
    """
    hora_inicio = CONFIG["hora_inicio_laboral"]
    hora_fin    = CONFIG["hora_fin_laboral"]
    alertas     = []

    for ev in eventos:
        timestamp, event_id, _, usuario, computador, _ = ev
        if event_id != 4672:
            continue
        if usuario in CONFIG["whitelist_usuarios"]:
            continue

        ts = parsear_timestamp(timestamp)
        if ts is None:
            continue

        hora = ts.hour
        if hora < hora_inicio or hora >= hora_fin:
            detalle = f"Privilegios elevados asignados a las {ts.strftime('%H:%M')} (fuera de horario laboral)"
            alertas.append(("PRIVILEGIOS FUERA DE HORARIO", "MEDIA", usuario, computador, detalle))

    return alertas

# ── Motor principal ───────────────────────────────────────────────────────────
def correr_motor():
    """Ejecuta todas las reglas de detección y guarda las alertas."""
    print("\n🔍 Mini-SIEM - Motor de Alertas v2.0")
    print("=" * 50)
    print(f"  Umbral fuerza bruta:  {CONFIG['fuerza_bruta_umbral']} fallos / {CONFIG['fuerza_bruta_ventana_min']} min")
    print(f"  Umbral usuario olvid: {CONFIG['fuerza_bruta_severidad_baja']} fallos (alerta MEDIA)")
    print(f"  Horario laboral:      {CONFIG['hora_inicio_laboral']}:00 - {CONFIG['hora_fin_laboral']}:00")
    print(f"  Whitelist:            {', '.join(CONFIG['whitelist_usuarios'])}")
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
