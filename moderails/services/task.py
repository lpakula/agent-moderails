"""Task service - CRUD and file management for tasks."""

from datetime import datetime
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

from ..db.models import Epic, Task, TaskStatus
from ..rules import get_task_template


class TaskService:
    def __init__(self, session: Session, moderails_dir: Path):
        self.session = session
        self.moderails_dir = moderails_dir
        self.tasks_dir = moderails_dir / "tasks"
    
    def _ensure_epic_dir(self, epic_name: str) -> Path:
        epic_dir = self.tasks_dir / epic_name
        epic_dir.mkdir(parents=True, exist_ok=True)
        return epic_dir
    
    def _sanitize_name(self, name: str) -> str:
        return name.lower().replace(" ", "-").replace("/", "-")
    
    def create(
        self,
        name: str,
        epic_name: str,
        tags: Optional[str] = None,
        summary: str = "",
    ) -> Task:
        """Create a new task with its file."""
        epic = self.session.query(Epic).filter(Epic.name == epic_name).first()
        if not epic:
            epic = Epic(name=epic_name, tag=tags or "")
            self.session.add(epic)
            self.session.commit()
            self.session.refresh(epic)
        
        file_name = f"{self._sanitize_name(name)}.md"
        epic_dir = self._ensure_epic_dir(epic_name)
        task_file = epic_dir / file_name
        
        template = get_task_template()
        content = template.format(name=name, summary=summary or "[task purpose]")
        task_file.write_text(content)
        
        task = Task(
            name=name,
            file_name=file_name,
            summary=summary,
            epic_id=epic.id,
            status=TaskStatus.TODO,
        )
        self.session.add(task)
        self.session.commit()
        self.session.refresh(task)
        return task
    
    def get(self, task_id: str) -> Optional[Task]:
        return self.session.query(Task).filter(Task.id == task_id).first()
    
    def get_by_name(self, name: str) -> Optional[Task]:
        return self.session.query(Task).filter(Task.name == name).first()
    
    def list_all(self, epic_name: Optional[str] = None, status: Optional[TaskStatus] = None) -> list[Task]:
        query = self.session.query(Task)
        if epic_name:
            epic = self.session.query(Epic).filter(Epic.name == epic_name).first()
            if epic:
                query = query.filter(Task.epic_id == epic.id)
        if status:
            query = query.filter(Task.status == status)
        return query.all()
    
    def update(
        self,
        name: str,
        status: Optional[TaskStatus] = None,
        summary: Optional[str] = None,
        git_hash: Optional[str] = None,
    ) -> Optional[Task]:
        task = self.get_by_name(name)
        if not task:
            return None
        
        if status:
            task.status = status
            if status == TaskStatus.COMPLETED:
                task.completed_at = datetime.utcnow()
        if summary is not None:
            task.summary = summary
        if git_hash:
            task.git_hash = git_hash
        
        self.session.commit()
        self.session.refresh(task)
        return task
    
    def delete(self, name: str) -> bool:
        task = self.get_by_name(name)
        if not task:
            return False
        
        task_file = self.tasks_dir / task.epic.name / task.file_name
        if task_file.exists():
            task_file.unlink()
        
        self.session.delete(task)
        self.session.commit()
        return True
    
    def get_task_content(self, name: str) -> Optional[str]:
        task = self.get_by_name(name)
        if not task:
            return None
        task_file = self.tasks_dir / task.epic.name / task.file_name
        return task_file.read_text() if task_file.exists() else None
