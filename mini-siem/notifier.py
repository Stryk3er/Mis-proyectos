"""
Mini-SIEM - Módulo 4: Notificaciones por Correo
Autor: Julian Eduardo
Descripción: Envía alertas críticas por email usando Gmail.
             Las credenciales se leen del archivo .env (nunca en el código).
"""

import smtplib
import sqlite3
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

DB_PATH = "siem_eventos.db"

# ── Cargar credenciales desde .env ────────────────────────────────────────────
def cargar_env(path=".env"):
    """Lee el archivo .env y carga las variables en el entorno."""
    if not os.path.exists(path):
        print(f"[-] Archivo {path} no encontrado.")
        return False
    with open(path) as f:
        for linea in f:
            linea = linea.strip()
            if not linea or linea.startswith("#"):
                continue
            if "=" in linea:
                clave, valor = linea.split("=", 1)
                os.environ[clave.strip()] = valor.strip().replace(" ", "")
    return True

# ── Obtener alertas nuevas ────────────────────────────────────────────────────
def obtener_alertas_criticas():
    """Recupera alertas CRITICAS y ALTA de la base de datos."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT * FROM alertas
            WHERE severidad IN ('CRITICA', 'ALTA')
            ORDER BY timestamp DESC
            LIMIT 20
        """)
        alertas = [dict(r) for r in cursor.fetchall()]
    except Exception:
        alertas = []
    conn.close()
    return alertas

# ── Construir el email ────────────────────────────────────────────────────────
def construir_email(alertas, remitente, destinatario):
    """Genera el mensaje de email con las alertas en formato HTML."""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"🚨 Mini-SIEM — {len(alertas)} Alerta(s) Detectada(s)"
    msg["From"]    = remitente
    msg["To"]      = destinatario

    colores = {
        "CRITICA": "#f85149",
        "ALTA":    "#f0883e",
        "MEDIA":   "#e3b341",
        "BAJA":    "#3fb950",
    }

    filas = ""
    for a in alertas:
        color = colores.get(a["severidad"], "#8b949e")
        filas += f"""
        <tr>
            <td style="padding:8px;border-bottom:1px solid #30363d;">{a['timestamp']}</td>
            <td style="padding:8px;border-bottom:1px solid #30363d;">{a['tipo']}</td>
            <td style="padding:8px;border-bottom:1px solid #30363d;">
                <span style="color:{color};font-weight:bold;">{a['severidad']}</span>
            </td>
            <td style="padding:8px;border-bottom:1px solid #30363d;">{a['usuario']}</td>
            <td style="padding:8px;border-bottom:1px solid #30363d;">{a['computador']}</td>
            <td style="padding:8px;border-bottom:1px solid #30363d;">{a['detalle']}</td>
        </tr>"""

    html = f"""
    <html><body style="background:#0d1117;color:#c9d1d9;font-family:Segoe UI,sans-serif;padding:24px;">
        <h2 style="color:#58a6ff;">🔐 Mini-SIEM — Reporte de Alertas</h2>
        <p style="color:#8b949e;">Generado el {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <table style="width:100%;border-collapse:collapse;font-size:13px;">
            <thead>
                <tr style="color:#8b949e;text-align:left;">
                    <th style="padding:8px;">Timestamp</th>
                    <th style="padding:8px;">Tipo</th>
                    <th style="padding:8px;">Severidad</th>
                    <th style="padding:8px;">Usuario</th>
                    <th style="padding:8px;">Equipo</th>
                    <th style="padding:8px;">Detalle</th>
                </tr>
            </thead>
            <tbody>{filas}</tbody>
        </table>
        <p style="color:#8b949e;font-size:11px;margin-top:24px;">
            Mini-SIEM · Autor: Julian Eduardo · Este es un mensaje automático.
        </p>
    </body></html>
    """

    msg.attach(MIMEText(html, "html"))
    return msg

# ── Enviar email ──────────────────────────────────────────────────────────────
def enviar_notificacion():
    """Carga credenciales, obtiene alertas y envía el correo."""
    print("\n📧 Mini-SIEM - Módulo de Notificaciones v1.0")
    print("=" * 50)

    # Buscar .env en la carpeta actual o en mini-siem/
    if not cargar_env(".env") and not cargar_env("mini-siem/.env"):
        print("[-] No se encontró el archivo .env")
        print("    Crea mini-siem/.env con EMAIL_REMITENTE, EMAIL_PASSWORD y EMAIL_DESTINATARIO")
        return

    remitente    = os.environ.get("EMAIL_REMITENTE")
    password     = os.environ.get("EMAIL_PASSWORD")
    destinatario = os.environ.get("EMAIL_DESTINATARIO")

    if not all([remitente, password, destinatario]):
        print("[-] Faltan variables en el archivo .env")
        return

    alertas = obtener_alertas_criticas()
    if not alertas:
        print("[+] Sin alertas críticas para notificar.")
        return

    print(f"[*] Enviando {len(alertas)} alerta(s) a {destinatario}...")

    try:
        msg = construir_email(alertas, remitente, destinatario)
        with smtplib.SMTP("smtp.gmail.com", 587) as servidor:
            servidor.starttls()
            servidor.login(remitente, password)
            servidor.sendmail(remitente, destinatario, msg.as_string())
        print(f"[+] Correo enviado exitosamente a {destinatario}")
    except smtplib.SMTPAuthenticationError:
        print("[-] Error de autenticación — verifica EMAIL_REMITENTE y EMAIL_PASSWORD en .env")
    except Exception as e:
        print(f"[-] Error al enviar correo: {e}")

    print("=" * 50)

# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    enviar_notificacion()
