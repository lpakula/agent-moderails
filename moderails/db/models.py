"""SQLAlchemy models for moderails."""

import secrets
import string
from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import Column, DateTime, Enum as SQLEnum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, relationship


def generate_id() -> str:
    """Generate a 6-character alphanumeric ID."""
    chars = string.ascii_lowercase + string.digits
    return "".join(secrets.choice(chars) for _ in range(6))


class Base(DeclarativeBase):
    pass


class TaskType(str, Enum):
    FEATURE = "feature"
    FIX = "fix"
    REFACTOR = "refactor"
    CHORE = "chore"


class Project(Base):
    __tablename__ = "projects"

    id: str = Column(String(6), primary_key=True, default=generate_id)
    name: str = Column(String(255), nullable=False)
    path: str = Column(Text, nullable=False, unique=True)
    integrations: str = Column(Text, default="{}")
    created_at: datetime = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "path": self.path,
            "integrations": self.integrations,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Task(Base):
    __tablename__ = "tasks"

    id: str = Column(String(6), primary_key=True, default=generate_id)
    project_id: str = Column(String(6), ForeignKey("projects.id"), nullable=False)
    name: str = Column(String(255), default="")
    description: str = Column(Text, default="")
    type: TaskType = Column(SQLEnum(TaskType), default=TaskType.FEATURE)
    worktree_branch: str = Column(String(255), default="")
    created_at: datetime = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    project = relationship("Project", back_populates="tasks")
    runs = relationship("TaskRun", back_populates="task", cascade="all, delete-orphan",
                        order_by="TaskRun.created_at")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "project_id": self.project_id,
            "name": self.name,
            "description": self.description,
            "type": self.type.value,
            "worktree_branch": self.worktree_branch,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Flow(Base):
    __tablename__ = "flows"

    id: str = Column(String(6), primary_key=True, default=generate_id)
    name: str = Column(String(255), nullable=False, unique=True)
    description: str = Column(Text, default="")
    created_at: datetime = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                                  onupdate=lambda: datetime.now(timezone.utc))

    steps = relationship("FlowStep", back_populates="flow", cascade="all, delete-orphan",
                         order_by="FlowStep.position")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "steps": [s.to_dict() for s in self.steps],
        }


class FlowStep(Base):
    __tablename__ = "flow_steps"

    id: str = Column(String(6), primary_key=True, default=generate_id)
    flow_id: str = Column(String(6), ForeignKey("flows.id"), nullable=False)
    name: str = Column(String(255), nullable=False)
    position: int = Column(Integer, nullable=False, default=0)
    content: str = Column(Text, default="")
    gates: str = Column(Text, default="[]")
    created_at: datetime = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                                  onupdate=lambda: datetime.now(timezone.utc))

    flow = relationship("Flow", back_populates="steps")

    def get_gates(self) -> list[dict]:
        """Parse gates JSON into a list of gate dicts."""
        import json
        try:
            return json.loads(self.gates or "[]")
        except (json.JSONDecodeError, TypeError):
            return []

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "flow_id": self.flow_id,
            "name": self.name,
            "position": self.position,
            "content": self.content,
            "gates": self.get_gates(),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class TaskRun(Base):
    __tablename__ = "task_runs"

    id: str = Column(String(6), primary_key=True, default=generate_id)
    project_id: str = Column(String(6), ForeignKey("projects.id"), nullable=False)
    task_id: str = Column(String(6), ForeignKey("tasks.id"), nullable=False)
    flow_name: str = Column(String(255), nullable=False, default="default")
    flow_chain: str = Column(Text, default="[]")
    current_step: str = Column(String(255), default="")
    outcome: str = Column(String(50), nullable=True)
    log_path: str = Column(Text, default="")
    user_prompt: str = Column(Text, default="")
    prompt: str = Column(Text, default="")
    summary: str = Column(Text, default="")
    steps_completed: str = Column(Text, default="[]")
    created_at: datetime = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    started_at: datetime = Column(DateTime, nullable=True)
    completed_at: datetime = Column(DateTime, nullable=True)

    task = relationship("Task", back_populates="runs")

    @property
    def status(self) -> str:
        if self.completed_at:
            return "completed"
        if self.started_at:
            return "running"
        return "queued"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "project_id": self.project_id,
            "task_id": self.task_id,
            "flow_name": self.flow_name,
            "flow_chain": self.flow_chain,
            "current_step": self.current_step,
            "status": self.status,
            "outcome": self.outcome,
            "log_path": self.log_path,
            "user_prompt": self.user_prompt,
            "prompt": self.prompt,
            "summary": self.summary,
            "steps_completed": self.steps_completed,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }
