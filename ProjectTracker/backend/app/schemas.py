"""
Pydantic v2 schemas for request/response validation.
"""

from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, EmailStr, field_validator
from .models import StatusEnum, PriorityEnum


# ── Auth ────────────────────────────────────────────────────────────────────

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    user_id: Optional[int] = None


# ── User ────────────────────────────────────────────────────────────────────

class UserBase(BaseModel):
    name: str
    email: EmailStr
    role: str = "member"
    avatar_color: str = "#6366f1"

class UserCreate(UserBase):
    password: str

class UserOut(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Project Member ───────────────────────────────────────────────────────────

class MemberOut(BaseModel):
    id: int
    user_id: int
    role: str
    user: UserOut

    model_config = {"from_attributes": True}


# ── Project Update ───────────────────────────────────────────────────────────

class ProjectUpdateCreate(BaseModel):
    content: str
    progress_snapshot: Optional[int] = None

class ProjectUpdateOut(BaseModel):
    id: int
    content: str
    progress_snapshot: Optional[int]
    created_at: datetime
    author: Optional[UserOut]

    model_config = {"from_attributes": True}


# ── Project ──────────────────────────────────────────────────────────────────

class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None
    status: StatusEnum = StatusEnum.on_track
    priority: PriorityEnum = PriorityEnum.medium
    progress: int = 0
    area: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    owner_id: Optional[int] = None

    @field_validator("progress")
    @classmethod
    def clamp_progress(cls, v: int) -> int:
        return max(0, min(100, v))

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[StatusEnum] = None
    priority: Optional[PriorityEnum] = None
    progress: Optional[int] = None
    area: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    owner_id: Optional[int] = None

class ProjectOut(ProjectBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    owner: Optional[UserOut] = None
    members: List[MemberOut] = []
    updates: List[ProjectUpdateOut] = []

    model_config = {"from_attributes": True}

class ProjectSummary(BaseModel):
    """Lightweight version for list views."""
    id: int
    name: str
    description: Optional[str]
    status: StatusEnum
    priority: PriorityEnum
    progress: int
    area: Optional[str]
    end_date: Optional[date]
    owner: Optional[UserOut]
    member_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Dashboard KPIs ───────────────────────────────────────────────────────────

class DashboardStats(BaseModel):
    total: int
    on_track: int
    at_risk: int
    delayed: int
    completed: int
    on_hold: int
    avg_progress: float
