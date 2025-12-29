"""Tests for CLI commands."""

import pytest
from click.testing import CliRunner
from pathlib import Path

from moderails.cli import cli
from moderails.db.migrations import set_schema_version, CURRENT_VERSION


@pytest.fixture
def cli_runner():
    """Create a Click CLI runner."""
    return CliRunner()


class TestInitCommand:
    """Tests for init command."""
    
    def test_init_success(self, cli_runner):
        """Test successful initialization."""
        with cli_runner.isolated_filesystem():
            result = cli_runner.invoke(cli, ['init'])
            
            assert result.exit_code == 0
            assert "ModeRails initialized successfully" in result.output
            assert "agent will guide you" in result.output
            
            # Check files were created
            assert (Path.cwd() / ".moderails" / "moderails.db").exists()
            assert (Path.cwd() / ".moderails" / "config.json").exists()


class TestStartCommand:
    """Tests for start command."""
    
    def test_start_shows_status(self, cli_runner):
        """Test start command shows status."""
        with cli_runner.isolated_filesystem():
            # Initialize first
            cli_runner.invoke(cli, ['init'])
            
            result = cli_runner.invoke(cli, ['start'])
            
            assert result.exit_code == 0
            assert "CURRENT STATUS" in result.output or "No epics yet" in result.output
    
    def test_start_with_task(self, cli_runner):
        """Test start command with an existing task."""
        with cli_runner.isolated_filesystem():
            # Initialize first
            cli_runner.invoke(cli, ['init'])
            
            # Create an epic and task using direct commands
            result = cli_runner.invoke(cli, ['epic', 'create', '--name', 'test-epic'])
            assert result.exit_code == 0
            
            # Extract epic ID from output (format: "✅ Created epic: <id> - test-epic")
            epic_id = result.output.split("Created epic: ")[1].split(" -")[0].strip()
            
            # Create a task
            result = cli_runner.invoke(cli, [
                'task', 'create',
                '--name', 'test-task',
                '--epic', epic_id
            ])
            assert result.exit_code == 0
            
            # Run start command
            result = cli_runner.invoke(cli, ['start'])
            
            assert result.exit_code == 0
            assert "CURRENT STATUS" in result.output


class TestStatusCommand:
    """Tests for status command."""
    
class TestModeCommand:
    """Tests for mode command."""
    
    def test_mode_research(self, cli_runner):
        """Test getting research mode definition."""
        with cli_runner.isolated_filesystem():
            cli_runner.invoke(cli, ['init'])
            
            result = cli_runner.invoke(cli, ['mode', '--name', 'research'])
            
            assert result.exit_code == 0
            assert "RESEARCH MODE" in result.output
    
    def test_mode_execute(self, cli_runner):
        """Test getting execute mode definition."""
        with cli_runner.isolated_filesystem():
            cli_runner.invoke(cli, ['init'])
            
            result = cli_runner.invoke(cli, ['mode', '--name', 'execute'])
            
            assert result.exit_code == 0
            assert "EXECUTE MODE" in result.output
    
    def test_mode_invalid(self, cli_runner):
        """Test invalid mode name."""
        with cli_runner.isolated_filesystem():
            cli_runner.invoke(cli, ['init'])
            
            result = cli_runner.invoke(cli, ['mode', '--name', 'invalid'])
            
            assert result.exit_code == 0
            assert "Invalid mode" in result.output


class TestTaskCommands:
    """Tests for task subcommands."""
    
    def test_task_update_status(self, cli_runner):
        """Test updating task status."""
        with cli_runner.isolated_filesystem():
            cli_runner.invoke(cli, ['init'])
            
            # Create epic and task
            epic_result = cli_runner.invoke(cli, ['epic', 'create', '--name', 'test-epic'])
            epic_id = epic_result.output.split("Created epic: ")[1].split(" -")[0].strip()
            
            task_result = cli_runner.invoke(cli, ['task', 'create', '--name', 'test-task', '--epic', epic_id])
            task_id = task_result.output.split("Task created: ")[1].split(" -")[0].strip()
            
            result = cli_runner.invoke(cli, [
                'task', 'update',
                '--task', task_id,
                '--status', 'in-progress'
            ])
            
            assert result.exit_code == 0
            assert "Updated task" in result.output
    
    def test_task_update_summary(self, cli_runner):
        """Test updating task summary."""
        with cli_runner.isolated_filesystem():
            cli_runner.invoke(cli, ['init'])
            
            # Create epic and task
            epic_result = cli_runner.invoke(cli, ['epic', 'create', '--name', 'test-epic'])
            epic_id = epic_result.output.split("Created epic: ")[1].split(" -")[0].strip()
            
            task_result = cli_runner.invoke(cli, ['task', 'create', '--name', 'test-task', '--epic', epic_id])
            task_id = task_result.output.split("Task created: ")[1].split(" -")[0].strip()
            
            result = cli_runner.invoke(cli, [
                'task', 'update',
                '--task', task_id,
                '--summary', 'New summary'
            ])
            
            assert result.exit_code == 0
            assert "Updated task" in result.output
    
    def test_task_delete(self, cli_runner):
        """Test deleting a task."""
        with cli_runner.isolated_filesystem():
            cli_runner.invoke(cli, ['init'])
            
            # Create epic and task
            epic_result = cli_runner.invoke(cli, ['epic', 'create', '--name', 'test-epic'])
            epic_id = epic_result.output.split("Created epic: ")[1].split(" -")[0].strip()
            
            task_result = cli_runner.invoke(cli, ['task', 'create', '--name', 'to-delete', '--epic', epic_id])
            task_id = task_result.output.split("Task created: ")[1].split(" -")[0].strip()
            
            result = cli_runner.invoke(cli, [
                'task', 'delete',
                '--task', task_id,
                '--confirm'
            ])
            
            assert result.exit_code == 0
            assert "Deleted task" in result.output
    
    def test_task_delete_without_confirm(self, cli_runner):
        """Test that delete requires confirmation."""
        with cli_runner.isolated_filesystem():
            cli_runner.invoke(cli, ['init'])
            
            # Create epic and task
            epic_result = cli_runner.invoke(cli, ['epic', 'create', '--name', 'test-epic'])
            epic_id = epic_result.output.split("Created epic: ")[1].split(" -")[0].strip()
            
            task_result = cli_runner.invoke(cli, ['task', 'create', '--name', 'test-task', '--epic', epic_id])
            task_id = task_result.output.split("Task created: ")[1].split(" -")[0].strip()
            
            result = cli_runner.invoke(cli, [
                'task', 'delete',
                '--task', task_id
            ])
            
            assert result.exit_code == 0
            assert "Use --confirm" in result.output


class TestEpicCommands:
    """Tests for epic subcommands."""
    
    def test_epic_list(self, cli_runner):
        """Test listing epics."""
        with cli_runner.isolated_filesystem():
            cli_runner.invoke(cli, ['init'])
            
            # Create epic with task
            epic_result = cli_runner.invoke(cli, ['epic', 'create', '--name', 'test-epic'])
            epic_id = epic_result.output.split("Created epic: ")[1].split(" -")[0].strip()
            
            result = cli_runner.invoke(cli, ['epic', 'list'])
            
            assert result.exit_code == 0
            assert "test-epic" in result.output
            assert epic_id in result.output
    
    def test_epic_create(self, cli_runner):
        """Test creating an epic manually."""
        with cli_runner.isolated_filesystem():
            cli_runner.invoke(cli, ['init'])
            
            result = cli_runner.invoke(cli, [
                'epic', 'create',
                '--name', 'new-epic'
            ])
            
            assert result.exit_code == 0
            assert "Created epic" in result.output


class TestMigrateCommand:
    """Tests for migrate command."""
    
    def test_migrate_no_database(self, cli_runner):
        """Test migrate command when no database exists."""
        with cli_runner.isolated_filesystem():
            result = cli_runner.invoke(cli, ['migrate'])
            
            assert result.exit_code == 1
            assert "No database found" in result.output
            assert "moderails init" in result.output
    
    def test_migrate_up_to_date(self, cli_runner):
        """Test migrate command when database is already up to date."""
        with cli_runner.isolated_filesystem():
            # Initialize database
            cli_runner.invoke(cli, ['init'])
            
            result = cli_runner.invoke(cli, ['migrate'])
            
            assert result.exit_code == 0
            assert f"Current schema version: {CURRENT_VERSION}" in result.output
            assert f"Latest schema version: {CURRENT_VERSION}" in result.output
            assert "Database is up to date" in result.output
    
    def test_migrate_needs_migration(self, cli_runner):
        """Test migrate command when migration is needed."""
        with cli_runner.isolated_filesystem():
            # Initialize database
            cli_runner.invoke(cli, ['init'])
            
            # Downgrade schema version to simulate old database
            db_path = Path.cwd() / ".moderails" / "moderails.db"
            old_version = CURRENT_VERSION - 1 if CURRENT_VERSION > 1 else 0
            set_schema_version(db_path, old_version)
            
            result = cli_runner.invoke(cli, ['migrate'])
            
            assert result.exit_code == 0
            assert f"Current schema version: {old_version}" in result.output
            assert f"Latest schema version: {CURRENT_VERSION}" in result.output
            assert "Applying migrations" in result.output
            assert "Database migrated successfully" in result.output

