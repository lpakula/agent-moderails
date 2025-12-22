"""Epic service - CRUD operations for epics."""

from typing import Optional

from sqlalchemy.orm import Session

from ..db.models import Epic, Task, TaskStatus
from ..utils.git import generate_epic_diff, generate_epic_files_changed, get_name_status


class EpicService:
    def __init__(self, session: Session):
        self.session = session
    
    def create(self, name: str, tag: str = "") -> Epic:
        epic = Epic(name=name, tag=tag)
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
    
    def update(self, name: str, tag: Optional[str] = None) -> Optional[Epic]:
        epic = self.get_by_name(name)
        if not epic:
            return None
        if tag is not None:
            epic.tag = tag
        self.session.commit()
        self.session.refresh(epic)
        return epic
    
    def delete(self, name: str) -> bool:
        epic = self.get_by_name(name)
        if not epic:
            return False
        self.session.delete(epic)
        self.session.commit()
        return True
    
    def get_summary(self, name: str, short: bool = False) -> str:
        """
        Get epic summary from completed task summaries and git diffs.
        
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
        parts = [f"# Epic: {epic.name}\n", "## Completed Tasks\n"]
        
        for idx, task in enumerate(tasks, 1):
            # Task header with number and date
            date_str = task.completed_at.strftime("%b %d") if task.completed_at else "unknown date"
            parts.append(f"\n### {idx}. {task.name} ({date_str})\n")
            parts.append(f"**Summary**: {task.summary}\n")
            
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
        
        return "\n".join(parts)
