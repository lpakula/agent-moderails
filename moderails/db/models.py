"""SQLAlchemy models for moderails."""

import uuid
from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import Column, DateTime, Enum as SQLEnum, ForeignKey, String, Text
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class TaskStatus(str, Enum):
    TODO = "todo"
    IN_PROGRESS = "in-progress"
    COMPLETED = "completed"


class Epic(Base):
    __tablename__ = "epics"
    
    id: str = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: str = Column(String(255), nullable=False, unique=True)
    tag: str = Column(String(100), default="")
    created_at: datetime = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    tasks = relationship("Task", back_populates="epic")
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "tag": self.tag,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Task(Base):
    __tablename__ = "tasks"
    
    id: str = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: str = Column(String(255), nullable=False, unique=True)
    file_name: str = Column(String(255), nullable=False)
    summary: str = Column(Text, default="")
    status: TaskStatus = Column(SQLEnum(TaskStatus), default=TaskStatus.TODO)
    git_hash: str = Column(String(40), default="")
    completed_at: datetime = Column(DateTime, nullable=True)
    epic_id: str = Column(String(36), ForeignKey("epics.id"), nullable=False)
    created_at: datetime = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    epic = relationship("Epic", back_populates="tasks")
    
    @property
    def file_path(self) -> str:
        """Get relative path to task file."""
        return f"moderails/tasks/{self.epic.name}/{self.file_name}"
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "file_name": self.file_name,
            "summary": self.summary,
            "status": self.status.value,
            "epic": self.epic.name if self.epic else None,
            "epic_id": self.epic_id,
            "git_hash": self.git_hash,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
