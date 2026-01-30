"""Task service - CRUD and file management for tasks."""

from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

from ..db.models import Epic, Task, TaskStatus, TaskType
from ..modes import get_task_template


class TaskService:
    def __init__(self, session: Session, moderails_dir: Path):
        self.session = session
        self.moderails_dir = moderails_dir
    
    def _sanitize_name(self, name: str) -> str:
        return name.lower().replace(" ", "-").replace("/", "-")
    
    def create(
        self,
        name: str,
        epic_id: Optional[str] = None,
        summary: str = "",
        task_type: TaskType = TaskType.FEATURE,
        status: TaskStatus = TaskStatus.IN_PROGRESS,
    ) -> Task:
        """Create a new task. Epic is optional (provide epic ID). Both task and epic names can contain spaces.
        
        Plan file is NOT created here - it's created when entering #plan mode.
        
        Args:
            name: Task name (max 50 characters)
            epic_id: Optional epic ID
            summary: Task summary
            task_type: Task type (feature, fix, refactor, chore)
            status: Initial task status (default: in-progress)
        """
        
        # Validate task name length
        if len(name) > 50:
            raise ValueError(f"Task name must be 50 characters or less (got {len(name)})")
        
        # Enforce single in-progress task when creating as in-progress
        if status == TaskStatus.IN_PROGRESS:
            existing = self.session.query(Task).filter(
                Task.status == TaskStatus.IN_PROGRESS
            ).first()
            if existing:
                raise ValueError(
                    f"Task '{existing.id}' ({existing.name}) is already in-progress. "
                    f"Complete or abort it first."
                )
        
        # Validate epic if provided
        epic = None
        if epic_id:
            epic = self.session.query(Epic).filter(Epic.id == epic_id).first()
            if not epic:
                raise ValueError(f"Epic with ID '{epic_id}' not found")
        
        # Create task - file_name stays empty until plan mode
        task = Task(
            name=name,
            file_name="",  # Will be set when entering #plan mode
            summary=summary,
            type=task_type,
            epic_id=epic_id,
            status=status,
        )
        self.session.add(task)
        self.session.commit()
        self.session.refresh(task)
        return task
    
    def create_plan_file(self, task_id: str) -> Optional[str]:
        """Create plan file for a task. Called when entering #plan mode.
        
        Returns:
            File path if created, None if task not found
        """
        task = self.get(task_id)
        if not task:
            return None
        
        # If file already exists, just return the path
        if task.file_name:
            return task.file_name
        
        # Generate file path
        sanitized_name = self._sanitize_name(task.name)
        filename_base = f"{sanitized_name}-{task.id}.plan.md"
        
        if task.epic:
            epic_folder = self._sanitize_name(task.epic.name)
            tasks_dir = self.moderails_dir / "tasks" / epic_folder
            file_name = f"tasks/{epic_folder}/{filename_base}"
        else:
            tasks_dir = self.moderails_dir / "tasks"
            file_name = f"tasks/{filename_base}"
        
        # Create directory and file
        tasks_dir.mkdir(parents=True, exist_ok=True)
        task_file = tasks_dir / filename_base
        
        template = get_task_template()
        content = template.format(name=task.name, summary=task.summary or "[task purpose]")
        task_file.write_text(content)
        
        # Update task with file path
        task.file_name = file_name
        self.session.commit()
        
        return file_name
    
    def get(self, task_id: str) -> Optional[Task]:
        """Get task by 6-character task ID."""
        return self.session.query(Task).filter(Task.id == task_id).first()
    
    def get_by_name(self, name: str) -> Optional[Task]:
        """Get task by name (for backwards compatibility)."""
        return self.session.query(Task).filter(Task.name == name).first()
    
    def list_all(self, epic_name: Optional[str] = None, status: Optional[TaskStatus] = None) -> list[Task]:
        query = self.session.query(Task)
        if epic_name:
            epic = self.session.query(Epic).filter(Epic.name == epic_name).first()
            if not epic:
                return []  # Epic not found, return empty list
            query = query.filter(Task.epic_id == epic.id)
        if status:
            query = query.filter(Task.status == status)
        return query.all()
    
    def update(
        self,
        task_id: str,
        name: Optional[str] = None,
        status: Optional[TaskStatus] = None,
        task_type: Optional[TaskType] = None,
        summary: Optional[str] = None,
        git_hash: Optional[str] = None,
        file_name: Optional[str] = None,
    ) -> Optional[Task]:
        task = self.get(task_id)
        if not task:
            return None
        
        # Enforce single in-progress task
        if status == TaskStatus.IN_PROGRESS:
            existing = self.session.query(Task).filter(
                Task.status == TaskStatus.IN_PROGRESS,
                Task.id != task_id
            ).first()
            if existing:
                raise ValueError(
                    f"Task '{existing.id}' ({existing.name}) is already in-progress. "
                    f"Complete or abort it first."
                )
        
        if name is not None:
            task.name = name
        if status:
            task.status = status
            if status == TaskStatus.COMPLETED:
                task.completed_at = datetime.now(timezone.utc)
        if task_type is not None:
            task.type = task_type
        if summary is not None:
            task.summary = summary
        if git_hash:
            task.git_hash = git_hash
        if file_name is not None:
            task.file_name = file_name
        
        self.session.commit()
        self.session.refresh(task)
        return task
    
    def delete(self, task_id: str) -> bool:
        task = self.get(task_id)
        if not task:
            return False
        
        # Delete task file if it exists
        if task.file_name:
            task_file = self.moderails_dir / task.file_name
            if task_file.exists():
                task_file.unlink()
        
        self.session.delete(task)
        self.session.commit()
        return True
    
    def get_task_content(self, task_id: str) -> Optional[str]:
        task = self.get(task_id)
        if not task:
            return None
        
        # Task file is directly in _moderails/
        task_file = self.moderails_dir / task.file_name
        
        return task_file.read_text() if task_file.exists() else None
    
    def complete(self, task_id: str, git_hash: Optional[str] = None) -> Task:
        """Mark task as completed and export to history.jsonl.
        
        Args:
            task_id: 6-character task ID
            git_hash: Git commit hash for the completed work
            
        Returns:
            Updated task
            
        Raises:
            ValueError: If task not found
        """
        task = self.get(task_id)
        if not task:
            raise ValueError(f"Task '{task_id}' not found")
        
        # Update task
        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.now(timezone.utc)
        if git_hash:
            task.git_hash = git_hash
        
        self.session.commit()
        self.session.refresh(task)
        
        
        return task
