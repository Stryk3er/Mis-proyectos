"""
Mini-SIEM - Módulo 3: Dashboard Web
Autor: Julian Eduardo
Descripción: Interfaz web en Flask que muestra eventos y alertas
             en tiempo real con colores por severidad.
"""

from flask import Flask, render_template_string, jsonify
import sqlite3
from datetime import datetime

app = Flask(__name__)
DB_PATH = "siem_eventos.db"

# ── Consultas a la base de datos ──────────────────────────────────────────────
def get_stats():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM eventos")
    total_eventos = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM eventos WHERE nivel = 'CRITICO'")
    total_criticos = cursor.fetchone()[0]
    try:
        cursor.execute("SELECT COUNT(*) FROM alertas")
        total_alertas = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM alertas WHERE severidad = 'CRITICA'")
        alertas_criticas = cursor.fetchone()[0]
    except Exception:
        total_alertas = 0
        alertas_criticas = 0
    conn.close()
    return {
        "total_eventos": total_eventos,
        "total_criticos": total_criticos,
        "total_alertas": total_alertas,
        "alertas_criticas": alertas_criticas,
    }

def get_alertas():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM alertas ORDER BY timestamp DESC LIMIT 50")
        rows = [dict(r) for r in cursor.fetchall()]
    except Exception:
        rows = []
    conn.close()
    return rows

def get_eventos():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM eventos ORDER BY timestamp DESC LIMIT 100")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def get_eventos_por_hora():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT substr(timestamp, 12, 2) as hora, COUNT(*) as total
            FROM eventos
            WHERE timestamp LIKE '____-__-__ %'
            GROUP BY hora ORDER BY hora
        """)
        datos = {str(r[0]).zfill(2): r[1] for r in cursor.fetchall()}
    except Exception:
        datos = {}
    conn.close()
    horas  = [f"{str(h).zfill(2)}:00" for h in range(24)]
    totales = [datos.get(str(h).zfill(2), 0) for h in range(24)]
    return {"horas": horas, "totales": totales}

def get_eventos_por_tipo():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT descripcion, COUNT(*) as total
            FROM eventos GROUP BY descripcion ORDER BY total DESC LIMIT 6
        """)
        rows = cursor.fetchall()
    except Exception:
        rows = []
    conn.close()
    return {"labels": [r[0] for r in rows], "totales": [r[1] for r in rows]}

def get_top_ips():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT ip_origen, COUNT(*) as total FROM eventos
            WHERE ip_origen NOT IN ('Local', 'N/A')
            GROUP BY ip_origen ORDER BY total DESC LIMIT 10
        """)
        rows = [{"ip": r[0], "total": r[1]} for r in cursor.fetchall()]
    except Exception:
        rows = []
    conn.close()
    return rows

# ── HTML del dashboard ────────────────────────────────────────────────────────
TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Mini-SIEM Dashboard</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { background: #0d1117; color: #c9d1d9; font-family: 'Segoe UI', monospace; }

    header {
      background: #161b22;
      border-bottom: 1px solid #30363d;
      padding: 16px 32px;
      display: flex;
      align-items: center;
      justify-content: space-between;
    }
    header h1 { font-size: 1.3rem; color: #58a6ff; letter-spacing: 2px; }
    header span { font-size: 0.8rem; color: #8b949e; }
    #last-update { font-size: 0.75rem; color: #8b949e; }

    .container { padding: 24px 32px; }

    /* Tarjetas de resumen */
    .cards {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 16px;
      margin-bottom: 32px;
    }
    .card {
      background: #161b22;
      border: 1px solid #30363d;
      border-radius: 8px;
      padding: 20px;
      text-align: center;
    }
    .card .number { font-size: 2.5rem; font-weight: bold; }
    .card .label  { font-size: 0.75rem; color: #8b949e; margin-top: 4px; text-transform: uppercase; letter-spacing: 1px; }
    .card.blue   .number { color: #58a6ff; }
    .card.yellow .number { color: #e3b341; }
    .card.orange .number { color: #f0883e; }
    .card.red    .number { color: #f85149; }

    /* Secciones */
    .section { margin-bottom: 32px; }
    .section h2 {
      font-size: 0.9rem;
      text-transform: uppercase;
      letter-spacing: 2px;
      color: #8b949e;
      margin-bottom: 12px;
      border-bottom: 1px solid #21262d;
      padding-bottom: 8px;
    }

    /* Tablas */
    table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
    th {
      background: #161b22;
      color: #8b949e;
      padding: 8px 12px;
      text-align: left;
      font-weight: 500;
      font-size: 0.75rem;
      text-transform: uppercase;
      letter-spacing: 1px;
    }
    td { padding: 8px 12px; border-bottom: 1px solid #21262d; }
    tr:hover td { background: #161b22; }

    /* Badges de severidad */
    .badge {
      display: inline-block;
      padding: 2px 8px;
      border-radius: 4px;
      font-size: 0.7rem;
      font-weight: bold;
      letter-spacing: 1px;
    }
    .CRITICA { background: #3d1a1a; color: #f85149; border: 1px solid #f85149; }
    .ALTA    { background: #2d1f0e; color: #f0883e; border: 1px solid #f0883e; }
    .MEDIA   { background: #2d260e; color: #e3b341; border: 1px solid #e3b341; }
    .BAJA    { background: #0e2d1a; color: #3fb950; border: 1px solid #3fb950; }
    .INFO    { background: #0e1f2d; color: #58a6ff; border: 1px solid #58a6ff; }

    .empty { color: #8b949e; font-style: italic; padding: 16px; text-align: center; }

    /* Gráficas */
    .charts {
      display: grid;
      grid-template-columns: 2fr 1fr;
      gap: 16px;
      margin-bottom: 32px;
    }
    .chart-box {
      background: #161b22;
      border: 1px solid #30363d;
      border-radius: 8px;
      padding: 16px;
    }
    .chart-box h3 {
      font-size: 0.75rem;
      text-transform: uppercase;
      letter-spacing: 1px;
      color: #8b949e;
      margin-bottom: 12px;
    }
    .chart-box canvas { width: 100% !important; }

    /* Barra de estado */
    .status-bar {
      position: fixed; bottom: 0; left: 0; right: 0;
      background: #161b22;
      border-top: 1px solid #30363d;
      padding: 6px 32px;
      font-size: 0.72rem;
      color: #8b949e;
      display: flex;
      justify-content: space-between;
    }
    .dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: #3fb950; margin-right: 6px; animation: pulse 2s infinite; }
    @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.4} }
  </style>
</head>
<body>

<header>
  <h1>🔐 Mini-SIEM Dashboard</h1>
  <div id="last-update">Actualizando...</div>
</header>

<div class="container">

  <div class="cards" id="cards">
    <div class="card blue">
      <div class="number" id="total-eventos">--</div>
      <div class="label">Total Eventos</div>
    </div>
    <div class="card yellow">
      <div class="number" id="total-criticos">--</div>
      <div class="label">Eventos Críticos</div>
    </div>
    <div class="card orange">
      <div class="number" id="total-alertas">--</div>
      <div class="label">Alertas Generadas</div>
    </div>
    <div class="card red">
      <div class="number" id="alertas-criticas">--</div>
      <div class="label">Alertas Críticas</div>
    </div>
  </div>

  <div class="charts">
    <div class="chart-box">
      <h3>📊 Eventos por hora del día</h3>
      <canvas id="chartHoras" height="120"></canvas>
    </div>
    <div class="chart-box">
      <h3>🥧 Top tipos de evento</h3>
      <canvas id="chartTipos" height="120"></canvas>
    </div>
  </div>

  <div class="section">
    <h2>⚠️ Alertas Detectadas</h2>
    <table>
      <thead>
        <tr>
          <th>Timestamp</th>
          <th>Tipo</th>
          <th>Severidad</th>
          <th>Usuario</th>
          <th>Equipo</th>
          <th>Detalle</th>
        </tr>
      </thead>
      <tbody id="tabla-alertas">
        <tr><td colspan="6" class="empty">Cargando...</td></tr>
      </tbody>
    </table>
  </div>

  <div class="section">
    <h2>📋 Eventos Recientes</h2>
    <table>
      <thead>
        <tr>
          <th>Timestamp</th>
          <th>Event ID</th>
          <th>Descripción</th>
          <th>Usuario</th>
          <th>Equipo</th>
          <th>IP Origen</th>
          <th>Nivel</th>
        </tr>
      </thead>
      <tbody id="tabla-eventos">
        <tr><td colspan="7" class="empty">Cargando...</td></tr>
      </tbody>
    </table>
  </div>

  <div class="section">
    <h2>🌐 Top IPs de Origen</h2>
    <table>
      <thead>
        <tr>
          <th>IP</th>
          <th>Ocurrencias</th>
        </tr>
      </thead>
      <tbody id="tabla-ips">
        <tr><td colspan="2" class="empty">Cargando...</td></tr>
      </tbody>
    </table>
  </div>

</div>

<div class="status-bar">
  <span><span class="dot"></span>Mini-SIEM activo | Autor: Julian Eduardo</span>
  <span id="status-time"></span>
</div>

<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
<script>
  Chart.defaults.color = '#8b949e';
  Chart.defaults.borderColor = '#21262d';

  let chartHoras = null;
  let chartTipos = null;

  function iniciarGraficas() {
    fetch('/api/chart_horas')
      .then(r => r.json())
      .then(d => {
        const ctx = document.getElementById('chartHoras').getContext('2d');
        if (chartHoras) chartHoras.destroy();
        chartHoras = new Chart(ctx, {
          type: 'bar',
          data: {
            labels: d.horas,
            datasets: [{
              label: 'Eventos',
              data: d.totales,
              backgroundColor: '#1f6feb',
              borderColor: '#58a6ff',
              borderWidth: 1,
              borderRadius: 3,
            }]
          },
          options: {
            responsive: true,
            plugins: { legend: { display: false } },
            scales: {
              x: { grid: { color: '#21262d' }, ticks: { maxTicksLimit: 12 } },
              y: { grid: { color: '#21262d' }, beginAtZero: true }
            }
          }
        });
      });

    fetch('/api/chart_tipos')
      .then(r => r.json())
      .then(d => {
        const ctx = document.getElementById('chartTipos').getContext('2d');
        if (chartTipos) chartTipos.destroy();
        chartTipos = new Chart(ctx, {
          type: 'doughnut',
          data: {
            labels: d.labels,
            datasets: [{
              data: d.totales,
              backgroundColor: ['#58a6ff','#f85149','#f0883e','#e3b341','#3fb950','#bc8cff'],
              borderColor: '#0d1117',
              borderWidth: 2,
            }]
          },
          options: {
            responsive: true,
            plugins: {
              legend: { position: 'bottom', labels: { boxWidth: 10, font: { size: 10 } } }
            }
          }
        });
      });
  }

  function badge(val) {
    return `<span class="badge ${val}">${val}</span>`;
  }

  function cargarDatos() {
    fetch('/api/stats')
      .then(r => r.json())
      .then(d => {
        document.getElementById('total-eventos').textContent   = d.total_eventos;
        document.getElementById('total-criticos').textContent  = d.total_criticos;
        document.getElementById('total-alertas').textContent   = d.total_alertas;
        document.getElementById('alertas-criticas').textContent = d.alertas_criticas;
      });

    fetch('/api/alertas')
      .then(r => r.json())
      .then(rows => {
        const tbody = document.getElementById('tabla-alertas');
        if (!rows.length) {
          tbody.innerHTML = '<tr><td colspan="6" class="empty">Sin alertas detectadas.</td></tr>';
          return;
        }
        tbody.innerHTML = rows.map(r => `
          <tr>
            <td>${r.timestamp}</td>
            <td>${r.tipo}</td>
            <td>${badge(r.severidad)}</td>
            <td>${r.usuario}</td>
            <td>${r.computador}</td>
            <td>${r.detalle}</td>
          </tr>`).join('');
      });

    fetch('/api/eventos')
      .then(r => r.json())
      .then(rows => {
        const tbody = document.getElementById('tabla-eventos');
        tbody.innerHTML = rows.map(r => `
          <tr>
            <td>${r.timestamp}</td>
            <td>${r.event_id}</td>
            <td>${r.descripcion}</td>
            <td>${r.usuario}</td>
            <td>${r.computador}</td>
            <td>${r.ip_origen || 'Local'}</td>
            <td>${badge(r.nivel)}</td>
          </tr>`).join('');
      });

    fetch('/api/top_ips')
      .then(r => r.json())
      .then(rows => {
        const tbody = document.getElementById('tabla-ips');
        if (!rows.length) {
          tbody.innerHTML = '<tr><td colspan="2" class="empty">Sin IPs externas registradas.</td></tr>';
          return;
        }
        tbody.innerHTML = rows.map(r => `
          <tr>
            <td>${r.ip}</td>
            <td>${r.total}</td>
          </tr>`).join('');
      });

    const now = new Date().toLocaleTimeString('es-MX');
    document.getElementById('last-update').textContent = `Última actualización: ${now}`;
    document.getElementById('status-time').textContent = now;
  }

  iniciarGraficas();
  cargarDatos();
  setInterval(() => { iniciarGraficas(); cargarDatos(); }, 30000);
</script>

</body>
</html>
"""

# ── Rutas Flask ───────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template_string(TEMPLATE)

@app.route("/api/stats")
def api_stats():
    return jsonify(get_stats())

@app.route("/api/alertas")
def api_alertas():
    return jsonify(get_alertas())

@app.route("/api/eventos")
def api_eventos():
    return jsonify(get_eventos())

@app.route("/api/top_ips")
def api_top_ips():
    return jsonify(get_top_ips())

@app.route("/api/chart_horas")
def api_chart_horas():
    return jsonify(get_eventos_por_hora())

@app.route("/api/chart_tipos")
def api_chart_tipos():
    return jsonify(get_eventos_por_tipo())

# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n🔐 Mini-SIEM - Dashboard Web v1.0")
    print("=" * 40)
    print("  Abre tu navegador en:")
    print("  http://127.0.0.1:5000")
    print("=" * 40)
    app.run(debug=False, port=5000)
