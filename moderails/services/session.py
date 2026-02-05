"""Session service - manages working sessions for tasks."""

from pathlib import Path
from typing import Any, Optional

from sqlalchemy.orm import Session as DBSession

from ..db.models import Session, Task, TaskStatus


class SessionService:
    """Manages working sessions for tasks.
    
    Only one active session at a time - all methods operate on the current active session.
    Sessions are created when a task becomes in-progress and deleted when completed.
    """
    
    def __init__(self, db_session: DBSession, moderails_dir: Path):
        self.db_session = db_session
        self.moderails_dir = moderails_dir
    
    def get_active(self) -> Optional[Session]:
        """Get the active session (for the current in-progress task).
        
        Returns:
            Active session or None if no in-progress task
        """
        # Find the in-progress task
        task = self.db_session.query(Task).filter(
            Task.status == TaskStatus.IN_PROGRESS
        ).first()
        
        if not task:
            return None
        
        # Find its session
        return self.db_session.query(Session).filter(
            Session.task_id == task.id
        ).first()
    
    def ensure_active(self, task_id: str) -> Session:
        """Ensure a session exists for the given task, creating if needed.
        
        Args:
            task_id: The task ID to create/get session for
            
        Returns:
            The session (existing or newly created)
        """
        # Check if session already exists
        existing = self.db_session.query(Session).filter(
            Session.task_id == task_id
        ).first()
        
        if existing:
            return existing
        
        # Create new session
        session = Session(task_id=task_id, current_mode="start")
        self.db_session.add(session)
        self.db_session.commit()
        self.db_session.refresh(session)
        return session
    
    def set_mode(self, mode: str) -> Optional[Session]:
        """Update the current mode on the active session.
        
        Args:
            mode: The new mode name (start, research, plan, execute, complete, fast, etc.)
            
        Returns:
            Updated session or None if no active session
        """
        session = self.get_active()
        if not session:
            return None
        
        session.current_mode = mode
        self.db_session.commit()
        self.db_session.refresh(session)
        return session
    
    def add_memory(self, memory_name: str) -> bool:
        """Add a memory to the active session's loaded memories.
        
        Args:
            memory_name: Name of the memory to add
            
        Returns:
            True if added, False if no active session or already loaded
        """
        session = self.get_active()
        if not session:
            return False
        
        if session.add_memory(memory_name):
            self.db_session.commit()
            return True
        return False
    
    def get_memories(self) -> list[str]:
        """Get list of loaded memory names for the active session.
        
        Returns:
            List of memory names, empty if no active session
        """
        session = self.get_active()
        if not session:
            return []
        return session.get_memories()
    
    def delete(self) -> bool:
        """Delete the active session.
        
        Called when task completes - session is no longer needed.
        
        Returns:
            True if deleted, False if no active session
        """
        session = self.get_active()
        if not session:
            return False
        
        self.db_session.delete(session)
        self.db_session.commit()
        return True
    
    def delete_for_task(self, task_id: str) -> bool:
        """Delete the session for a specific task.
        
        Args:
            task_id: The task ID whose session should be deleted
            
        Returns:
            True if deleted, False if no session existed
        """
        session = self.db_session.query(Session).filter(
            Session.task_id == task_id
        ).first()
        
        if not session:
            return False
        
        self.db_session.delete(session)
        self.db_session.commit()
        return True
    
    def get_full_context(self) -> Optional[dict[str, Any]]:
        """Get full context for session show command.
        
        Returns:
            Dict with all session context, or None if no active session
        """
        session = self.get_active()
        if not session:
            return None
        
        task = session.task
        epic = task.epic if task else None
        
        return {
            "session": session.to_dict(),
            "task": task.to_dict() if task else None,
            "epic": epic.to_dict() if epic else None,
            "current_mode": session.current_mode,
            "loaded_memories": session.get_memories(),
            "epic_skills": epic.get_skills() if epic else [],
        }
