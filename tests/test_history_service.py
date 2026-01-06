"""Tests for HistoryService."""

import json
import pytest
from datetime import datetime, timezone

from moderails.db.models import Epic, Task, TaskStatus
from moderails.services.history import HistoryService


class TestHistoryService:
    """Tests for HistoryService."""
    
    def test_sync_from_empty_file(self, test_db, temp_dir):
        """Test syncing when history file doesn't exist."""
        history_file = temp_dir / "history.jsonl"
        service = HistoryService(test_db, history_file)
        
        imported = service.sync_from_file()
        
        assert imported == 0
    
    def test_sync_imports_tasks(self, test_db, temp_dir):
        """Test importing tasks from history.jsonl (JSON Lines format)."""
        history_file = temp_dir / "history.jsonl"
        
        # Create history file (one JSON object per line)
        tasks = [
            {
                "name": "Test task 1",
                "summary": "First task summary",
                "files_changed": ["file1.py"],
                "completed_at": "2024-01-18T14:20:00Z"
            },
            {
                "name": "Test task 2",
                "summary": "Second task summary",
                "files_changed": ["file2.py"],
                "completed_at": "2024-01-19T15:30:00Z"
            }
        ]
        
        with open(history_file, 'w') as f:
            for task in tasks:
                f.write(json.dumps(task) + '\n')
        
        service = HistoryService(test_db, history_file)
        imported = service.sync_from_file()
        
        assert imported == 2
        
        # Check tasks were imported
        task1 = test_db.query(Task).filter(Task.name == "Test task 1").first()
        assert task1 is not None
        assert task1.summary == "First task summary"
        assert task1.status == TaskStatus.COMPLETED
        assert task1.epic_id is None
        
        task2 = test_db.query(Task).filter(Task.name == "Test task 2").first()
        assert task2 is not None
        # Epic is not imported from history.jsonl (local-only)
        assert task2.epic_id is None
    
    def test_sync_ignores_epic_from_history(self, test_db, temp_dir):
        """Test that sync ignores epic field from history.jsonl (epic_id is local-only)."""
        history_file = temp_dir / "history.jsonl"
        
        task_data = {
            "name": "Task with epic in history",
            "epic": "some-epic",
            "summary": "Summary",
            "files_changed": [],
            "completed_at": "2024-01-20T10:00:00Z"
        }
        
        with open(history_file, 'w') as f:
            f.write(json.dumps(task_data) + '\n')
        
        service = HistoryService(test_db, history_file)
        service.sync_from_file()
        
        # Epic field in history.jsonl is ignored (epic_id is local-only)
        task = test_db.query(Task).filter(Task.name == "Task with epic in history").first()
        assert task is not None
        assert task.epic_id is None
    
    def test_sync_skips_existing_tasks(self, test_db, temp_dir):
        """Test that sync doesn't duplicate existing tasks."""
        history_file = temp_dir / "history.jsonl"
        
        # Create task in DB
        task = Task(
            name="Existing task",
            file_name="task.md",
            status=TaskStatus.COMPLETED,
            summary="Original summary"
        )
        test_db.add(task)
        test_db.commit()
        
        # Create history file with same task (use task ID for matching)
        task_data = {
            "id": task.id,
            "name": "Existing task",
            "summary": "Different summary",
            "files_changed": [],
            "completed_at": "2024-01-20T10:00:00Z"
        }
        
        with open(history_file, 'w') as f:
            f.write(json.dumps(task_data) + '\n')
        
        service = HistoryService(test_db, history_file)
        imported = service.sync_from_file()
        
        assert imported == 0
        
        # Check task wasn't duplicated
        tasks = test_db.query(Task).filter(Task.name == "Existing task").all()
        assert len(tasks) == 1
        assert tasks[0].summary == "Original summary"  # Not overwritten
    
    def test_sync_tracks_mtime(self, test_db, temp_dir):
        """Test that sync tracks file modification time."""
        history_file = temp_dir / "history.jsonl"
        
        # Create empty history file
        history_file.touch()
        
        service = HistoryService(test_db, history_file)
        
        # First sync
        service.sync_from_file()
        
        # Second sync without file change
        imported = service.sync_from_file()
        assert imported == 0  # Skipped because mtime unchanged
    
    def test_export_task(self, test_db, temp_dir):
        """Test exporting a completed task to history.jsonl (JSON Lines format)."""
        history_file = temp_dir / "history.jsonl"
        
        # Create completed task
        task = Task(
            name="Completed task",
            file_name="task.md",
            status=TaskStatus.COMPLETED,
            summary="Task summary",
            git_hash="abc123",
            completed_at=datetime.now(timezone.utc)
        )
        test_db.add(task)
        test_db.commit()
        
        service = HistoryService(test_db, history_file)
        service.export_task(task.id)
        
        # Verify task was exported (read JSON Lines format)
        with open(history_file, 'r') as f:
            lines = f.readlines()
        
        assert len(lines) == 1
        exported_task = json.loads(lines[0])
        assert exported_task['name'] == "Completed task"
        assert exported_task['summary'] == "Task summary"
        # git_hash is NOT exported (local-only)
        assert 'git_hash' not in exported_task
        # epic is NOT exported (local-only)
        assert 'epic' not in exported_task
    
    def test_export_task_with_epic(self, test_db, temp_dir):
        """Test exporting task that belongs to an epic (epic not included in export)."""
        history_file = temp_dir / "history.jsonl"
        
        # Create epic and task
        epic = Epic(name="test-epic")
        test_db.add(epic)
        test_db.flush()
        
        task = Task(
            name="Epic task",
            file_name="task.md",
            epic_id=epic.id,
            status=TaskStatus.COMPLETED,
            summary="Task in epic",
            completed_at=datetime.now(timezone.utc)
        )
        test_db.add(task)
        test_db.commit()
        
        service = HistoryService(test_db, history_file)
        service.export_task(task.id)
        
        # Verify epic is NOT exported (epic_id is local only)
        with open(history_file, 'r') as f:
            lines = f.readlines()
        
        assert len(lines) == 1
        exported_task = json.loads(lines[0])
        # Epic is NOT exported to history.jsonl (local-only)
        assert 'epic' not in exported_task
        assert exported_task['name'] == "Epic task"
    
    def test_export_task_includes_files_changed(self, test_db, temp_dir):
        """Test that files_changed is included in export (from staged files)."""
        history_file = temp_dir / "history.jsonl"
        
        # Create completed task
        task = Task(
            name="Task with files",
            file_name="task.md",
            status=TaskStatus.COMPLETED,
            summary="Task summary",
            completed_at=datetime.now(timezone.utc)
        )
        test_db.add(task)
        test_db.commit()
        
        service = HistoryService(test_db, history_file)
        service.export_task(task.id)
        
        # Verify files_changed field exists
        with open(history_file, 'r') as f:
            lines = f.readlines()
        
        exported_task = json.loads(lines[0])
        # files_changed should be a list (may be empty if no staged files)
        assert isinstance(exported_task['files_changed'], list)
    
    def test_export_task_not_found(self, test_db, temp_dir):
        """Test exporting non-existent task raises error."""
        history_file = temp_dir / "history.jsonl"
        service = HistoryService(test_db, history_file)
        
        with pytest.raises(ValueError, match="not found"):
            service.export_task("fake123")
    
    def test_export_task_not_completed(self, test_db, temp_dir):
        """Test exporting incomplete task raises error."""
        history_file = temp_dir / "history.jsonl"
        
        task = Task(
            name="Incomplete task",
            file_name="task.md",
            status=TaskStatus.DRAFT
        )
        test_db.add(task)
        test_db.commit()
        
        service = HistoryService(test_db, history_file)
        
        with pytest.raises(ValueError, match="not completed"):
            service.export_task(task.id)
    
    def test_export_task_idempotent(self, test_db, temp_dir):
        """Test that exporting same task twice doesn't duplicate."""
        history_file = temp_dir / "history.jsonl"
        
        task = Task(
            name="Task",
            file_name="task.md",
            status=TaskStatus.COMPLETED,
            completed_at=datetime.now(timezone.utc)
        )
        test_db.add(task)
        test_db.commit()
        
        service = HistoryService(test_db, history_file)
        
        # Export twice
        service.export_task(task.id)
        service.export_task(task.id)
        
        # Should only have one line (not duplicated)
        with open(history_file, 'r') as f:
            lines = [line for line in f.readlines() if line.strip()]
        
        assert len(lines) == 1
    
    def test_search_by_file(self, test_db, temp_dir):
        """Test searching tasks by file path."""
        history_file = temp_dir / "history.jsonl"
        
        # Create task with file in summary
        task = Task(
            name="Task 1",
            file_name="task.md",
            summary="Modified auth/login.py",
            status=TaskStatus.COMPLETED
        )
        test_db.add(task)
        test_db.commit()
        
        service = HistoryService(test_db, history_file)
        results = service.search_by_file("auth/login.py")
        
        assert len(results) == 1
        assert results[0]['name'] == "Task 1"
    
    def test_search_by_query(self, test_db, temp_dir):
        """Test searching tasks by keyword."""
        history_file = temp_dir / "history.jsonl"
        
        # Create tasks
        task1 = Task(
            name="Add authentication",
            file_name="task1.md",
            summary="Implemented JWT tokens",
            status=TaskStatus.COMPLETED
        )
        task2 = Task(
            name="Fix bug",
            file_name="task2.md",
            summary="Fixed database connection",
            status=TaskStatus.DRAFT
        )
        test_db.add_all([task1, task2])
        test_db.commit()
        
        service = HistoryService(test_db, history_file)
        
        # Search for "authentication"
        results = service.search_by_query("authentication")
        assert len(results) == 1
        assert results[0]['name'] == "Add authentication"
        
        # Search for "JWT"
        results = service.search_by_query("JWT")
        assert len(results) == 1
        assert results[0]['name'] == "Add authentication"
    
    def test_search_case_insensitive(self, test_db, temp_dir):
        """Test search is case-insensitive."""
        history_file = temp_dir / "history.jsonl"
        
        task = Task(
            name="Task",
            file_name="task.md",
            summary="Implemented Authentication",
            status=TaskStatus.COMPLETED
        )
        test_db.add(task)
        test_db.commit()
        
        service = HistoryService(test_db, history_file)
        
        # Search with different cases
        results1 = service.search_by_query("authentication")
        results2 = service.search_by_query("AUTHENTICATION")
        results3 = service.search_by_query("Authentication")
        
        assert len(results1) == 1
        assert len(results2) == 1
        assert len(results3) == 1

