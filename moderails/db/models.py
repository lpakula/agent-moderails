"""SQLAlchemy models for moderails."""

import secrets
import string
from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import Column, DateTime, Enum as SQLEnum, ForeignKey, String, Text
from sqlalchemy.orm import DeclarativeBase, relationship


def generate_task_id() -> str:
    """Generate a 6-character alphanumeric task ID."""
    chars = string.ascii_lowercase + string.digits
    return ''.join(secrets.choice(chars) for _ in range(6))


class Base(DeclarativeBase):
    pass


class TaskStatus(str, Enum):
    DRAFT = "draft"
    IN_PROGRESS = "in-progress"
    COMPLETED = "completed"


class TaskType(str, Enum):
    FEATURE = "feature"
    FIX = "fix"
    REFACTOR = "refactor"
    CHORE = "chore"


class Epic(Base):
    __tablename__ = "epics"
    
    id: str = Column(String(6), primary_key=True, default=generate_task_id)
    name: str = Column(String(255), nullable=False, unique=True)
    
    tasks = relationship("Task", back_populates="epic")
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
        }


class Task(Base):
    __tablename__ = "tasks"
    
    id: str = Column(String(6), primary_key=True, default=generate_task_id)
    name: str = Column(String(255), nullable=False)
    file_name: str = Column(String(255), nullable=False)
    summary: str = Column(Text, default="")
    type: TaskType = Column(SQLEnum(TaskType), default=TaskType.FEATURE)
    status: TaskStatus = Column(SQLEnum(TaskStatus), default=TaskStatus.DRAFT)
    git_hash: str = Column(String(40), default="")
    completed_at: datetime = Column(DateTime, nullable=True)
    epic_id: str = Column(String(6), ForeignKey("epics.id"), nullable=True)
    created_at: datetime = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    epic = relationship("Epic", back_populates="tasks")
    
    @property
    def file_path(self) -> str:
        """Get relative path to task file."""
        return f".moderails/{self.file_name}"
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "file_name": self.file_name,
            "summary": self.summary,
            "type": self.type.value,
            "status": self.status.value,
            "epic": self.epic.name if self.epic else None,
            "epic_id": self.epic_id,
            "git_hash": self.git_hash,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
