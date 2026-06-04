# 🔐 Mini-SIEM

Sistema de gestión de eventos e información de seguridad (SIEM) desarrollado en Python como proyecto de portafolio en ciberseguridad.

## ¿Qué hace?

Recolecta eventos del Security Event Log de Windows, los analiza en busca de patrones sospechosos y los visualiza en un dashboard web en tiempo real.

## Módulos

| Archivo | Descripción |
|---|---|
| `log_collector.py` | Recolecta eventos del Event Log de Windows y los guarda en SQLite |
| `alert_engine.py` | Analiza los eventos y genera alertas por severidad |
| `dashboard.py` | Dashboard web (Flask) con tablas y métricas en tiempo real |

## Detección de amenazas

- **Fuerza bruta** — 3+ logins fallidos (EventID 4625) en menos de 1 minuto
- **Cuenta bloqueada post-ataque** — correlación entre 4625 y 4740
- **Servicio nuevo instalado** — alerta inmediata en EventID 7045 (posible persistencia)
- **Privilegios fuera de horario** — EventID 4672 entre 10pm y 6am

## Tecnologías

- Python 3
- SQLite (almacenamiento de eventos y alertas)
- Flask (dashboard web)
- pywin32 (lectura del Event Log de Windows)

## Cómo correrlo

```bash
# 1. Instalar dependencias
pip install flask pywin32

# 2. Recolectar eventos (ejecutar como Administrador)
python log_collector.py

# 3. Correr el motor de alertas
python alert_engine.py

# 4. Levantar el dashboard
python dashboard.py
# Abrir http://127.0.0.1:5000
```

> **Nota:** Para leer logs reales de Windows, ejecutar como Administrador. Si no, corre en modo simulación automáticamente.
