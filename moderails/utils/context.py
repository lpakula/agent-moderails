"""Context builder for dynamic mode templates."""

from typing import Any, Optional

from ..db.models import Task, TaskStatus
from .git import get_current_branch, get_staged_files, get_unstaged_files


def get_in_progress_task(services: dict) -> Optional[dict]:
    """Get the current in-progress task as a dict for template rendering.
    
    Returns:
        Task dict with id, name, status, file_name, epic info, or None
    """
    tasks = services["task"].list_all(status=TaskStatus.IN_PROGRESS)
    if not tasks:
        return None
    
    task = tasks[0]
    return _task_to_dict(task)


def get_in_progress_or_draft_task(services: dict) -> Optional[dict]:
    """Get the current in-progress task, or first draft task if none in-progress.
    
    Returns:
        Task dict with id, name, status, file_name, epic info, or None
    """
    # First check for in-progress
    tasks = services["task"].list_all(status=TaskStatus.IN_PROGRESS)
    if tasks:
        return _task_to_dict(tasks[0])
    
    # Fall back to draft
    tasks = services["task"].list_all(status=TaskStatus.DRAFT)
    if tasks:
        return _task_to_dict(tasks[0])
    
    return None


def _task_to_dict(task: Task) -> dict:
    """Convert Task model to dict for template rendering."""
    return {
        "id": task.id,
        "name": task.name,
        "status": task.status.value,
        "file_name": task.file_name,
        "file_path": f".moderails/{task.file_name}",
        "type": task.type.value,
        "epic": {
            "id": task.epic.id,
            "name": task.epic.name,
        } if task.epic else None,
    }


def build_mode_context(
    services: dict,
    mode_name: str,
    flags: list[str] | None = None,
) -> dict[str, Any]:
    """Build context dict for mode template rendering.
    
    Each mode only loads what it needs for efficiency.
    
    Args:
        services: Dict containing task, context, epic services
        mode_name: Name of the mode being loaded
        flags: Optional list of mode flags (e.g., ["no-confirmation"])
        
    Returns:
        Context dict for Jinja template rendering
    """
    context: dict[str, Any] = {}
    
    # Always include flags for conditional template rendering
    context["flags"] = flags or []
    
    # Start mode - needs task info and epics for conditional workflow
    if mode_name == "start":
        context["current_task"] = get_in_progress_or_draft_task(services)
        # Load epics so agent doesn't need to run `moderails epic list`
        epics = services["epic"].list_all()
        context["epics"] = [{"id": e.id, "name": e.name} for e in epics]
    
    # Task-aware modes - need current in-progress task
    if mode_name in ("execute", "complete", "plan", "brainstorm", "abort"):
        context["current_task"] = get_in_progress_task(services)
    
    # Git state - only complete mode needs this
    if mode_name == "complete":
        branch = get_current_branch()
        context["git"] = {
            "branch": branch,
            "is_main": branch == "main" if branch else False,
            "staged_files": get_staged_files(),
            "unstaged_files": get_unstaged_files(),
        }
    
    # Full context discovery - research and fast modes
    if mode_name in ("research", "fast"):
        context["mandatory_context"] = services["context"].load_mandatory_context()
        context["memories"] = services["context"].list_memories()
        context["files_tree"] = services["context"].get_files_tree()
    
    return context
