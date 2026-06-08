"""
SQLAlchemy ORM models.
"""

from datetime import datetime, date
from sqlalchemy import (
    Column, Integer, String, Text, Date, DateTime,
    ForeignKey, Enum, Boolean, Float
)
from sqlalchemy.orm import relationship
import enum
from .database import Base


class StatusEnum(str, enum.Enum):
    on_track = "on_track"
    at_risk = "at_risk"
    delayed = "delayed"
    completed = "completed"
    on_hold = "on_hold"


class PriorityEnum(str, enum.Enum):
    high = "high"
    medium = "medium"
    low = "low"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    email = Column(String(200), unique=True, index=True, nullable=False)
    hashed_password = Column(String(256), nullable=False)
    role = Column(String(50), default="member")  # admin | leader | member
    avatar_color = Column(String(10), default="#6366f1")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    owned_projects = relationship("Project", back_populates="owner", foreign_keys="Project.owner_id")
    memberships = relationship("ProjectMember", back_populates="user")


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(Enum(StatusEnum), default=StatusEnum.on_track, nullable=False)
    priority = Column(Enum(PriorityEnum), default=PriorityEnum.medium, nullable=False)
    progress = Column(Integer, default=0)         # 0–100
    area = Column(String(100), nullable=True)      # e.g. "Infraestructura", "Desarrollo"
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner = relationship("User", back_populates="owned_projects", foreign_keys=[owner_id])
    members = relationship("ProjectMember", back_populates="project", cascade="all, delete-orphan")
    updates = relationship("ProjectUpdate", back_populates="project", cascade="all, delete-orphan",
                           order_by="ProjectUpdate.created_at.desc()")


class ProjectMember(Base):
    __tablename__ = "project_members"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(String(80), default="member")

    project = relationship("Project", back_populates="members")
    user = relationship("User", back_populates="memberships")


class ProjectUpdate(Base):
    """Changelog / progress notes per project."""
    __tablename__ = "project_updates"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    content = Column(Text, nullable=False)
    progress_snapshot = Column(Integer, nullable=True)  # progress at time of update
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="updates")
    author = relationship("User")
