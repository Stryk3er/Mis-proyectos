# Portafolio técnico — Julian Eduardo

Proyectos de automatización, inteligencia artificial aplicada y ciberseguridad. El hilo conductor es el mismo en todos: resolver problemas reales con código, reducir trabajo manual y dejar trazabilidad de lo que pasa.

---

## Proyectos

### 🧠 [DataMind AI](./datamind-ai/)
Herramienta web para analizar archivos Excel y CSV con IA. Subes un archivo y en segundos tienes un resumen ejecutivo, métricas clave, tendencias, anomalías y recomendaciones. También puedes hacerle preguntas al dataset en lenguaje natural.

Construido pensando en que cualquier persona — sin saber SQL ni Python — pueda extraer insights de sus datos.

**Stack:** Node.js · Express · Anthropic Claude (Sonnet + Haiku) · Chart.js · Docker  
**Características:** Auth JWT, audit log, rate limiting por usuario, cache de análisis, control de costos en tiempo real

---

### 🤖 [Agente de Tickets](./agente-tickets/)
Agente de IA para equipos de soporte IT que lee los tickets abiertos en Jira Service Management, los clasifica automáticamente por categoría, agrupa los similares, sugiere soluciones concretas y genera un reporte de SLA destacando los tickets en riesgo.

Lo que antes tomaba 30-40 minutos de revisión manual se reduce a ejecutar un script.

**Stack:** Python · Anthropic Claude · Jira API  
**Características:** Clasificación automática por 6 categorías, detección de tickets críticos, reporte exportable, comentarios opcionales directo en Jira

---

### 🔐 [Mini-SIEM](./mini-siem/)
Sistema de gestión de eventos de seguridad que recolecta logs del Event Log de Windows, detecta patrones de ataque (fuerza bruta, escalación de privilegios, persistencia) y los muestra en un dashboard web en tiempo real.

**Stack:** Python · Flask · SQLite · pywin32  
**Características:** Detección de múltiples vectores de ataque, dashboard en tiempo real, exportación de reportes PDF

---

## Tecnologías que uso

| Área | Herramientas |
|---|---|
| IA / LLMs | Anthropic Claude (Sonnet, Haiku), prompt engineering, agentes |
| Backend | Node.js, Express, Python, Flask |
| Seguridad | JWT, bcrypt, audit logging, rate limiting, detección de amenazas |
| Datos | SheetJS, SQLite, Chart.js, análisis estadístico |
| DevOps | Docker, Git, variables de entorno, CI/CD básico |

---

*Más proyectos en desarrollo.*
