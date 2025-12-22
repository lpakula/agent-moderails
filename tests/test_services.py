"""Tests for service modules."""

import pytest
from pathlib import Path

from moderails.db.models import Epic, Task, TaskStatus
from moderails.services.epic import EpicService
from moderails.services.task import TaskService
from moderails.services.context import ContextService


class TestEpicService:
    """Tests for EpicService."""
    
    def test_create_epic(self, test_db):
        """Test creating an epic."""
        service = EpicService(test_db)
        
        epic = service.create("test-epic", "backend")
        
        assert epic.name == "test-epic"
        assert epic.tag == "backend"
        assert epic.id is not None
    
    def test_get_epic(self, test_db):
        """Test getting an epic by ID."""
        service = EpicService(test_db)
        created = service.create("test-epic", "")
        
        found = service.get(created.id)
        
        assert found is not None
        assert found.id == created.id
    
    def test_get_by_name(self, test_db):
        """Test getting an epic by name."""
        service = EpicService(test_db)
        service.create("my-epic", "")
        
        found = service.get_by_name("my-epic")
        
        assert found is not None
        assert found.name == "my-epic"
    
    def test_list_all(self, test_db):
        """Test listing all epics."""
        service = EpicService(test_db)
        service.create("epic1", "")
        service.create("epic2", "backend")
        
        epics = service.list_all()
        
        assert len(epics) == 2
    
    def test_update_epic(self, test_db):
        """Test updating an epic."""
        service = EpicService(test_db)
        service.create("test-epic", "old-tag")
        
        updated = service.update("test-epic", tag="new-tag")
        
        assert updated is not None
        assert updated.tag == "new-tag"
    
    def test_delete_epic(self, test_db):
        """Test deleting an epic."""
        service = EpicService(test_db)
        service.create("to-delete", "")
        
        result = service.delete("to-delete")
        
        assert result is True
        assert service.get_by_name("to-delete") is None
    
    def test_get_summary_no_tasks(self, test_db):
        """Test getting summary for epic with no completed tasks."""
        service = EpicService(test_db)
        epic = service.create("empty-epic", "")
        
        summary = service.get_summary("empty-epic")
        
        assert "empty-epic" in summary
        assert "No completed tasks yet" in summary
    
    def test_get_summary_with_tasks(self, test_db):
        """Test getting summary with completed tasks."""
        epic_service = EpicService(test_db)
        epic = epic_service.create("test-epic", "")
        
        task = Task(
            name="completed-task",
            file_name="task.md",
            epic_id=epic.id,
            status=TaskStatus.COMPLETED,
            summary="Task summary"
        )
        test_db.add(task)
        test_db.commit()
        
        summary = epic_service.get_summary("test-epic")
        
        assert "test-epic" in summary
        assert "Completed Tasks" in summary
        assert "completed-task" in summary
        assert "Task summary" in summary
    
    def test_get_summary_short_format(self, test_db):
        """Test getting summary in short format."""
        epic_service = EpicService(test_db)
        epic = epic_service.create("test-epic", "")
        
        task = Task(
            name="task",
            file_name="t.md",
            epic_id=epic.id,
            status=TaskStatus.COMPLETED,
            summary="Summary",
            git_hash="abc123"
        )
        test_db.add(task)
        test_db.commit()
        
        summary = epic_service.get_summary("test-epic", short=True)
        
        assert "test-epic" in summary
        # In short format, should show "Files Changed" not "Code Changes"
        # (though without real git repo, files section may be empty)


class TestTaskService:
    """Tests for TaskService."""
    
    def test_create_task(self, test_db, temp_dir):
        """Test creating a task."""
        epic_service = EpicService(test_db)
        epic_service.create("test-epic", "")
        
        task_service = TaskService(test_db, temp_dir)
        task = task_service.create("test-task", "test-epic")
        
        assert task.name == "test-task"
        assert task.file_name == "test-task.md"
        assert task.status == TaskStatus.TODO
    
    def test_create_task_creates_file(self, test_db, temp_dir):
        """Test that creating task creates the file."""
        epic_service = EpicService(test_db)
        epic_service.create("test-epic", "")
        
        task_service = TaskService(test_db, temp_dir)
        task = task_service.create("test-task", "test-epic")
        
        task_file = temp_dir / "tasks" / "test-epic" / "test-task.md"
        assert task_file.exists()
    
    def test_get_task(self, test_db, temp_dir):
        """Test getting a task by ID."""
        epic_service = EpicService(test_db)
        epic_service.create("test-epic", "")
        
        task_service = TaskService(test_db, temp_dir)
        created = task_service.create("test-task", "test-epic")
        
        found = task_service.get(created.id)
        
        assert found is not None
        assert found.id == created.id
    
    def test_get_by_name(self, test_db, temp_dir):
        """Test getting task by name."""
        epic_service = EpicService(test_db)
        epic_service.create("test-epic", "")
        
        task_service = TaskService(test_db, temp_dir)
        task_service.create("my-task", "test-epic")
        
        found = task_service.get_by_name("my-task")
        
        assert found is not None
        assert found.name == "my-task"
    
    def test_list_all_tasks(self, test_db, temp_dir):
        """Test listing all tasks."""
        epic_service = EpicService(test_db)
        epic_service.create("epic1", "")
        epic_service.create("epic2", "")
        
        task_service = TaskService(test_db, temp_dir)
        task_service.create("task1", "epic1")
        task_service.create("task2", "epic2")
        
        tasks = task_service.list_all()
        
        assert len(tasks) == 2
    
    def test_list_tasks_by_epic(self, test_db, temp_dir):
        """Test listing tasks filtered by epic."""
        epic_service = EpicService(test_db)
        epic_service.create("epic1", "")
        epic_service.create("epic2", "")
        
        task_service = TaskService(test_db, temp_dir)
        task_service.create("task1", "epic1")
        task_service.create("task2", "epic2")
        
        tasks = task_service.list_all(epic_name="epic1")
        
        assert len(tasks) == 1
        assert tasks[0].name == "task1"
    
    def test_update_task(self, test_db, temp_dir):
        """Test updating a task."""
        epic_service = EpicService(test_db)
        epic_service.create("test-epic", "")
        
        task_service = TaskService(test_db, temp_dir)
        task_service.create("test-task", "test-epic")
        
        updated = task_service.update(
            "test-task",
            status=TaskStatus.IN_PROGRESS,
            summary="New summary"
        )
        
        assert updated is not None
        assert updated.status == TaskStatus.IN_PROGRESS
        assert updated.summary == "New summary"
    
    def test_delete_task(self, test_db, temp_dir):
        """Test deleting a task."""
        epic_service = EpicService(test_db)
        epic_service.create("test-epic", "")
        
        task_service = TaskService(test_db, temp_dir)
        task_service.create("to-delete", "test-epic")
        
        result = task_service.delete("to-delete")
        
        assert result is True
        assert task_service.get_by_name("to-delete") is None
    
    def test_get_task_content(self, test_db, temp_dir):
        """Test getting task file content."""
        epic_service = EpicService(test_db)
        epic_service.create("test-epic", "")
        
        task_service = TaskService(test_db, temp_dir)
        task_service.create("test-task", "test-epic")
        
        content = task_service.get_task_content("test-task")
        
        assert content is not None
        assert "# TASK NAME" in content
        assert "SUMMARY" in content


class TestContextService:
    """Tests for ContextService."""
    
    def test_load_mandatory_context(self, temp_dir):
        """Test loading mandatory context files."""
        context_dir = temp_dir / "context"
        context_dir.mkdir()
        
        # Create mandatory context file
        (context_dir / "overview.md").write_text("# Project Overview\nThis is the overview.")
        
        service = ContextService(temp_dir)
        content = service.load_for_tags([])
        
        assert "Project Overview" in content
        assert "overview.md (mandatory)" in content
    
    def test_load_tag_specific_context(self, temp_dir):
        """Test loading tag-specific context files."""
        context_dir = temp_dir / "context"
        context_dir.mkdir()
        
        # Create tag-specific context
        backend_dir = context_dir / "backend"
        backend_dir.mkdir()
        (backend_dir / "guide.md").write_text("# Backend Guide\nBackend info.")
        
        service = ContextService(temp_dir)
        content = service.load_for_tags(["backend"])
        
        assert "Backend Guide" in content
        assert "backend/guide.md" in content
    
    def test_load_multiple_tags(self, temp_dir):
        """Test loading context for multiple tags."""
        context_dir = temp_dir / "context"
        context_dir.mkdir()
        
        # Create multiple tag contexts
        for tag in ["api", "auth"]:
            tag_dir = context_dir / tag
            tag_dir.mkdir()
            (tag_dir / f"{tag}.md").write_text(f"# {tag.upper()}\nContent.")
        
        service = ContextService(temp_dir)
        content = service.load_for_tags(["api", "auth"])
        
        assert "API" in content
        assert "AUTH" in content
    
    def test_no_context_directory(self, temp_dir):
        """Test when context directory doesn't exist."""
        service = ContextService(temp_dir)
        content = service.load_for_tags(["test"])
        
        assert content == ""

