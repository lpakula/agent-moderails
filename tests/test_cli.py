"""Tests for CLI commands."""

import pytest
from click.testing import CliRunner
from pathlib import Path

from moderails.cli import cli
from moderails.db.models import Epic, Task, TaskStatus


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
            assert "#onboard" in result.output  # Suggests onboarding
            
            # Check files were created
            assert (Path.cwd() / "agent" / "moderails" / "moderails.db").exists()
            assert (Path.cwd() / "agent" / "moderails" / "config.json").exists()
    
    def test_init_with_custom_base_dir(self, cli_runner):
        """Test initialization with custom base directory."""
        with cli_runner.isolated_filesystem():
            result = cli_runner.invoke(cli, ['init', '--base-dir', 'tools'])
            
            assert result.exit_code == 0
            assert (Path.cwd() / "tools" / "moderails" / "moderails.db").exists()
    
    def test_init_with_invalid_base_dir(self, cli_runner):
        """Test initialization with invalid base directory."""
        with cli_runner.isolated_filesystem():
            result = cli_runner.invoke(cli, ['init', '--base-dir', '.ai'])
            
            assert result.exit_code == 0
            assert "Invalid base directory" in result.output


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
    
    def test_start_new_task(self, cli_runner):
        """Test creating a new task."""
        with cli_runner.isolated_filesystem():
            # Initialize first
            cli_runner.invoke(cli, ['init'])
            
            result = cli_runner.invoke(cli, [
                'start',
                '--new',
                '--task', 'test-task',
                '--epic', 'test-epic'
            ])
            
            assert result.exit_code == 0
            assert "Created task" in result.output
    
    def test_start_existing_task(self, cli_runner):
        """Test continuing an existing task."""
        with cli_runner.isolated_filesystem():
            # Initialize first
            cli_runner.invoke(cli, ['init'])
            
            # Create a task
            cli_runner.invoke(cli, [
                'start',
                '--new',
                '--task', 'my-task',
                '--epic', 'my-epic'
            ])
            
            # Then continue it
            result = cli_runner.invoke(cli, ['start', '--task', 'my-task'])
            
            assert result.exit_code == 0
            assert "my-task" in result.output


class TestStatusCommand:
    """Tests for status command."""
    
    def test_status_empty(self, cli_runner):
        """Test status with no epics."""
        with cli_runner.isolated_filesystem():
            # Initialize first
            cli_runner.invoke(cli, ['init'])
            
            result = cli_runner.invoke(cli, ['status'])
            
            assert result.exit_code == 0
            assert "No tasks" in result.output or "0 tasks" in result.output or "No epics found" in result.output
    
    def test_status_with_tasks(self, cli_runner):
        """Test status with existing tasks."""
        with cli_runner.isolated_filesystem():
            # Initialize first
            cli_runner.invoke(cli, ['init'])
            
            # Create a task
            cli_runner.invoke(cli, [
                'start',
                '--new',
                '--task', 'test-task',
                '--epic', 'test-epic'
            ])
            
            result = cli_runner.invoke(cli, ['status'])
            
            assert result.exit_code == 0
            assert "test-task" in result.output


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
    
    def test_mode_onboard(self, cli_runner):
        """Test getting onboard mode definition."""
        with cli_runner.isolated_filesystem():
            cli_runner.invoke(cli, ['init'])
            
            result = cli_runner.invoke(cli, ['mode', '--name', 'onboard'])
            
            assert result.exit_code == 0
            assert "ONBOARD MODE" in result.output
            assert "One-time codebase analysis" in result.output
    
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
            
            # Create task first
            cli_runner.invoke(cli, [
                'start',
                '--new',
                '--task', 'test-task',
                '--epic', 'test-epic'
            ])
            
            result = cli_runner.invoke(cli, [
                'task', 'update',
                '--task', 'test-task',
                '--status', 'in-progress'
            ])
            
            assert result.exit_code == 0
            assert "Updated task" in result.output
    
    def test_task_update_summary(self, cli_runner):
        """Test updating task summary."""
        with cli_runner.isolated_filesystem():
            cli_runner.invoke(cli, ['init'])
            
            cli_runner.invoke(cli, [
                'start',
                '--new',
                '--task', 'test-task',
                '--epic', 'test-epic'
            ])
            
            result = cli_runner.invoke(cli, [
                'task', 'update',
                '--task', 'test-task',
                '--summary', 'New summary'
            ])
            
            assert result.exit_code == 0
            assert "Updated task" in result.output
    
    def test_task_delete(self, cli_runner):
        """Test deleting a task."""
        with cli_runner.isolated_filesystem():
            cli_runner.invoke(cli, ['init'])
            
            cli_runner.invoke(cli, [
                'start',
                '--new',
                '--task', 'to-delete',
                '--epic', 'test-epic'
            ])
            
            result = cli_runner.invoke(cli, [
                'task', 'delete',
                '--task', 'to-delete',
                '--confirm'
            ])
            
            assert result.exit_code == 0
            assert "Deleted task" in result.output
    
    def test_task_delete_without_confirm(self, cli_runner):
        """Test that delete requires confirmation."""
        with cli_runner.isolated_filesystem():
            cli_runner.invoke(cli, ['init'])
            
            cli_runner.invoke(cli, [
                'start',
                '--new',
                '--task', 'test-task',
                '--epic', 'test-epic'
            ])
            
            result = cli_runner.invoke(cli, [
                'task', 'delete',
                '--task', 'test-task'
            ])
            
            assert result.exit_code == 0
            assert "Use --confirm" in result.output


class TestEpicCommands:
    """Tests for epic subcommands."""
    
    def test_epic_summary(self, cli_runner):
        """Test getting epic summary."""
        with cli_runner.isolated_filesystem():
            cli_runner.invoke(cli, ['init'])
            
            # Create epic with task
            cli_runner.invoke(cli, [
                'start',
                '--new',
                '--task', 'test-task',
                '--epic', 'test-epic'
            ])
            
            result = cli_runner.invoke(cli, [
                'epic', 'summary',
                '--name', 'test-epic'
            ])
            
            assert result.exit_code == 0
            assert "test-epic" in result.output
    
    def test_epic_summary_short(self, cli_runner):
        """Test getting epic summary with short flag."""
        with cli_runner.isolated_filesystem():
            cli_runner.invoke(cli, ['init'])
            
            cli_runner.invoke(cli, [
                'start',
                '--new',
                '--task', 'test-task',
                '--epic', 'test-epic'
            ])
            
            result = cli_runner.invoke(cli, [
                'epic', 'summary',
                '--name', 'test-epic',
                '--short'
            ])
            
            assert result.exit_code == 0
            assert "test-epic" in result.output
    
    def test_epic_update(self, cli_runner):
        """Test updating epic tags."""
        with cli_runner.isolated_filesystem():
            cli_runner.invoke(cli, ['init'])
            
            cli_runner.invoke(cli, [
                'start',
                '--new',
                '--task', 'test-task',
                '--epic', 'test-epic'
            ])
            
            result = cli_runner.invoke(cli, [
                'epic', 'update',
                '--name', 'test-epic',
                '--tags', 'backend,api'
            ])
            
            assert result.exit_code == 0
            assert "Updated epic" in result.output
    
    def test_epic_delete(self, cli_runner):
        """Test deleting an epic."""
        with cli_runner.isolated_filesystem():
            cli_runner.invoke(cli, ['init'])
            
            cli_runner.invoke(cli, [
                'start',
                '--new',
                '--task', 'test-task',
                '--epic', 'to-delete'
            ])
            
            result = cli_runner.invoke(cli, [
                'epic', 'delete',
                '--name', 'to-delete',
                '--confirm'
            ])
            
            assert result.exit_code == 0
            assert "Deleted epic" in result.output
    
    def test_epic_delete_without_confirm(self, cli_runner):
        """Test that epic delete requires confirmation."""
        with cli_runner.isolated_filesystem():
            cli_runner.invoke(cli, ['init'])
            
            cli_runner.invoke(cli, [
                'start',
                '--new',
                '--task', 'test-task',
                '--epic', 'test-epic'
            ])
            
            result = cli_runner.invoke(cli, [
                'epic', 'delete',
                '--name', 'test-epic'
            ])
            
            assert result.exit_code == 0
            assert "Use --confirm" in result.output

