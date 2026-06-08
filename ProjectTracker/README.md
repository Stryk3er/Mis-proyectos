<div align="center">

# 📊 ProjectTracker

**A lightweight, self-hostable project management tool for teams without SaaS licenses.**

[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=flat&logo=fastapi)](https://fastapi.tiangolo.com)
[![Vue 3](https://img.shields.io/badge/Vue-3.4-42b883?style=flat&logo=vue.js)](https://vuejs.org)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind-3.4-38bdf8?style=flat&logo=tailwindcss)](https://tailwindcss.com)
[![SQLite](https://img.shields.io/badge/SQLite-3-003b57?style=flat&logo=sqlite)](https://sqlite.org)
[![Docker](https://img.shields.io/badge/Docker-compose-2496ed?style=flat&logo=docker)](https://docker.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>

---

## 🎯 Why ProjectTracker?

Enterprise tools like Jira or Azure DevOps are great for large software teams, but **manufacturing plants, ops teams, and SMBs** often need something simpler: track which projects exist, who owns them, and whether they're on time — without paying for SaaS seats or requiring cloud connectivity.

ProjectTracker runs entirely **on-premise** with a single SQLite database. No internet required after setup.

---

## ✨ Features

- 🔐 **JWT Authentication** — secure login with role-based access (admin / leader / member)
- 📋 **Full Project CRUD** — create, edit, soft-delete projects with rich metadata
- 🚦 **Status Tracking** — On Track / At Risk / Delayed / Completed / On Hold
- 📈 **Progress Bar** — 0–100% visual indicator per project
- 🏷️ **Priority & Area** — tag projects by business area and urgency
- 📅 **Due Date Warnings** — automatic overdue / approaching alerts
- 📝 **Project Changelog** — post progress notes with timestamps
- 📊 **KPI Dashboard** — live aggregate cards (total, by status, avg progress)
- 🔍 **Filtering & Search** — filter by status, priority, area, or free text
- 🐳 **Docker-ready** — `docker compose up` and you're done
- 📖 **Auto API Docs** — Swagger UI at `/api/docs`, ReDoc at `/api/redoc`

---

## 🏗️ Architecture

```
ProjectTracker/
├── backend/             # FastAPI · SQLAlchemy · SQLite · JWT
│   └── app/
│       ├── main.py      # App entry point + CORS + lifespan
│       ├── config.py    # Settings from .env
│       ├── database.py  # SQLAlchemy engine & session
│       ├── models.py    # ORM models (User, Project, Member, Update)
│       ├── schemas.py   # Pydantic v2 request/response schemas
│       ├── crud.py      # All DB operations (thin routers pattern)
│       ├── auth.py      # JWT creation, verification, dependencies
│       └── routers/
│           ├── auth.py      # POST /login · GET /me · GET /users
│           └── projects.py  # CRUD + /stats + /updates
└── frontend/            # Vue 3 · Pinia · Vue Router · Tailwind
    └── src/
        ├── api/         # Axios instance with JWT interceptors
        ├── stores/      # auth.js · projects.js (Pinia)
        ├── router/      # Vue Router with auth navigation guard
        ├── views/       # Login.vue · Dashboard.vue
        └── components/  # KpiCards · FilterBar · ProjectTable · ProjectModal
```

---

## 🚀 Quick Start

### Option A — Docker Compose (recommended)

```bash
git clone https://github.com/your-username/project-tracker.git
cd project-tracker
cp .env.example .env          # edit SECRET_KEY
docker compose up --build
```

Open **http://localhost** — the app is running.

### Option B — Local development

**Backend**

```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp ../.env.example .env
uvicorn app.main:app --reload
# API running at http://localhost:8000
# Swagger docs at http://localhost:8000/api/docs
```

**Frontend** (new terminal)

```bash
cd frontend
npm install
npm run dev
# App running at http://localhost:5173
```

---

## 🔑 Demo Credentials

| Role   | Email                  | Password  |
|--------|------------------------|-----------|
| Admin  | admin@company.com      | admin123  |
| Leader | ana@company.com        | pass123   |
| Member | luis@company.com       | pass123   |

---

## 📡 API Reference

Full interactive docs available at `/api/docs` (Swagger) or `/api/redoc`.

| Method | Endpoint                        | Description                        |
|--------|---------------------------------|------------------------------------|
| POST   | `/api/auth/login`               | Get JWT token                      |
| GET    | `/api/auth/me`                  | Authenticated user profile         |
| GET    | `/api/auth/users`               | List all users                     |
| GET    | `/api/projects`                 | List projects (filterable)         |
| POST   | `/api/projects`                 | Create project                     |
| GET    | `/api/projects/{id}`            | Project detail with members & log  |
| PATCH  | `/api/projects/{id}`            | Partial update                     |
| DELETE | `/api/projects/{id}`            | Soft delete                        |
| GET    | `/api/projects/stats`           | Dashboard KPIs                     |
| POST   | `/api/projects/{id}/updates`    | Add progress note                  |

---

## 🔧 Configuration

| Variable                      | Default                      | Description                    |
|-------------------------------|------------------------------|--------------------------------|
| `SECRET_KEY`                  | *(required in prod)*         | JWT signing key                |
| `DATABASE_URL`                | `sqlite:///./projecttracker.db` | SQLAlchemy DB URL           |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `480`                        | Token lifetime (8 h)           |

---

## 🛣️ Roadmap

- [ ] PostgreSQL support for multi-instance deployments
- [ ] Excel / PDF export
- [ ] Email notifications for overdue projects
- [ ] Gantt chart view
- [ ] Role-based project visibility

---

## 📄 License

MIT © 2024
