"""
Mini-SIEM - Módulo 5: Generador de Reporte PDF
Autor: Julian Eduardo
Descripción: Genera un reporte PDF diario con resumen de eventos y alertas.
"""

import sqlite3
from datetime import datetime
import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)

DB_PATH = "siem_eventos.db"

# ── Paleta de colores ─────────────────────────────────────────────────────────
COLOR_BG       = colors.HexColor("#0d1117")
COLOR_AZUL     = colors.HexColor("#58a6ff")
COLOR_ROJO     = colors.HexColor("#f85149")
COLOR_NARANJA  = colors.HexColor("#f0883e")
COLOR_AMARILLO = colors.HexColor("#e3b341")
COLOR_VERDE    = colors.HexColor("#3fb950")
COLOR_GRIS     = colors.HexColor("#8b949e")
COLOR_FILA     = colors.HexColor("#161b22")
COLOR_BORDE    = colors.HexColor("#30363d")

SEVERIDAD_COLOR = {
    "CRITICA": COLOR_ROJO,
    "ALTA":    COLOR_NARANJA,
    "MEDIA":   COLOR_AMARILLO,
    "BAJA":    COLOR_VERDE,
    "INFO":    COLOR_AZUL,
}

# ── Consultas ─────────────────────────────────────────────────────────────────
def get_stats():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM eventos")
    total = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM eventos WHERE nivel='CRITICO'")
    criticos = cursor.fetchone()[0]
    try:
        cursor.execute("SELECT COUNT(*) FROM alertas")
        alertas = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM alertas WHERE severidad='CRITICA'")
        a_criticas = cursor.fetchone()[0]
    except Exception:
        alertas = a_criticas = 0
    conn.close()
    return total, criticos, alertas, a_criticas

def get_alertas():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM alertas ORDER BY timestamp DESC LIMIT 30")
        rows = [dict(r) for r in cursor.fetchall()]
    except Exception:
        rows = []
    conn.close()
    return rows

def get_top_eventos():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT event_id, descripcion, COUNT(*) as total
        FROM eventos GROUP BY event_id ORDER BY total DESC LIMIT 8
    """)
    rows = cursor.fetchall()
    conn.close()
    return rows

# ── Estilos ───────────────────────────────────────────────────────────────────
def estilos():
    base = getSampleStyleSheet()
    return {
        "titulo": ParagraphStyle("titulo",
            fontSize=22, textColor=COLOR_AZUL, spaceAfter=4,
            fontName="Helvetica-Bold"),
        "subtitulo": ParagraphStyle("subtitulo",
            fontSize=10, textColor=COLOR_GRIS, spaceAfter=16,
            fontName="Helvetica"),
        "seccion": ParagraphStyle("seccion",
            fontSize=11, textColor=COLOR_GRIS, spaceBefore=20, spaceAfter=8,
            fontName="Helvetica-Bold"),
        "normal": ParagraphStyle("normal",
            fontSize=9, textColor=colors.white,
            fontName="Helvetica"),
        "pie": ParagraphStyle("pie",
            fontSize=8, textColor=COLOR_GRIS, alignment=1,
            fontName="Helvetica"),
    }

# ── Tabla de resumen ──────────────────────────────────────────────────────────
def tabla_resumen(total, criticos, alertas, a_criticas):
    data = [
        ["Total Eventos", "Eventos Críticos", "Alertas Generadas", "Alertas Críticas"],
        [str(total), str(criticos), str(alertas), str(a_criticas)],
    ]
    t = Table(data, colWidths=[1.6*inch]*4)
    t.setStyle(TableStyle([
        ("BACKGROUND",   (0,0), (-1,0), COLOR_FILA),
        ("BACKGROUND",   (0,1), (-1,1), COLOR_BG),
        ("TEXTCOLOR",    (0,0), (-1,0), COLOR_GRIS),
        ("TEXTCOLOR",    (0,1), (0,1),  COLOR_AZUL),
        ("TEXTCOLOR",    (1,1), (1,1),  COLOR_ROJO),
        ("TEXTCOLOR",    (2,1), (2,1),  COLOR_NARANJA),
        ("TEXTCOLOR",    (3,1), (3,1),  COLOR_ROJO),
        ("FONTNAME",     (0,0), (-1,0), "Helvetica"),
        ("FONTNAME",     (0,1), (-1,1), "Helvetica-Bold"),
        ("FONTSIZE",     (0,0), (-1,0), 8),
        ("FONTSIZE",     (0,1), (-1,1), 20),
        ("ALIGN",        (0,0), (-1,-1), "CENTER"),
        ("VALIGN",       (0,0), (-1,-1), "MIDDLE"),
        ("ROWHEIGHT",    (0,0), (-1,-1), 30),
        ("GRID",         (0,0), (-1,-1), 0.5, COLOR_BORDE),
        ("TOPPADDING",   (0,1), (-1,1), 8),
        ("BOTTOMPADDING",(0,1), (-1,1), 8),
    ]))
    return t

# ── Tabla de alertas ──────────────────────────────────────────────────────────
def tabla_alertas(alertas, est):
    encabezado = ["Timestamp", "Tipo", "Severidad", "Usuario", "Equipo"]
    filas = [encabezado]
    for a in alertas:
        filas.append([
            a.get("timestamp","")[:16],
            a.get("tipo",""),
            a.get("severidad",""),
            a.get("usuario","")[:20],
            a.get("computador","")[:20],
        ])

    anchos = [1.3*inch, 1.8*inch, 0.9*inch, 1.2*inch, 1.3*inch]
    t = Table(filas, colWidths=anchos, repeatRows=1)

    style = [
        ("BACKGROUND",   (0,0), (-1,0), COLOR_FILA),
        ("TEXTCOLOR",    (0,0), (-1,0), COLOR_GRIS),
        ("FONTNAME",     (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",     (0,0), (-1,-1), 8),
        ("FONTNAME",     (0,1), (-1,-1), "Helvetica"),
        ("TEXTCOLOR",    (0,1), (-1,-1), colors.white),
        ("ROWBACKGROUNDS",(0,1),(-1,-1), [COLOR_BG, COLOR_FILA]),
        ("GRID",         (0,0), (-1,-1), 0.3, COLOR_BORDE),
        ("ALIGN",        (0,0), (-1,-1), "LEFT"),
        ("VALIGN",       (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING",   (0,0), (-1,-1), 5),
        ("BOTTOMPADDING",(0,0), (-1,-1), 5),
    ]

    # Color por severidad en la columna Severidad
    for i, a in enumerate(alertas, start=1):
        sev = a.get("severidad","")
        color = SEVERIDAD_COLOR.get(sev, COLOR_GRIS)
        style.append(("TEXTCOLOR", (2,i), (2,i), color))
        style.append(("FONTNAME",  (2,i), (2,i), "Helvetica-Bold"))

    t.setStyle(TableStyle(style))
    return t

# ── Tabla top eventos ─────────────────────────────────────────────────────────
def tabla_top_eventos(top):
    encabezado = ["Event ID", "Descripción", "Ocurrencias"]
    filas = [encabezado] + [[str(r[0]), r[1], str(r[2])] for r in top]
    anchos = [1*inch, 4*inch, 1.5*inch]
    t = Table(filas, colWidths=anchos, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0), COLOR_FILA),
        ("TEXTCOLOR",     (0,0), (-1,0), COLOR_GRIS),
        ("FONTNAME",      (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",      (0,0), (-1,-1), 8),
        ("FONTNAME",      (0,1), (-1,-1), "Helvetica"),
        ("TEXTCOLOR",     (0,1), (-1,-1), colors.white),
        ("ROWBACKGROUNDS",(0,1),(-1,-1), [COLOR_BG, COLOR_FILA]),
        ("GRID",          (0,0), (-1,-1), 0.3, COLOR_BORDE),
        ("ALIGN",         (2,0), (2,-1), "CENTER"),
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING",    (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
    ]))
    return t

# ── Generar PDF ───────────────────────────────────────────────────────────────
def generar_reporte():
    fecha = datetime.now().strftime("%Y-%m-%d")
    os.makedirs("reportes", exist_ok=True)
    nombre_archivo = f"reportes/reporte_siem_{fecha}.pdf"

    print(f"\n📄 Mini-SIEM - Generador de Reporte PDF v1.0")
    print("=" * 50)

    doc = SimpleDocTemplate(
        nombre_archivo,
        pagesize=letter,
        leftMargin=0.75*inch, rightMargin=0.75*inch,
        topMargin=0.75*inch,  bottomMargin=0.75*inch,
    )

    est   = estilos()
    story = []

    # Encabezado
    story.append(Paragraph("Mini-SIEM — Reporte de Seguridad", est["titulo"]))
    story.append(Paragraph(f"Generado el {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  |  Autor: Julian Eduardo", est["subtitulo"]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=COLOR_BORDE))
    story.append(Spacer(1, 12))

    # Resumen
    total, criticos, alertas, a_criticas = get_stats()
    story.append(Paragraph("RESUMEN EJECUTIVO", est["seccion"]))
    story.append(tabla_resumen(total, criticos, alertas, a_criticas))
    story.append(Spacer(1, 16))

    # Alertas
    story.append(HRFlowable(width="100%", thickness=0.5, color=COLOR_BORDE))
    story.append(Paragraph("ALERTAS DETECTADAS", est["seccion"]))
    rows_alertas = get_alertas()
    if rows_alertas:
        story.append(tabla_alertas(rows_alertas, est))
    else:
        story.append(Paragraph("Sin alertas registradas.", est["normal"]))
    story.append(Spacer(1, 16))

    # Top eventos
    story.append(HRFlowable(width="100%", thickness=0.5, color=COLOR_BORDE))
    story.append(Paragraph("TOP EVENTOS POR FRECUENCIA", est["seccion"]))
    top = get_top_eventos()
    if top:
        story.append(tabla_top_eventos(top))
    else:
        story.append(Paragraph("Sin eventos registrados.", est["normal"]))
    story.append(Spacer(1, 24))

    # Pie
    story.append(HRFlowable(width="100%", thickness=0.5, color=COLOR_BORDE))
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        f"Mini-SIEM · Reporte generado automáticamente · {fecha}",
        est["pie"]
    ))

    doc.build(story)
    print(f"[+] Reporte generado: {nombre_archivo}")
    print("=" * 50)

# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    generar_reporte()
