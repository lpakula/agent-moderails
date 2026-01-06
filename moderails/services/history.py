"""History service - manages history.jsonl exports and imports."""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

from ..db.models import Task, TaskStatus, TaskType
from ..utils.git import get_name_status


class HistoryService:
    def __init__(self, session: Session, history_file: Path):
        self.session = session
        self.history_file = history_file
        self._last_mtime: Optional[float] = None
    
    def sync_from_file(self) -> int:
        """Import completed tasks from history.jsonl to DB.
        
        History file format: one JSON object per line (JSON Lines).
        
        Returns:
            Number of tasks imported
        """
        if not self.history_file.exists():
            return 0
        
        # Check if file has changed since last sync
        current_mtime = self.history_file.stat().st_mtime
        if self._last_mtime is not None and current_mtime == self._last_mtime:
            return 0
        
        imported_count = 0
        
        with open(self.history_file, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                task_data = json.loads(line)
                task_id = task_data.get('id')
                
                # Check if task already exists (by id if available)
                if task_id:
                    existing_task = self.session.query(Task).filter(Task.id == task_id).first()
                else:
                    # Fallback to name for old history entries
                    existing_task = self.session.query(Task).filter(Task.name == task_data['name']).first()
                
                if existing_task:
                    continue
                
                # Epic is not stored in history.jsonl (local only)
                epic_id = None
                
                # Create task
                task_name = task_data['name']
                sanitized_name = task_name.lower().replace(' ', '-')
                
                # Get task type, default to FEATURE for old history entries
                task_type = TaskType(task_data.get('type', 'feature'))
                
                task = Task(
                    id=task_id if task_id else None,  # Will auto-generate if None
                    name=task_name,
                    file_name=f"{sanitized_name}.md",
                    summary=task_data.get('summary', ''),
                    type=task_type,
                    status=TaskStatus.COMPLETED,
                    completed_at=datetime.fromisoformat(task_data['completed_at']) if task_data.get('completed_at') else None,
                    epic_id=epic_id,
                )
                self.session.add(task)
                imported_count += 1
        
        if imported_count > 0:
            self.session.commit()
        
        self._last_mtime = current_mtime
        return imported_count
    
    def export_task(self, task_id: str) -> None:
        """Export completed task to history.jsonl.
        
        Appends task as a single line (JSON Lines format).
        """
        task = self.session.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise ValueError(f"Task '{task_id}' not found")
        
        if task.status != TaskStatus.COMPLETED:
            raise ValueError(f"Task '{task_id}' is not completed")
        
        # Check if task already exported (by reading existing lines)
        if self.history_file.exists():
            with open(self.history_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        existing_task = json.loads(line)
                        if existing_task.get('id') == task.id:
                            return  # Already exported
                    except json.JSONDecodeError:
                        continue
        
        # Extract files changed from git diff
        files_changed = []
        if task.git_hash:
            name_status = get_name_status(task.git_hash)
            if name_status:
                # Parse git name-status output
                # Format: "A\tfile.py" or "M\tfile.py" or "R100\told.py\tnew.py"
                for line in name_status.splitlines():
                    if not line.strip():
                        continue
                    parts = line.split('\t')
                    if len(parts) >= 2:
                        status = parts[0]
                        if status.startswith('R'):  # Rename: use new filename
                            files_changed.append(parts[2] if len(parts) > 2 else parts[1])
                        else:  # Add/Modify/Delete: use filename
                            files_changed.append(parts[1])
        
        # Prepare task data (git_hash and epic_id stored only in local DB, not in shared history.jsonl)
        task_data = {
            "id": task.id,
            "name": task.name,
            "type": task.type.value,
            "summary": task.summary,
            "files_changed": files_changed,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
        }
        
        # Append as single line (JSON Lines format)
        with open(self.history_file, 'a') as f:
            f.write(json.dumps(task_data) + '\n')
        
        self._last_mtime = self.history_file.stat().st_mtime
    
    def search_by_file(self, file_path: str) -> list[dict]:
        """Search tasks (all statuses) that touched this file."""
        # Search in DB
        tasks = self.session.query(Task).all()
        results = []
        
        for task in tasks:
            # Check if file is in files_changed (from history.jsonl or git_hash)
            # For now, we'll search by summary/name containing the file path
            if file_path in task.summary or file_path in task.file_name:
                results.append({
                    "name": task.name,
                    "status": task.status.value,
                    "epic": task.epic.name if task.epic else None,
                    "summary": task.summary,
                    "git_hash": task.git_hash,
                    "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                })
        
        # Also search history.jsonl for files_changed field (JSON Lines format)
        if self.history_file.exists():
            with open(self.history_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        task_data = json.loads(line)
                        if file_path in task_data.get('files_changed', []):
                            # Check if not already in results
                            if not any(r['name'] == task_data['name'] for r in results):
                                results.append({
                                    "name": task_data['name'],
                                    "status": "completed",
                                    "epic": task_data.get('epic'),
                                    "summary": task_data.get('summary', ''),
                                    "git_hash": task_data.get('git_hash', ''),
                                    "completed_at": task_data.get('completed_at'),
                                    "files_changed": task_data.get('files_changed', []),
                                })
                    except json.JSONDecodeError:
                        continue
        
        return results
    
    def search_by_query(self, query: str) -> list[dict]:
        """Full-text search in task summaries (all statuses).
        
        Supports OR search with multiple terms separated by | (pipe).
        Example: "auth|user" matches tasks containing "auth" OR "user"
        """
        # Split query by | for OR search
        query_terms = [term.strip().lower() for term in query.split('|')]
        tasks = self.session.query(Task).all()
        results = []
        
        for task in tasks:
            task_name_lower = task.name.lower()
            task_summary_lower = task.summary.lower()
            
            # Check if any query term matches (OR logic)
            if any(term in task_name_lower or term in task_summary_lower for term in query_terms):
                results.append({
                    "name": task.name,
                    "status": task.status.value,
                    "epic": task.epic.name if task.epic else None,
                    "summary": task.summary,
                    "git_hash": task.git_hash,
                    "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                })
        
        return results

