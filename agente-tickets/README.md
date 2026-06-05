# Agente de Tickets — Jira Service Management

Agente de IA para el equipo de IT de Deacero que automatiza el análisis de tickets de Jira Service Management: los clasifica, agrupa, sugiere soluciones y genera reportes de SLA.

## ¿Qué hace?

1. **Lee tickets abiertos** de Jira JSM vía API
2. **Clasifica y agrupa** por categoría usando Claude (Accesos/Permisos, Hardware, Conectividad/Red, Software/Licencias, Impresoras, Correo/Office365)
3. **Sugiere solución** concreta para cada grupo de tickets similares
4. **Genera reporte de SLA** destacando tickets en riesgo y tickets críticos
5. **Escribe comentarios en Jira** (opcional, desactivado por defecto)

## Requisitos

```bash
pip install anthropic requests python-dotenv
```

## Configuración

Copia `.env.example` como `.env` y llena tus credenciales:

```bash
cp .env.example .env
```

```env
ANTHROPIC_API_KEY=sk-ant-...
JIRA_URL=https://deacero.atlassian.net
JIRA_EMAIL=tu@deacero.com
JIRA_TOKEN=tu_api_token_de_jira
JIRA_PROJECT=SD
```

> El token de Jira se genera en: **Jira → Perfil → Manage account → Security → API tokens**

## Uso

```bash
python agente_tickets.py
```

Por defecto corre en **modo simulación**: lee Jira pero no escribe comentarios. Para activar escritura:

```python
# En agente_tickets.py, línea final:
agente(tarea="...", escribir_en_jira=True)
```

## SLA por defecto

El límite es **8 horas**. Tickets que superen ese tiempo aparecen como "en riesgo"; los que superen 16 horas se marcan como "críticos".

Para cambiar el límite, pasa `sla_horas=N` a la herramienta `generar_reporte_sla`.

## Estructura del proyecto

```
agente-tickets/
├── agente_tickets.py   # Script principal
├── .env.example        # Plantilla de variables de entorno
└── README.md
```
