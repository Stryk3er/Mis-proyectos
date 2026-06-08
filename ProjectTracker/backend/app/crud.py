"""
CRUD operations — all DB logic lives here, keeping routers thin.
"""

from datetime import date, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from . import models, schemas
from .auth import get_password_hash


# ── Users ────────────────────────────────────────────────────────────────────

def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.email == email).first()

def get_users(db: Session) -> List[models.User]:
    return db.query(models.User).filter(models.User.is_active == True).all()

def create_user(db: Session, user_in: schemas.UserCreate) -> models.User:
    user = models.User(
        name=user_in.name,
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        role=user_in.role,
        avatar_color=user_in.avatar_color,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def authenticate_user(db: Session, email: str, password: str) -> Optional[models.User]:
    from .auth import verify_password
    user = get_user_by_email(db, email)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user


# ── Projects ─────────────────────────────────────────────────────────────────

def get_projects(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    area: Optional[str] = None,
    search: Optional[str] = None,
) -> List[models.Project]:
    q = db.query(models.Project).filter(models.Project.is_active == True)
    if status:
        q = q.filter(models.Project.status == status)
    if priority:
        q = q.filter(models.Project.priority == priority)
    if area:
        q = q.filter(models.Project.area == area)
    if search:
        q = q.filter(models.Project.name.ilike(f"%{search}%"))
    return q.order_by(models.Project.updated_at.desc()).offset(skip).limit(limit).all()

def get_project(db: Session, project_id: int) -> Optional[models.Project]:
    return db.query(models.Project).filter(
        models.Project.id == project_id,
        models.Project.is_active == True,
    ).first()

def create_project(db: Session, project_in: schemas.ProjectCreate) -> models.Project:
    project = models.Project(**project_in.model_dump())
    db.add(project)
    db.commit()
    db.refresh(project)
    return project

def update_project(
    db: Session, project: models.Project, project_in: schemas.ProjectUpdate
) -> models.Project:
    data = project_in.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(project, field, value)
    db.commit()
    db.refresh(project)
    return project

def delete_project(db: Session, project: models.Project) -> None:
    project.is_active = False
    db.commit()

def add_project_update(
    db: Session,
    project_id: int,
    update_in: schemas.ProjectUpdateCreate,
    author_id: int,
) -> models.ProjectUpdate:
    entry = models.ProjectUpdate(
        project_id=project_id,
        author_id=author_id,
        content=update_in.content,
        progress_snapshot=update_in.progress_snapshot,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


# ── Dashboard stats ──────────────────────────────────────────────────────────

def get_dashboard_stats(db: Session) -> schemas.DashboardStats:
    projects = db.query(models.Project).filter(models.Project.is_active == True).all()
    total = len(projects)
    avg = round(sum(p.progress for p in projects) / total, 1) if total else 0.0
    return schemas.DashboardStats(
        total=total,
        on_track=sum(1 for p in projects if p.status == models.StatusEnum.on_track),
        at_risk=sum(1 for p in projects if p.status == models.StatusEnum.at_risk),
        delayed=sum(1 for p in projects if p.status == models.StatusEnum.delayed),
        completed=sum(1 for p in projects if p.status == models.StatusEnum.completed),
        on_hold=sum(1 for p in projects if p.status == models.StatusEnum.on_hold),
        avg_progress=avg,
    )


# ── Seed demo data ───────────────────────────────────────────────────────────

def seed_demo_data(db: Session) -> None:
    """Populate DB with demo users and projects on first run."""
    if db.query(models.User).first():
        return  # Already seeded

    avatar_colors = ["#6366f1", "#f43f5e", "#0ea5e9", "#10b981", "#f59e0b", "#8b5cf6"]

    users_data = [
        {"name": "Admin User",     "email": "admin@company.com",   "password": "admin123",  "role": "admin",  "color": avatar_colors[0]},
        {"name": "Ana García",     "email": "ana@company.com",     "password": "pass123",   "role": "leader", "color": avatar_colors[1]},
        {"name": "Luis Ramírez",   "email": "luis@company.com",    "password": "pass123",   "role": "member", "color": avatar_colors[2]},
        {"name": "María Torres",   "email": "maria@company.com",   "password": "pass123",   "role": "member", "color": avatar_colors[3]},
        {"name": "Carlos Mendez",  "email": "carlos@company.com",  "password": "pass123",   "role": "member", "color": avatar_colors[4]},
        {"name": "Pedro Solís",    "email": "pedro@company.com",   "password": "pass123",   "role": "member", "color": avatar_colors[5]},
    ]

    users = []
    for u in users_data:
        user = models.User(
            name=u["name"], email=u["email"],
            hashed_password=get_password_hash(u["password"]),
            role=u["role"], avatar_color=u["color"],
        )
        db.add(user)
        users.append(user)
    db.commit()
    for u in users:
        db.refresh(u)

    today = date.today()
    projects_data = [
        {"name": "Cloud Migration — GCP", "description": "Migrate on-premise infrastructure to Google Cloud Platform.", "status": "on_track",  "priority": "high",   "progress": 72, "area": "Infrastructure", "end_date": today + timedelta(days=30),  "owner": users[1]},
        {"name": "MFA Corporate Rollout",  "description": "Deploy multi-factor authentication for all corporate users.", "status": "on_track",  "priority": "high",   "progress": 55, "area": "Security",       "end_date": today + timedelta(days=45),  "owner": users[2]},
        {"name": "Looker Dashboard Automation", "description": "Automate weekly reports for area leaders via Looker.", "status": "at_risk",   "priority": "medium", "progress": 30, "area": "Development",    "end_date": today + timedelta(days=10),  "owner": users[3]},
        {"name": "ISO 27001 Policy Update","description": "Review and update ISMS policies aligned to new audit cycle.", "status": "delayed",   "priority": "high",   "progress": 15, "area": "Security",       "end_date": today - timedelta(days=5),   "owner": users[4]},
        {"name": "OT Cybersecurity Training", "description": "IEC 62443 awareness program for plant operators.", "status": "on_track",  "priority": "medium", "progress": 90, "area": "Operations",     "end_date": today + timedelta(days=60),  "owner": users[1]},
        {"name": "Critical Assets Inventory", "description": "Full inventory and risk classification of OT/IT assets.", "status": "at_risk",   "priority": "low",    "progress": 48, "area": "Infrastructure", "end_date": today + timedelta(days=7),   "owner": users[5]},
        {"name": "DevOps Pipeline — CI/CD",   "description": "Implement automated CI/CD pipeline with GitHub Actions.", "status": "on_track",  "priority": "medium", "progress": 60, "area": "Development",    "end_date": today + timedelta(days=20),  "owner": users[2]},
        {"name": "ERP Integration Layer",     "description": "REST adapter connecting ERP with internal microservices.", "status": "on_hold",   "priority": "high",   "progress": 20, "area": "Development",    "end_date": today + timedelta(days=90),  "owner": users[3]},
    ]

    for pd in projects_data:
        project = models.Project(
            name=pd["name"], description=pd["description"],
            status=pd["status"], priority=pd["priority"],
            progress=pd["progress"], area=pd["area"],
            start_date=today - timedelta(days=30),
            end_date=pd["end_date"],
            owner_id=pd["owner"].id,
        )
        db.add(project)
    db.commit()
