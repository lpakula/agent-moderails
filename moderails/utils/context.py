"""Context builder for dynamic mode templates."""

from typing import Any, Optional

from ..db.models import Task, TaskStatus
from .git import get_current_branch, get_staged_files, get_unstaged_files


def get_in_progress_task(services: dict) -> Optional[dict]:
    """Get the current in-progress task as a dict for template rendering.
    
    Returns:
        Task dict with id, name, status, file_name, has_plan_file, epic info, or None
    """
    tasks = services["task"].list_all(status=TaskStatus.IN_PROGRESS)
    if not tasks:
        return None
    
    task = tasks[0]
    return _task_to_dict(task)


def get_draft_tasks(services: dict) -> list[dict]:
    """Get all draft tasks as a list of dicts for template rendering."""
    tasks = services["task"].list_all(status=TaskStatus.DRAFT)
    return [_task_to_dict(t) for t in tasks]


def _task_to_dict(task: Task) -> dict:
    """Convert Task model to dict for template rendering."""
    has_plan_file = bool(task.file_name)
    return {
        "id": task.id,
        "name": task.name,
        "status": task.status.value,
        "file_name": task.file_name,
        "file_path": f".moderails/{task.file_name}" if task.file_name else None,
        "has_plan_file": has_plan_file,
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
    
    # Start mode - needs in-progress task, draft tasks, and epics
    if mode_name == "start":
        context["current_task"] = get_in_progress_task(services)
        context["draft_tasks"] = get_draft_tasks(services)
        epics = services["epic"].list_all()
        context["epics"] = [{"id": e.id, "name": e.name} for e in epics]
    
    # Task-aware modes - need current in-progress task only
    if mode_name in ("execute", "complete", "plan", "brainstorm", "abort"):
        context["current_task"] = get_in_progress_task(services)
    
    # Plan mode: auto-create plan file if it doesn't exist
    if mode_name == "plan" and context.get("current_task"):
        task_dict = context["current_task"]
        if not task_dict.get("has_plan_file"):
            # Create plan file and re-fetch task to get updated file info
            services["task"].create_plan_file(task_dict["id"])
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
    
    # Research mode also needs current in-progress task and epic context
    if mode_name == "research":
        task = get_in_progress_task(services)
        context["current_task"] = task
        # Only load epic context for in-progress tasks
        if task and task.get("epic"):
            epic_summary = services["epic"].get_summary(task["epic"]["name"])
            context["epic_context"] = epic_summary
    
    return context
