"""Tests for database module."""

import pytest

from moderails.db.database import init_db, find_db_path
from moderails.db.models import Epic, Task, TaskStatus


class TestInitDb:
    """Tests for init_db function."""
    
    def test_init_db_creates_database(self, temp_dir, monkeypatch):
        """Test that init_db creates database file."""
        monkeypatch.chdir(temp_dir)
        
        db_path = init_db()
        
        assert db_path.exists()
        assert db_path.name == "moderails.db"
        assert db_path.parent.name == ".moderails"
    
    def test_init_db_creates_config(self, temp_dir, monkeypatch):
        """Test that init_db creates config.json."""
        monkeypatch.chdir(temp_dir)
        
        db_path = init_db()
        config_path = db_path.parent / "config.json"
        
        assert config_path.exists()
    
    def test_init_db_creates_gitignore(self, temp_dir, monkeypatch):
        """Test that init_db creates .gitignore."""
        monkeypatch.chdir(temp_dir)
        
        db_path = init_db()
        gitignore_path = db_path.parent / ".gitignore"
        
        assert gitignore_path.exists()
        content = gitignore_path.read_text()
        assert "*.db" in content
        assert "tasks/" in content


class TestFindDbPath:
    """Tests for find_db_path function."""
    
    def test_find_db_path_success(self, temp_dir, monkeypatch):
        """Test successfully finding database."""
        monkeypatch.chdir(temp_dir)
        
        # Initialize database
        db_path = init_db()
        
        # Find it
        found = find_db_path(temp_dir)
        assert found == db_path
    
    def test_find_db_path_not_found(self, temp_dir):
        """Test when database doesn't exist."""
        found = find_db_path(temp_dir)
        assert found is None


class TestEpicModel:
    """Tests for Epic model."""
    
    def test_create_epic(self, test_db):
        """Test creating an epic."""
        epic = Epic(name="test-epic")
        test_db.add(epic)
        test_db.commit()
        
        assert epic.id is not None
        assert epic.name == "test-epic"
    
    def test_epic_to_dict(self, test_db):
        """Test Epic to_dict method."""
        epic = Epic(name="test-epic")
        test_db.add(epic)
        test_db.commit()
        
        data = epic.to_dict()
        
        assert data["name"] == "test-epic"
        assert "id" in data
    
    def test_epic_unique_name(self, test_db):
        """Test that epic names must be unique."""
        epic1 = Epic(name="duplicate")
        test_db.add(epic1)
        test_db.commit()
        
        epic2 = Epic(name="duplicate")
        test_db.add(epic2)
        
        with pytest.raises(Exception):  # SQLAlchemy IntegrityError
            test_db.commit()


class TestTaskModel:
    """Tests for Task model."""
    
    def test_create_task(self, test_db):
        """Test creating a task."""
        epic = Epic(name="test-epic")
        test_db.add(epic)
        test_db.commit()
        
        task = Task(
            name="test-task",
            file_name="test-task.md",
            epic_id=epic.id,
            status=TaskStatus.DRAFT
        )
        test_db.add(task)
        test_db.commit()
        
        assert task.id is not None
        assert task.name == "test-task"
        assert task.status == TaskStatus.DRAFT
        assert task.epic == epic
    
    def test_task_to_dict(self, test_db):
        """Test Task to_dict method."""
        epic = Epic(name="test-epic")
        test_db.add(epic)
        test_db.commit()
        
        task = Task(
            name="test-task",
            file_name="test.md",
            epic_id=epic.id,
            summary="Test summary"
        )
        test_db.add(task)
        test_db.commit()
        
        data = task.to_dict()
        
        assert data["name"] == "test-task"
        assert data["epic"] == "test-epic"
        assert data["summary"] == "Test summary"
        assert data["status"] == "draft"
    
    def test_task_file_path_property(self, test_db):
        """Test Task file_path property."""
        epic = Epic(name="my-epic")
        test_db.add(epic)
        test_db.commit()
        
        task = Task(
            name="my-task",
            file_name="tasks/task.md",
            epic_id=epic.id
        )
        test_db.add(task)
        test_db.commit()
        
        assert task.file_path == ".moderails/tasks/task.md"
    
    def test_task_status_enum(self, test_db):
        """Test TaskStatus enum values."""
        epic = Epic(name="test")
        test_db.add(epic)
        test_db.commit()
        
        task = Task(name="task", file_name="t.md", epic_id=epic.id)
        test_db.add(task)
        test_db.commit()
        
        assert task.status == TaskStatus.DRAFT
        
        task.status = TaskStatus.IN_PROGRESS
        test_db.commit()
        assert task.status == TaskStatus.IN_PROGRESS
        
        task.status = TaskStatus.COMPLETED
        test_db.commit()
        assert task.status == TaskStatus.COMPLETED
    
    def test_task_git_hash(self, test_db):
        """Test storing git hash in task."""
        epic = Epic(name="test")
        test_db.add(epic)
        test_db.commit()
        
        task = Task(
            name="task",
            file_name="t.md",
            epic_id=epic.id,
            git_hash="abc123def456"
        )
        test_db.add(task)
        test_db.commit()
        
        assert task.git_hash == "abc123def456"

