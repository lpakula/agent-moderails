"""Tests for dynamic mode templates."""

import pytest
from unittest.mock import Mock, patch

from moderails.modes import get_mode
from moderails.utils.context import build_mode_context, get_in_progress_task, get_in_progress_or_draft_task


class TestAllModesRender:
    """Test that all mode templates render without Jinja errors."""
    
    @pytest.fixture
    def task_context(self):
        """Standard task context for testing."""
        return {
            "id": "abc123",
            "name": "Test Task",
            "status": "in-progress",
            "file_name": "tasks/test-epic/test-task-abc123.plan.md",
            "file_path": ".moderails/tasks/test-epic/test-task-abc123.plan.md",
            "type": "feature",
            "epic": {"id": "xyz789", "name": "Test Epic"},
        }
    
    def test_start_mode_renders_with_task(self, task_context):
        """Test start mode renders with current task."""
        context = {
            "current_task": task_context,
            "epics": [{"id": "xyz789", "name": "Test Epic"}],
            "flags": [],
        }
        result = get_mode("start", context)
        
        assert "# Moderails Protocol" in result
        assert "abc123" in result
        assert "Test Task" in result
    
    def test_start_mode_renders_without_task(self):
        """Test start mode renders without task (new user flow)."""
        context = {
            "current_task": None,
            "epics": [],
            "flags": [],
        }
        result = get_mode("start", context)
        
        assert "# Moderails Protocol" in result
        assert "No Active Task" in result
        assert "No epics exist yet" in result
    
    def test_start_mode_renders_with_epics(self):
        """Test start mode renders with existing epics."""
        context = {
            "current_task": None,
            "epics": [
                {"id": "abc123", "name": "authentication"},
                {"id": "def456", "name": "payments"},
            ],
            "flags": [],
        }
        result = get_mode("start", context)
        
        assert "abc123" in result
        assert "authentication" in result
        assert "def456" in result
        assert "payments" in result
    
    def test_research_mode_renders(self, task_context):
        """Test research mode renders with full context."""
        context = {
            "mandatory_context": "## MANDATORY CONTEXT\n\nTest mandatory content",
            "memories": ["auth", "payments", "api"],
            "files_tree": "src/\n  main.ts\n  utils.ts",
            "flags": [],
        }
        result = get_mode("research", context)
        
        assert "# RESEARCH MODE" in result
        assert "MANDATORY CONTEXT" in result
        assert "auth" in result
    
    def test_research_mode_renders_empty_context(self):
        """Test research mode renders with no context."""
        context = {
            "mandatory_context": None,
            "memories": [],
            "files_tree": None,
            "flags": [],
        }
        result = get_mode("research", context)
        
        assert "# RESEARCH MODE" in result
    
    def test_brainstorm_mode_renders(self, task_context):
        """Test brainstorm mode renders."""
        context = {
            "current_task": task_context,
            "flags": [],
        }
        result = get_mode("brainstorm", context)
        
        assert "# BRAINSTORM MODE" in result
        assert "abc123" in result
    
    def test_plan_mode_renders(self, task_context):
        """Test plan mode renders."""
        context = {
            "current_task": task_context,
            "flags": [],
        }
        result = get_mode("plan", context)
        
        assert "# PLAN MODE" in result
        assert "abc123" in result
        assert task_context["file_path"] in result
    
    def test_plan_mode_renders_without_task(self):
        """Test plan mode renders without task."""
        context = {
            "current_task": None,
            "flags": [],
        }
        result = get_mode("plan", context)
        
        assert "# PLAN MODE" in result
    
    def test_execute_mode_renders(self, task_context):
        """Test execute mode renders."""
        context = {
            "current_task": task_context,
            "flags": [],
        }
        result = get_mode("execute", context)
        
        assert "# EXECUTE MODE" in result
        assert "abc123" in result
    
    def test_execute_mode_renders_draft_task(self, task_context):
        """Test execute mode renders with draft task (shows status update command)."""
        task_context["status"] = "draft"
        context = {
            "current_task": task_context,
            "flags": [],
        }
        result = get_mode("execute", context)
        
        assert "# EXECUTE MODE" in result
        assert "in-progress" in result  # Should suggest updating to in-progress
    
    def test_complete_mode_renders(self, task_context):
        """Test complete mode renders with git state."""
        context = {
            "current_task": task_context,
            "git": {
                "branch": "feature/test",
                "is_main": False,
                "staged_files": ["src/main.ts", "src/utils.ts"],
                "unstaged_files": ["README.md"],
            },
            "flags": [],
        }
        result = get_mode("complete", context)
        
        assert "# COMPLETE MODE" in result
        assert "feature/test" in result
        assert "src/main.ts" in result
        assert "README.md" in result
    
    def test_complete_mode_renders_main_branch_warning(self, task_context):
        """Test complete mode shows warning on main branch."""
        context = {
            "current_task": task_context,
            "git": {
                "branch": "main",
                "is_main": True,
                "staged_files": [],
                "unstaged_files": [],
            },
            "flags": [],
        }
        result = get_mode("complete", context)
        
        assert "# COMPLETE MODE" in result
        assert "WARNING" in result or "main" in result
    
    def test_complete_mode_renders_no_changes(self, task_context):
        """Test complete mode renders with no git changes."""
        context = {
            "current_task": task_context,
            "git": {
                "branch": "feature/test",
                "is_main": False,
                "staged_files": [],
                "unstaged_files": [],
            },
            "flags": [],
        }
        result = get_mode("complete", context)
        
        assert "# COMPLETE MODE" in result
        assert "No changes detected" in result
    
    def test_fast_mode_renders(self):
        """Test fast mode renders with full context."""
        context = {
            "mandatory_context": "## MANDATORY CONTEXT\n\nTest content",
            "memories": ["auth"],
            "files_tree": "src/\n  file.ts",
            "flags": [],
        }
        result = get_mode("fast", context)
        
        assert "# FAST MODE" in result
    
    def test_abort_mode_renders(self, task_context):
        """Test abort mode renders."""
        context = {
            "current_task": task_context,
            "flags": [],
        }
        result = get_mode("abort", context)
        
        assert "# ABORT MODE" in result
        assert "abc123" in result


class TestGetMode:
    """Tests for get_mode() function."""
    
    def test_get_mode_without_context(self):
        """Test loading a mode without context renders static parts."""
        result = get_mode("start")
        
        assert "# Moderails Protocol" in result
        assert "Modal control system for AI agents" in result
    
    def test_get_mode_with_task_context(self):
        """Test mode renders with task context."""
        context = {
            "current_task": {
                "id": "abc123",
                "name": "Test Task",
                "status": "draft",
                "file_name": "tasks/test-task-abc123.plan.md",
                "file_path": ".moderails/tasks/test-task-abc123.plan.md",
                "type": "feature",
                "epic": None,
            }
        }
        
        result = get_mode("start", context)
        
        assert "abc123" in result
        assert "Test Task" in result
        assert "#research" in result  # Should suggest research for draft
    
    def test_get_mode_in_progress_task(self):
        """Test mode renders correctly for in-progress task."""
        context = {
            "current_task": {
                "id": "xyz789",
                "name": "In Progress Task",
                "status": "in-progress",
                "file_name": "tasks/in-progress-task-xyz789.plan.md",
                "file_path": ".moderails/tasks/in-progress-task-xyz789.plan.md",
                "type": "feature",
                "epic": None,
            }
        }
        
        result = get_mode("start", context)
        
        assert "xyz789" in result
        assert "#execute" in result  # Should suggest execute for in-progress
    
    def test_get_mode_no_task(self):
        """Test mode renders 'no task' workflow when current_task is None."""
        context = {"current_task": None}
        
        result = get_mode("start", context)
        
        assert "No Active Task" in result
        assert "What would you like to build" in result
    
    def test_get_mode_invalid_mode(self):
        """Test getting an invalid mode returns error message."""
        result = get_mode("nonexistent")
        
        assert "Mode file not found" in result
    
    def test_get_mode_backward_compatible(self):
        """Test that modes without Jinja syntax work without context."""
        # All modes should work without context (graceful degradation)
        for mode_name in ["start", "research", "fast", "execute", "complete", "plan", "brainstorm", "abort"]:
            result = get_mode(mode_name)
            assert result is not None
            assert len(result) > 0


class TestResearchMode:
    """Tests for research mode with auto-injected context."""
    
    def test_research_mode_with_mandatory_context(self):
        """Test research mode includes mandatory context."""
        context = {
            "mandatory_context": "## MANDATORY\n\nThis is mandatory context.",
            "memories": ["auth", "payments", "users"],
            "files_tree": "src/\n  auth.ts\n  payments.ts",
        }
        
        result = get_mode("research", context)
        
        assert "MANDATORY" in result
        assert "This is mandatory context" in result
        assert "auth" in result
        assert "payments" in result
        assert "users" in result
        assert "auth.ts" in result
    
    def test_research_mode_no_memories(self):
        """Test research mode handles empty memories."""
        context = {
            "mandatory_context": None,
            "memories": [],
            "files_tree": None,
        }
        
        result = get_mode("research", context)
        
        assert "No memories available" in result
        assert "No files in history" in result


class TestCompleteMode:
    """Tests for complete mode with git state."""
    
    def test_complete_mode_with_git_state(self):
        """Test complete mode shows git status."""
        context = {
            "current_task": {
                "id": "abc123",
                "name": "Test",
                "status": "in-progress",
                "file_name": "tasks/test-abc123.plan.md",
                "file_path": ".moderails/tasks/test-abc123.plan.md",
                "type": "feature",
                "epic": None,
            },
            "git": {
                "branch": "feature/test",
                "is_main": False,
                "staged_files": ["src/foo.ts", "src/bar.ts"],
                "unstaged_files": ["src/baz.ts"],
            }
        }
        
        result = get_mode("complete", context)
        
        assert "feature/test" in result
        assert "src/foo.ts" in result
        assert "src/bar.ts" in result
        assert "src/baz.ts" in result
        assert "abc123" in result
    
    def test_complete_mode_main_branch_warning(self):
        """Test complete mode shows warning on main branch."""
        context = {
            "current_task": None,
            "git": {
                "branch": "main",
                "is_main": True,
                "staged_files": [],
                "unstaged_files": [],
            }
        }
        
        result = get_mode("complete", context)
        
        assert "WARNING" in result
        assert "main" in result


class TestBuildModeContext:
    """Tests for build_mode_context() function."""
    
    def test_build_context_start_mode(self):
        """Test start mode gets current task context."""
        mock_task = Mock()
        mock_task.id = "abc123"
        mock_task.name = "Test Task"
        mock_task.status = Mock(value="draft")
        mock_task.file_name = "tasks/test.plan.md"
        mock_task.type = Mock(value="feature")
        mock_task.epic = None
        
        mock_task_service = Mock()
        mock_task_service.list_all.return_value = [mock_task]
        
        mock_epic_service = Mock()
        mock_epic_service.list_all.return_value = []
        
        services = {
            "task": mock_task_service,
            "context": Mock(),
            "epic": mock_epic_service,
        }
        
        context = build_mode_context(services, "start")
        
        assert context.get("current_task") is not None
        assert context["current_task"]["id"] == "abc123"
        assert context.get("epics") == []
        assert context.get("flags") == []
    
    def test_build_context_research_mode(self):
        """Test research mode gets mandatory context and memories."""
        mock_context_service = Mock()
        mock_context_service.load_mandatory_context.return_value = "Mandatory content"
        mock_context_service.list_memories.return_value = ["auth", "payments"]
        mock_context_service.get_files_tree.return_value = "src/\n  file.ts"
        
        services = {
            "task": Mock(),
            "context": mock_context_service,
            "epic": Mock(),
        }
        
        context = build_mode_context(services, "research")
        
        assert context["mandatory_context"] == "Mandatory content"
        assert context["memories"] == ["auth", "payments"]
        assert "src/" in context["files_tree"]
    
    @patch('moderails.utils.context.get_current_branch')
    @patch('moderails.utils.context.get_staged_files')
    @patch('moderails.utils.context.get_unstaged_files')
    def test_build_context_complete_mode(self, mock_unstaged, mock_staged, mock_branch):
        """Test complete mode gets git state."""
        mock_branch.return_value = "main"
        mock_staged.return_value = ["file1.ts"]
        mock_unstaged.return_value = ["file2.ts"]
        
        mock_task = Mock()
        mock_task.id = "abc123"
        mock_task.name = "Test"
        mock_task.status = Mock(value="in-progress")
        mock_task.file_name = "tasks/test.plan.md"
        mock_task.type = Mock(value="feature")
        mock_task.epic = None
        
        mock_task_service = Mock()
        mock_task_service.list_all.return_value = [mock_task]
        
        services = {
            "task": mock_task_service,
            "context": Mock(),
            "epic": Mock(),
        }
        
        context = build_mode_context(services, "complete")
        
        assert context["git"]["branch"] == "main"
        assert context["git"]["is_main"] is True
        assert context["git"]["staged_files"] == ["file1.ts"]
        assert context["git"]["unstaged_files"] == ["file2.ts"]


class TestModeFlags:
    """Tests for mode flag-based conditional rendering."""
    
    def test_build_context_with_flags(self):
        """Test flags are passed through to context."""
        mock_task_service = Mock()
        mock_task_service.list_all.return_value = []
        
        services = {
            "task": mock_task_service,
            "context": Mock(),
            "epic": Mock(),
        }
        
        context = build_mode_context(services, "execute", flags=["no-confirmation"])
        
        assert context["flags"] == ["no-confirmation"]
    
    def test_build_context_multiple_flags(self):
        """Test multiple flags are passed through."""
        mock_task_service = Mock()
        mock_task_service.list_all.return_value = []
        
        services = {
            "task": mock_task_service,
            "context": Mock(),
            "epic": Mock(),
        }
        
        context = build_mode_context(services, "execute", flags=["no-confirmation", "verbose"])
        
        assert context["flags"] == ["no-confirmation", "verbose"]
        assert "no-confirmation" in context["flags"]
    
    def test_execute_mode_no_confirmation_flag_renders_batch(self):
        """Test execute mode with no-confirmation flag renders batch mode instructions."""
        context = {
            "current_task": {
                "id": "abc123",
                "name": "Test Task",
                "status": "in-progress",
                "file_path": ".moderails/tasks/test.plan.md",
                "type": "feature",
                "epic": None,
            },
            "flags": ["no-confirmation"],
        }
        
        rendered = get_mode("execute", context)
        
        # Should have batch mode header
        assert "BATCH MODE" in rendered
        assert "--no-confirmation" in rendered
        # Should NOT have one-at-a-time instructions
        assert "ONE TODO ITEM PER RESPONSE" not in rendered
        assert "STOP and WAIT" not in rendered
    
    def test_execute_mode_without_flag_renders_normal(self):
        """Test execute mode without flag renders normal one-at-a-time instructions."""
        context = {
            "current_task": {
                "id": "abc123",
                "name": "Test Task",
                "status": "in-progress",
                "file_path": ".moderails/tasks/test.plan.md",
                "type": "feature",
                "epic": None,
            },
            "flags": [],
        }
        
        rendered = get_mode("execute", context)
        
        # Should have normal one-at-a-time instructions
        assert "ONE TODO ITEM PER RESPONSE" in rendered
        assert "STOP and WAIT" in rendered or "STOP and wait" in rendered.lower()
        # Should NOT have batch mode header
        assert "BATCH MODE" not in rendered
