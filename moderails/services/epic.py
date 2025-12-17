"""Epic service - CRUD operations for epics."""

from typing import Optional

from sqlalchemy.orm import Session

from ..db.models import Epic, Task, TaskStatus


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
    
    def get_summary(self, name: str) -> str:
        """Get epic summary from completed task summaries."""
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
        
        parts = [f"# Epic: {epic.name}\n"]
        for t in tasks:
            parts.append(f"- **{t.name}**: {t.summary}")
        
        return "\n".join(parts)
