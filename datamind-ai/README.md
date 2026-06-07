# DataMind AI — Excel Intelligence

> Plataforma full-stack de análisis de datos con IA. Sube cualquier archivo Excel y obtén un reporte ejecutivo automático, gráficas y un chat en lenguaje natural — todo impulsado por Claude de Anthropic.

![stack](https://img.shields.io/badge/stack-Node.js%20%2B%20Express%20%2B%20Anthropic-6366f1?style=flat-square)
![license](https://img.shields.io/badge/license-MIT-22d3ee?style=flat-square)
![model](https://img.shields.io/badge/AI-Claude%20Sonnet%204.6-a855f7?style=flat-square)
![docker](https://img.shields.io/badge/docker-ready-0ea5e9?style=flat-square)

---

## Features

- **Drag & drop upload** — `.xlsx`, `.xls`, `.csv` con soporte multi-hoja
- **Análisis IA automático** — resumen ejecutivo, métricas clave, tendencias, anomalías y recomendaciones
- **Gráfica automática** — Chart.js con configuración generada por la IA
- **Chat en lenguaje natural** — pregunta cualquier cosa sobre tus datos
- **Datasets grandes** — análisis estadístico inteligente para archivos con miles de filas
- **Exportar PDF** — reporte listo para presentar con `Ctrl+P`
- **Exportar CSV** — descarga los datos filtrados en un clic
- **Búsqueda y ordenamiento** en la tabla de datos
- **Backend seguro** — la API key de Anthropic vive en el servidor, nunca en el navegador

## Arquitectura

```
Browser (HTML/JS)  →  Express server (Node.js)  →  Anthropic API
     SheetJS             /api/analyze                  Claude
     Chart.js            /api/health               Sonnet / Haiku
```

## Inicio rápido

```bash
# 1. Clonar e instalar
git clone https://github.com/tu-usuario/datamind-ai.git
cd datamind-ai
npm install

# 2. Configurar API key
cp .env.example .env
# Edita .env y agrega tu ANTHROPIC_API_KEY

# 3. Correr
npm start
# → http://localhost:3000
```

## Con Docker

```bash
docker build -t datamind-ai .
docker run -p 3000:3000 -e ANTHROPIC_API_KEY=sk-ant-... datamind-ai
```

## Estructura del proyecto

```
datamind-ai/
├── server.js          ← Backend Node.js / Express
├── public/
│   └── index.html     ← Frontend SPA (HTML + CSS + JS)
├── .env               ← API key (no se sube a git)
├── .env.example       ← Plantilla de configuración
├── package.json
├── Dockerfile
└── README.md
```

## Variables de entorno

| Variable | Descripción | Default |
|---|---|---|
| `ANTHROPIC_API_KEY` | API key de Anthropic | requerida |
| `PORT` | Puerto del servidor | `3000` |

## Despliegue en producción

Funciona en cualquier plataforma que soporte Node.js 18+:

- **Railway / Render / Fly.io** — conecta el repo y configura `ANTHROPIC_API_KEY` en variables de entorno
- **VPS (Ubuntu/Debian)** — `npm start` o PM2 para proceso persistente
- **Docker** — ver sección Docker arriba

## License

MIT
