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
    skills: str = Column(Text, default="[]")  # JSON array of skill names
    
    tasks = relationship("Task", back_populates="epic")
    
    def get_skills(self) -> list[str]:
        """Get skills as a list."""
        import json
        try:
            return json.loads(self.skills or "[]")
        except json.JSONDecodeError:
            return []
    
    def set_skills(self, skill_list: list[str]) -> None:
        """Set skills from a list."""
        import json
        self.skills = json.dumps(skill_list)
    
    def add_skill(self, skill_name: str) -> bool:
        """Add a skill if not already present. Returns True if added."""
        skills = self.get_skills()
        if skill_name not in skills:
            skills.append(skill_name)
            self.set_skills(skills)
            return True
        return False
    
    def remove_skill(self, skill_name: str) -> bool:
        """Remove a skill if present. Returns True if removed."""
        skills = self.get_skills()
        if skill_name in skills:
            skills.remove(skill_name)
            self.set_skills(skills)
            return True
        return False
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "skills": self.get_skills(),
        }


class Task(Base):
    __tablename__ = "tasks"
    
    id: str = Column(String(6), primary_key=True, default=generate_task_id)
    name: str = Column(String(255), nullable=False)
    file_name: str = Column(String(255), nullable=False)
    summary: str = Column(Text, default="")
    description: str = Column(Text, default="")
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
        return f"_moderails/{self.file_name}"
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "file_name": self.file_name,
            "summary": self.summary,
            "description": self.description,
            "type": self.type.value,
            "status": self.status.value,
            "epic": self.epic.name if self.epic else None,
            "epic_id": self.epic_id,
            "git_hash": self.git_hash,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Session(Base):
    """Tracks the current working session for a task.
    
    Only one active session at a time. Sessions are created when a task
    becomes in-progress and deleted when the task completes.
    """
    __tablename__ = "sessions"
    
    id: str = Column(String(6), primary_key=True, default=generate_task_id)
    task_id: str = Column(String(6), ForeignKey("tasks.id"), unique=True, nullable=False)
    current_mode: str = Column(String(20), default="start")
    loaded_memories: str = Column(Text, default="[]")  # JSON array of memory names
    created_at: datetime = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    task = relationship("Task", backref="session", uselist=False)
    
    def get_memories(self) -> list[str]:
        """Get loaded memories as a list."""
        import json
        try:
            return json.loads(self.loaded_memories or "[]")
        except json.JSONDecodeError:
            return []
    
    def add_memory(self, memory_name: str) -> bool:
        """Add a memory if not already loaded. Returns True if added."""
        import json
        memories = self.get_memories()
        if memory_name not in memories:
            memories.append(memory_name)
            self.loaded_memories = json.dumps(memories)
            return True
        return False
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "task_id": self.task_id,
            "current_mode": self.current_mode,
            "loaded_memories": self.get_memories(),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
