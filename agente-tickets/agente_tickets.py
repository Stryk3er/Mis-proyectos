"""
Agente de tickets — Jira Service Management
Deacero IT Support

Funciones:
  - Lee tickets abiertos de Jira JSM
  - Los clasifica por categoría
  - Agrupa los similares
  - Sugiere solución para cada grupo
  - Genera reporte de SLA
  - (Opcional) Escribe el comentario de vuelta en Jira

Requiere:
  pip install anthropic requests python-dotenv

Variables en .env:
  ANTHROPIC_API_KEY=...
  JIRA_URL=https://deacero.atlassian.net
  JIRA_EMAIL=tu@deacero.com
  JIRA_TOKEN=tu_api_token
  JIRA_PROJECT=SD   ← clave de tu proyecto JSM
"""

import os
import json
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv
import anthropic

load_dotenv()

# ─── Configuración ────────────────────────────────────────────────────────────

JIRA_URL   = os.getenv("JIRA_URL", "https://deacero.atlassian.net")
JIRA_EMAIL = os.getenv("JIRA_EMAIL")
JIRA_TOKEN = os.getenv("JIRA_TOKEN")
JIRA_PROJECT = os.getenv("JIRA_PROJECT", "SD")

jira_auth    = (JIRA_EMAIL, JIRA_TOKEN)
jira_headers = {"Accept": "application/json", "Content-Type": "application/json"}

client = anthropic.Anthropic()

# ─── HERRAMIENTAS que el agente puede usar ────────────────────────────────────

TOOLS = [
    {
        "name": "obtener_tickets_abiertos",
        "description": (
            "Lee los tickets abiertos de Jira Service Management. "
            "Devuelve una lista con clave, resumen, descripción, estado, "
            "prioridad, fecha de creación y tiempo transcurrido en horas."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "max_resultados": {
                    "type": "integer",
                    "description": "Cuántos tickets traer. Default 50.",
                    "default": 50
                }
            }
        }
    },
    {
        "name": "clasificar_y_agrupar",
        "description": (
            "Recibe una lista de tickets (JSON) y devuelve grupos por categoría. "
            "Categorías posibles: Accesos/Permisos, Hardware, Conectividad/Red, "
            "Software/Licencias, Impresoras, Correo/Office365, Sin ciencia (ruido)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "tickets_json": {
                    "type": "string",
                    "description": "JSON string con la lista de tickets"
                }
            },
            "required": ["tickets_json"]
        }
    },
    {
        "name": "sugerir_solucion",
        "description": (
            "Dada una categoría y una lista de tickets similares, "
            "genera pasos de solución concretos y accionables para resolver ese grupo."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "categoria": {"type": "string"},
                "tickets_json": {"type": "string", "description": "JSON del grupo de tickets"}
            },
            "required": ["categoria", "tickets_json"]
        }
    },
    {
        "name": "generar_reporte_sla",
        "description": (
            "Analiza todos los tickets y genera un reporte de SLA: "
            "tickets en riesgo, tiempo promedio por categoría, y recomendaciones."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "tickets_json": {"type": "string"},
                "sla_horas": {
                    "type": "integer",
                    "description": "Límite de SLA en horas. Default 8.",
                    "default": 8
                }
            },
            "required": ["tickets_json"]
        }
    },
    {
        "name": "agregar_comentario_jira",
        "description": "Agrega un comentario a un ticket de Jira con la solución sugerida.",
        "input_schema": {
            "type": "object",
            "properties": {
                "ticket_key": {"type": "string", "description": "Ej: SD-123"},
                "comentario": {"type": "string"}
            },
            "required": ["ticket_key", "comentario"]
        }
    }
]


# ─── Implementación de cada herramienta ──────────────────────────────────────

def obtener_tickets_abiertos(max_resultados=50):
    """Consulta Jira JSM por JQL y devuelve lista de tickets."""
    jql = f'project = {JIRA_PROJECT} AND status != Done ORDER BY created DESC'
    url = f"{JIRA_URL}/rest/api/3/search"
    params = {
        "jql": jql,
        "maxResults": max_resultados,
        "fields": "summary,description,status,priority,created,comment"
    }
    resp = requests.get(url, auth=jira_auth, headers=jira_headers, params=params)
    resp.raise_for_status()
    data = resp.json()

    tickets = []
    ahora = datetime.now(timezone.utc)
    for issue in data.get("issues", []):
        fields = issue["fields"]
        created = datetime.fromisoformat(fields["created"].replace("Z", "+00:00"))
        horas = round((ahora - created).total_seconds() / 3600, 1)

        # Extraer texto de descripción (Jira usa Atlassian Document Format)
        desc = fields.get("description") or {}
        desc_texto = ""
        if isinstance(desc, dict):
            for block in desc.get("content", []):
                for node in block.get("content", []):
                    desc_texto += node.get("text", "") + " "
        else:
            desc_texto = str(desc)

        tickets.append({
            "key": issue["key"],
            "resumen": fields.get("summary", ""),
            "descripcion": desc_texto.strip()[:400],
            "estado": fields["status"]["name"],
            "prioridad": fields.get("priority", {}).get("name", "Medium"),
            "horas_abierto": horas
        })

    return json.dumps(tickets, ensure_ascii=False)


def clasificar_y_agrupar(tickets_json):
    """Usa Claude para clasificar tickets en categorías."""
    prompt = f"""Eres un experto en soporte IT. Clasifica cada ticket en UNA de estas categorías:
- Accesos/Permisos
- Hardware
- Conectividad/Red
- Software/Licencias
- Impresoras
- Correo/Office365
- Sin ciencia (ruido sin problema real)

Tickets:
{tickets_json}

Devuelve SOLO un JSON con esta estructura:
{{
  "grupos": {{
    "Accesos/Permisos": ["SD-1","SD-5"],
    "Hardware": ["SD-2"],
    ...
  }},
  "sin_ciencia": ["SD-9"],
  "resumen": "X tickets clasificados en Y categorías"
}}"""

    resp = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}]
    )
    return resp.content[0].text


def sugerir_solucion(categoria, tickets_json):
    """Genera pasos de solución para un grupo de tickets."""
    prompt = f"""Eres un técnico senior de IT en una empresa siderúrgica (Deacero, México).

Categoría del grupo: {categoria}
Tickets en este grupo:
{tickets_json}

Genera una respuesta estructurada con:
1. Causa raíz probable
2. Pasos de solución (numerados, concretos)
3. Tiempo estimado de resolución
4. Si aplica: cómo prevenir que vuelva a ocurrir

Sé directo y práctico. Máximo 200 palabras."""

    resp = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=600,
        messages=[{"role": "user", "content": prompt}]
    )
    return resp.content[0].text


def generar_reporte_sla(tickets_json, sla_horas=8):
    """Analiza tickets y genera reporte de SLA."""
    tickets = json.loads(tickets_json)
    en_riesgo = [t for t in tickets if t["horas_abierto"] >= sla_horas]
    criticos  = [t for t in tickets if t["horas_abierto"] >= sla_horas * 2]

    reporte = {
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "total_tickets": len(tickets),
        "en_riesgo_sla": len(en_riesgo),
        "criticos": len(criticos),
        "tickets_criticos": [{"key": t["key"], "horas": t["horas_abierto"], "resumen": t["resumen"]} for t in criticos],
        "promedio_horas": round(sum(t["horas_abierto"] for t in tickets) / len(tickets), 1) if tickets else 0,
        "sla_limite_horas": sla_horas
    }
    return json.dumps(reporte, ensure_ascii=False, indent=2)


def agregar_comentario_jira(ticket_key, comentario):
    """Escribe un comentario en el ticket de Jira."""
    url = f"{JIRA_URL}/rest/api/3/issue/{ticket_key}/comment"
    body = {
        "body": {
            "type": "doc",
            "version": 1,
            "content": [{
                "type": "paragraph",
                "content": [{"type": "text", "text": f"[Agente IA] {comentario}"}]
            }]
        }
    }
    resp = requests.post(url, auth=jira_auth, headers=jira_headers, json=body)
    if resp.status_code == 201:
        return f"Comentario agregado a {ticket_key}"
    return f"Error {resp.status_code}: {resp.text[:200]}"


# ─── Dispatcher ──────────────────────────────────────────────────────────────

def ejecutar_herramienta(nombre, params):
    print(f"\n  🔧 [{nombre}]")
    if nombre == "obtener_tickets_abiertos":
        return obtener_tickets_abiertos(params.get("max_resultados", 50))
    if nombre == "clasificar_y_agrupar":
        return clasificar_y_agrupar(params["tickets_json"])
    if nombre == "sugerir_solucion":
        return sugerir_solucion(params["categoria"], params["tickets_json"])
    if nombre == "generar_reporte_sla":
        return generar_reporte_sla(params["tickets_json"], params.get("sla_horas", 8))
    if nombre == "agregar_comentario_jira":
        return agregar_comentario_jira(params["ticket_key"], params["comentario"])
    return f"Herramienta '{nombre}' no reconocida"


# ─── Loop del agente ─────────────────────────────────────────────────────────

SYSTEM_PROMPT = """Eres un agente de soporte IT para Deacero (empresa siderúrgica mexicana).
Tu objetivo es ayudar al equipo de IT a resolver tickets de Jira Service Management más rápido.

Cuando te pidan analizar tickets:
1. Obtén los tickets abiertos
2. Clasifícalos y agrúpalos por categoría
3. Para cada grupo genera una solución
4. Genera el reporte de SLA destacando los tickets en riesgo
5. Opcionalmente actualiza los tickets en Jira con el comentario de solución

Sé conciso, práctico y directo. Prioriza siempre los tickets más antiguos."""


def agente(tarea: str, escribir_en_jira=False):
    print(f"\n{'='*60}")
    print(f"🤖 Tarea: {tarea}")
    print(f"{'='*60}")

    mensajes = [{"role": "user", "content": tarea}]

    # Guardamos tickets para reusar sin volver a pedir
    tickets_cache = None

    while True:
        resp = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=mensajes
        )

        if resp.stop_reason == "tool_use":
            mensajes.append({"role": "assistant", "content": resp.content})
            resultados = []

            for bloque in resp.content:
                if bloque.type == "tool_use":
                    params = bloque.input

                    # Si ya tenemos los tickets en cache, los reutilizamos
                    if bloque.name in ("clasificar_y_agrupar", "generar_reporte_sla"):
                        if tickets_cache and "tickets_json" not in params:
                            params["tickets_json"] = tickets_cache

                    resultado = ejecutar_herramienta(bloque.name, params)

                    # Guardamos en cache si son los tickets crudos
                    if bloque.name == "obtener_tickets_abiertos":
                        tickets_cache = resultado

                    # Si el agente decide escribir en Jira pero está desactivado
                    if bloque.name == "agregar_comentario_jira" and not escribir_en_jira:
                        resultado = "✋ Escritura en Jira desactivada en modo simulación."

                    resultados.append({
                        "type": "tool_result",
                        "tool_use_id": bloque.id,
                        "content": resultado
                    })

            mensajes.append({"role": "user", "content": resultados})

        else:
            # Respuesta final
            texto = next((b.text for b in resp.content if hasattr(b, "text")), "")
            print(f"\n✅ Análisis completado:\n")
            print(texto)
            return texto


# ─── Punto de entrada ────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Modo simulación: lee Jira pero NO escribe comentarios
    # Cambia a escribir_en_jira=True cuando estés listo para producción
    agente(
        tarea=(
            "Analiza todos los tickets abiertos de hoy. "
            "Clasifícalos, agrúpalos, sugiere solución para cada grupo "
            "y dime cuáles están en riesgo de romper el SLA de 8 horas."
        ),
        escribir_en_jira=False
    )
