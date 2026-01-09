"""Epic service - CRUD operations for epics."""

import re
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

from ..db.models import Epic, Task, TaskStatus
from ..utils.git import generate_epic_diff, generate_epic_files_changed, get_name_status


def is_valid_slug(name: str) -> bool:
    """Check if name is a valid slug (lowercase letters, numbers, and dashes only)."""
    return bool(re.match(r'^[a-z0-9]+(-[a-z0-9]+)*$', name))


class EpicService:
    def __init__(self, session: Session, moderails_dir: Optional[Path] = None):
        self.session = session
        self.moderails_dir = moderails_dir
    
    def create(self, name: str) -> Epic:
        """Create a new epic with a slug name (lowercase letters, numbers, and dashes only)."""
        if not is_valid_slug(name):
            raise ValueError("Epic name must be a slug (lowercase letters, numbers, and dashes only, e.g., 'my-epic')")
        
        epic = Epic(name=name)
        self.session.add(epic)
        self.session.commit()
        self.session.refresh(epic)
        return epic
    
    def get(self, epic_id: str) -> Optional[Epic]:
        return self.session.query(Epic).filter(Epic.id == epic_id).first()
    
    def get_by_name(self, name: str) -> Optional[Epic]:
        return self.session.query(Epic).filter(Epic.name == name).first()
    
    def list_all(self) -> list[Epic]:
        return self.session.query(Epic).all()
    
    def update(self, name: str) -> Optional[Epic]:
        """Update epic. Note: Epics are permanent containers and cannot be deleted."""
        epic = self.get_by_name(name)
        if not epic:
            return None
        # Epics only have name, nothing to update currently
        self.session.commit()
        self.session.refresh(epic)
        return epic
    
    def get_summary(self, name: str, short: bool = False) -> str:
        """
        Get epic summary from completed task summaries, task files, and git diffs.
        
        Args:
            name: Epic name
            short: If True, show only filenames. If False, show full diffs per task.
        """
        epic = self.get_by_name(name)
        if not epic:
            return ""
        
        # Get completed tasks in order
        tasks = (
            self.session.query(Task)
            .filter(Task.epic_id == epic.id, Task.status == TaskStatus.COMPLETED)
            .order_by(Task.completed_at)
            .all()
        )
        
        if not tasks:
            return f"# Epic: {epic.name}\n\nNo completed tasks yet."
        
        # Build epic summary with per-task details
        task_parts = []
        
        for idx, task in enumerate(tasks, 1):
            parts = []
            
            # Task header with number and date
            date_str = task.completed_at.strftime("%b %d") if task.completed_at else "unknown date"
            parts.append(f"### {idx}. {task.name} ({date_str})\n")
            parts.append(f"**Summary**: {task.summary}\n")
            
            # Include task file content if exists
            if self.moderails_dir and task.file_name:
                task_file = self.moderails_dir / task.file_name
                if task_file.exists():
                    try:
                        task_content = task_file.read_text().strip()
                        if task_content:
                            parts.append("**Task Plan**:\n")
                            parts.append(task_content)
                            parts.append("")
                    except Exception:
                        pass
            
            # Show files and diffs if git hash exists
            if task.git_hash and task.git_hash.strip():
                git_hash = task.git_hash.strip()
                
                if short:
                    # Short format: only filenames for this task
                    files_changed = generate_epic_files_changed([git_hash])
                    if files_changed:
                        parts.append("**Files changed**:")
                        parts.append(files_changed)
                else:
                    # Full format: show diff for this task
                    name_status = get_name_status(git_hash)
                    if name_status:
                        parts.append("**Files changed**:")
                        for line in name_status.splitlines():
                            parts.append(f"  {line}")
                        parts.append("")
                    
                    task_diff = generate_epic_diff([git_hash])
                    if task_diff:
                        parts.append("**Changes**:")
                        parts.append(task_diff)
            
            task_parts.append("\n".join(parts))
        
        # Join with separators
        header = f"# Epic: {epic.name}\n\n## Completed Tasks\n"
        return header + "\n---\n\n".join(task_parts)
