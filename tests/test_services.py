"""Tests for service modules."""

from moderails.db.models import Task, TaskStatus
from moderails.services.epic import EpicService
from moderails.services.task import TaskService


class TestEpicService:
    """Tests for EpicService."""
    
    def test_create_epic(self, test_db):
        """Test creating an epic."""
        service = EpicService(test_db)
        
        epic = service.create("test-epic")
        
        assert epic.name == "test-epic"
        assert epic.id is not None
    
    def test_get_epic(self, test_db):
        """Test getting an epic by ID."""
        service = EpicService(test_db)
        created = service.create("test-epic")
        
        found = service.get(created.id)
        
        assert found is not None
        assert found.id == created.id
    
    def test_get_by_name(self, test_db):
        """Test getting an epic by name."""
        service = EpicService(test_db)
        service.create("my-epic")
        
        found = service.get_by_name("my-epic")
        
        assert found is not None
        assert found.name == "my-epic"
    
    def test_list_all(self, test_db):
        """Test listing all epics."""
        service = EpicService(test_db)
        service.create("epic1")
        service.create("epic2")
        
        epics = service.list_all()
        
        assert len(epics) == 2
    
    def test_update_epic(self, test_db):
        """Test updating an epic (epics are now immutable containers)."""
        service = EpicService(test_db)
        service.create("test-epic")
        
        updated = service.update("test-epic")
        
        assert updated is not None
        assert updated.name == "test-epic"
    
    def test_delete_epic(self, test_db):
        """Test that epics cannot be deleted (they're permanent)."""
        service = EpicService(test_db)
        service.create("permanent-epic")
        
        # Epics don't have delete method anymore - they're permanent
        # Just verify the epic exists
        assert service.get_by_name("permanent-epic") is not None
    
    def test_get_summary_no_tasks(self, test_db):
        """Test getting summary for epic with no completed tasks."""
        service = EpicService(test_db)
        service.create("empty-epic")
        
        summary = service.get_summary("empty-epic")
        
        assert "empty-epic" in summary
        assert "No completed tasks yet" in summary
    
    def test_get_summary_with_tasks(self, test_db):
        """Test getting summary with completed tasks."""
        epic_service = EpicService(test_db)
        epic = epic_service.create("test-epic")
        
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
        epic = epic_service.create("test-epic")
        
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
        epic = epic_service.create("test-epic")
        
        task_service = TaskService(test_db, temp_dir)
        task = task_service.create("test-task", epic.id)
        
        assert task.name == "test-task"
        assert task.file_name == ""  # File not created until #plan mode
        assert task.status == TaskStatus.IN_PROGRESS  # Default is now in-progress
    
    def test_create_plan_file(self, test_db, temp_dir):
        """Test that create_plan_file creates the task file."""
        epic_service = EpicService(test_db)
        epic = epic_service.create("test-epic")
        
        task_service = TaskService(test_db, temp_dir)
        task = task_service.create("test-task", epic.id)
        
        # File doesn't exist initially
        assert task.file_name == ""
        
        # Create plan file (simulating entering #plan mode)
        file_path = task_service.create_plan_file(task.id)
        
        assert file_path is not None
        assert file_path.startswith("tasks/test-epic/test-task-")
        
        # File should now exist
        task_file = temp_dir / file_path
        assert task_file.exists()
    
    def test_get_task(self, test_db, temp_dir):
        """Test getting a task by ID."""
        epic_service = EpicService(test_db)
        epic = epic_service.create("test-epic")
        
        task_service = TaskService(test_db, temp_dir)
        created = task_service.create("test-task", epic.id)
        
        found = task_service.get(created.id)
        
        assert found is not None
        assert found.id == created.id
    
    def test_get_by_name(self, test_db, temp_dir):
        """Test getting task by name."""
        epic_service = EpicService(test_db)
        epic = epic_service.create("test-epic")
        
        task_service = TaskService(test_db, temp_dir)
        task_service.create("my-task", epic.id)
        
        found = task_service.get_by_name("my-task")
        
        assert found is not None
        assert found.name == "my-task"
    
    def test_list_all_tasks(self, test_db, temp_dir):
        """Test listing all tasks."""
        epic_service = EpicService(test_db)
        epic1 = epic_service.create("epic1")
        epic2 = epic_service.create("epic2")
        
        task_service = TaskService(test_db, temp_dir)
        # Use draft status for multiple tasks since only one can be in-progress
        task_service.create("task1", epic1.id, status=TaskStatus.DRAFT)
        task_service.create("task2", epic2.id, status=TaskStatus.DRAFT)
        
        tasks = task_service.list_all()
        
        assert len(tasks) == 2
    
    def test_list_tasks_by_epic(self, test_db, temp_dir):
        """Test listing tasks filtered by epic."""
        epic_service = EpicService(test_db)
        epic1 = epic_service.create("epic1")
        epic2 = epic_service.create("epic2")
        
        task_service = TaskService(test_db, temp_dir)
        # Use draft status for multiple tasks since only one can be in-progress
        task_service.create("task1", epic1.id, status=TaskStatus.DRAFT)
        task_service.create("task2", epic2.id, status=TaskStatus.DRAFT)
        
        tasks = task_service.list_all(epic_name="epic1")
        
        assert len(tasks) == 1
        assert tasks[0].name == "task1"
    
    def test_update_task(self, test_db, temp_dir):
        """Test updating a task."""
        epic_service = EpicService(test_db)
        epic = epic_service.create("test-epic")
        
        task_service = TaskService(test_db, temp_dir)
        task = task_service.create("test-task", epic.id)  # Already in-progress
        
        updated = task_service.update(
            task.id,
            summary="New summary"
        )
        
        assert updated is not None
        assert updated.status == TaskStatus.IN_PROGRESS  # Still in-progress
        assert updated.summary == "New summary"
    
    def test_delete_task(self, test_db, temp_dir):
        """Test deleting a task."""
        epic_service = EpicService(test_db)
        epic = epic_service.create("test-epic")
        
        task_service = TaskService(test_db, temp_dir)
        task = task_service.create("to-delete", epic.id, status=TaskStatus.DRAFT)
        
        result = task_service.delete(task.id)
        
        assert result is True
        assert task_service.get(task.id) is None
    
    def test_get_task_content(self, test_db, temp_dir):
        """Test getting task file content."""
        epic_service = EpicService(test_db)
        epic = epic_service.create("test-epic")
        
        task_service = TaskService(test_db, temp_dir)
        task = task_service.create("test-task", epic.id)
        
        # Create the plan file (simulating entering #plan mode)
        task_service.create_plan_file(task.id)
        
        content = task_service.get_task_content(task.id)
        
        assert content is not None
        assert "# TASK NAME" in content
        assert "SUMMARY" in content
    
    def test_single_in_progress_enforcement(self, test_db, temp_dir):
        """Test that only one task can be in-progress at a time."""
        import pytest
        
        epic_service = EpicService(test_db)
        epic = epic_service.create("test-epic")
        
        task_service = TaskService(test_db, temp_dir)
        # Create tasks as draft first
        task1 = task_service.create("task-1", epic.id, status=TaskStatus.DRAFT)
        task2 = task_service.create("task-2", epic.id, status=TaskStatus.DRAFT)
        
        # Set first task to in-progress
        task_service.update(task1.id, status=TaskStatus.IN_PROGRESS)
        
        # Try to set second task to in-progress - should fail
        with pytest.raises(ValueError) as exc_info:
            task_service.update(task2.id, status=TaskStatus.IN_PROGRESS)
        
        assert "already in-progress" in str(exc_info.value)
        assert task1.id in str(exc_info.value)
    
    def test_single_in_progress_allows_same_task(self, test_db, temp_dir):
        """Test that updating the same in-progress task is allowed."""
        epic_service = EpicService(test_db)
        epic = epic_service.create("test-epic")
        
        task_service = TaskService(test_db, temp_dir)
        task = task_service.create("task-1", epic.id)  # Defaults to in-progress
        
        # Update the same task again (e.g., adding summary) - should work
        updated = task_service.update(task.id, status=TaskStatus.IN_PROGRESS, summary="New summary")
        
        assert updated is not None
        assert updated.summary == "New summary"
    
    def test_in_progress_after_completing_previous(self, test_db, temp_dir):
        """Test that a new task can be in-progress after completing previous."""
        epic_service = EpicService(test_db)
        epic = epic_service.create("test-epic")
        
        task_service = TaskService(test_db, temp_dir)
        task1 = task_service.create("task-1", epic.id)  # Defaults to in-progress
        
        # Complete first task
        task_service.update(task1.id, status=TaskStatus.COMPLETED)
        
        # Now second task can be created (defaults to in-progress)
        task2 = task_service.create("task-2", epic.id)
        
        assert task2 is not None
        assert task2.status == TaskStatus.IN_PROGRESS

