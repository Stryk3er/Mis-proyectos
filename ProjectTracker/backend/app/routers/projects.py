"""
Projects router — full CRUD + dashboard stats.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from .. import crud, schemas, models
from ..auth import get_current_user
from ..database import get_db

router = APIRouter()


@router.get("/stats", response_model=schemas.DashboardStats)
def dashboard_stats(
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user),
):
    """Aggregate KPIs for the dashboard."""
    return crud.get_dashboard_stats(db)


@router.get("/", response_model=List[schemas.ProjectSummary])
def list_projects(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=200),
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    area: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user),
):
    """List projects with optional filters."""
    projects = crud.get_projects(db, skip, limit, status, priority, area, search)
    result = []
    for p in projects:
        summary = schemas.ProjectSummary(
            id=p.id, name=p.name, description=p.description,
            status=p.status, priority=p.priority, progress=p.progress,
            area=p.area, end_date=p.end_date, owner=p.owner,
            member_count=len(p.members),
            created_at=p.created_at, updated_at=p.updated_at,
        )
        result.append(summary)
    return result


@router.post("/", response_model=schemas.ProjectOut, status_code=status.HTTP_201_CREATED)
def create_project(
    project_in: schemas.ProjectCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Create a new project."""
    return crud.create_project(db, project_in)


@router.get("/{project_id}", response_model=schemas.ProjectOut)
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user),
):
    """Retrieve full project detail including members and updates."""
    project = crud.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.patch("/{project_id}", response_model=schemas.ProjectOut)
def update_project(
    project_id: int,
    project_in: schemas.ProjectUpdate,
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user),
):
    """Partially update a project (PATCH semantics)."""
    project = crud.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return crud.update_project(db, project, project_in)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user),
):
    """Soft-delete a project."""
    project = crud.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    crud.delete_project(db, project)


@router.post("/{project_id}/updates", response_model=schemas.ProjectUpdateOut, status_code=201)
def add_update(
    project_id: int,
    update_in: schemas.ProjectUpdateCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Post a progress note to the project changelog."""
    project = crud.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return crud.add_project_update(db, project_id, update_in, current_user.id)
