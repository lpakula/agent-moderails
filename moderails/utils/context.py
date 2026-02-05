"""Context builder for dynamic mode templates."""

from pathlib import Path
from typing import Any, Optional

from ..config import is_private_mode
from ..db.database import find_db_path
from ..db.models import Task, TaskStatus
from ..modes import get_mode
from .git import get_current_branch, get_staged_files, get_unstaged_files, is_git_repo


def load_protocol_partial() -> str:
    """Load the shared protocol partial.
    
    Returns:
        Content of the protocol.md partial, or empty string if not found
    """
    partial_path = Path(__file__).parent.parent / "modes" / "partials" / "protocol.md"
    if partial_path.exists():
        return partial_path.read_text()
    return ""


def get_project_root() -> Optional[Path]:
    """Get the project root directory (parent of _moderails).
    
    Returns:
        Absolute path to project root, or None if no moderails found
    """
    db_path = find_db_path()
    if db_path:
        # db is at _moderails/moderails.db, so parent.parent is project root
        return db_path.parent.parent
    return None


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
        "file_path": f"_moderails/{task.file_name}" if task.file_name else None,
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
    
    # Always include project root so agent knows which project it's working in
    project_root = get_project_root()
    context["project_root"] = str(project_root) if project_root else None
    
    # Start mode - needs in-progress task, draft tasks, epics, and skills
    if mode_name == "start":
        context["current_task"] = get_in_progress_task(services)
        context["draft_tasks"] = get_draft_tasks(services)
        epics = services["epic"].list_all()
        context["epics"] = [{"id": e.id, "name": e.name} for e in epics]
        context["skills"] = services["context"].list_skills()
    
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
    
    # Git state and private mode - only complete mode needs this
    if mode_name == "complete":
        in_git_repo = is_git_repo()
        branch = get_current_branch() if in_git_repo else None
        context["git"] = {
            "is_repo": in_git_repo,
            "branch": branch,
            "is_main": branch == "main" if branch else False,
            "staged_files": get_staged_files() if in_git_repo else [],
            "unstaged_files": get_unstaged_files() if in_git_repo else [],
        }
        context["private"] = is_private_mode()
    
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


def build_rerail_context(services: dict, task, project_root) -> str:
    """Build session context output for --rerail flag (instant resume).
    
    Args:
        services: Dict containing task, context, session services
        task: The in-progress task object
        project_root: Path to the project root
        
    Returns:
        Formatted session context string
    """
    epic = task.epic if task else None
    active_session = services["session"].get_active()
    
    output = []
    
    # Header
    output.append("# Moderails Session\n")
    if project_root:
        output.append(f"**Project**: `{project_root}`")
    output.append(f"**Task**: {task.name} (`{task.id}`) [{task.status.value}]")
    if epic:
        output.append(f"**Epic**: {epic.name} (`{epic.id}`)")
    if active_session:
        output.append(f"**Mode**: {active_session.current_mode.upper()}")
    output.append("")
    
    output.append("---\n")
    
    # Protocol rules (from partial)
    protocol_content = load_protocol_partial()
    if protocol_content:
        output.append(protocol_content)
        output.append("")
        output.append("---\n")
    
    # Mandatory context
    mandatory_content = services["context"].load_mandatory_context()
    if mandatory_content:
        output.append(mandatory_content)
        output.append("")
        output.append("---\n")
    
    # Epic skills
    if epic:
        skills = epic.get_skills()
        if skills:
            output.append(f"## Epic Skills ({epic.name})\n")
            for skill in skills:
                output.append(f"- {skill} (skills/{skill}/SKILL.md)")
            output.append("")
            output.append("---\n")
    
    # Task plan
    if task.file_name:
        task_content = services["task"].get_task_content(task.id)
        if task_content:
            output.append("## Task Plan\n")
            output.append(f"File: `_moderails/{task.file_name}`\n")
            output.append(task_content)
            output.append("")
            output.append("---\n")
    
    # Current mode instructions (skip for "start" - protocol already loaded above)
    mode = active_session.current_mode
    if mode != "start":
        mode_context = build_mode_context(services, mode)
        mode_content = get_mode(mode, mode_context)
        if mode_content:
            output.append(f"## Current Mode: {mode.upper()}\n")
            output.append(mode_content)
            output.append("")
            output.append("---\n")
    
    # Resume instruction (ask before acting)
    output.append("## Resume\n")
    if mode == "start":
        output.append("Session loaded. Ask user to describe the task in more detail before proceeding.")
        output.append("Once you understand the requirements, suggest `#research` to begin analysis.")
    else:
        output.append(f"Current mode is `{mode.upper()}`. Ask the user what to do next before taking any action.")
    
    return "\n".join(output)
