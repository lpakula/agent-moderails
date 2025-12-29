"""CLI for moderails - structured agent workflow with persistent memory."""

import json
from pathlib import Path
from typing import Optional

import click

from . import __version__
from .db.database import find_db_path, get_session, init_db
from .db.models import TaskStatus, TaskType
from .modes import get_mode
from .services import ContextService, EpicService, TaskService
from .services.history import HistoryService
from .utils import (
    create_command_files,
    format_task_line,
    get_current_commit_hash,
    search_context_files,
)


def get_moderails_dir(db_path: Optional[Path] = None) -> Path:
    if db_path:
        return db_path.parent
    found = find_db_path()
    return found.parent if found else Path.cwd() / "moderails"


def get_services(db_path: Optional[Path] = None):
    """Get services. Raises FileNotFoundError if database doesn't exist."""
    session = get_session(db_path)
    moderails_dir = get_moderails_dir(db_path)
    history_file = moderails_dir / "history.json"
    return {
        "task": TaskService(session, moderails_dir),
        "epic": EpicService(session),
        "history": HistoryService(session, history_file),
        "context": ContextService(moderails_dir),
    }


def get_services_or_exit(ctx):
    """Get services or exit with helpful message if database doesn't exist."""
    try:
        return get_services(ctx.obj.get("db_path"))
    except FileNotFoundError:
        click.echo("❌ No moderails database found. Run `moderails init` first.")
        ctx.exit(0)


@click.group()
@click.version_option(version=__version__, prog_name="moderails", message="%(prog)s version %(version)s")
@click.pass_context
def cli(ctx):
    """moderails - structured agent workflow with persistent memory."""
    ctx.ensure_object(dict)
    ctx.obj["db_path"] = None
    
    # Auto-sync history on startup (if DB exists)
    try:
        services = get_services(ctx.obj.get("db_path"))
        imported = services["history"].sync_from_file()
        if imported > 0:
            click.echo(f"✓ Synced {imported} tasks from history.json", err=True)
    except FileNotFoundError:
        pass  # DB doesn't exist yet, skip sync


# ============== INIT ==============

@cli.command()
@click.pass_context
def init(ctx):
    """Initialize moderails in current directory."""
    try:
        db_path = init_db()
        created_commands = create_command_files()
        
        if ctx.obj.get("json"):
            click.echo(json.dumps({"status": "initialized", "path": str(db_path), "commands": created_commands}))
        else:
            # Use relative paths from current directory
            cwd = Path.cwd()
            rel_db_path = Path(db_path).relative_to(cwd) if Path(db_path).is_relative_to(cwd) else db_path
            rel_commands = [Path(cmd).relative_to(cwd) if Path(cmd).is_relative_to(cwd) else cmd for cmd in created_commands]
            
            click.echo()
            click.echo(click.style("✓ ModeRails initialized successfully!", fg="green", bold=True))
            click.echo()
            click.echo(f"  Database:  {click.style(str(rel_db_path), fg='cyan')}")
            for cmd in rel_commands:
                click.echo(f"  Commands:  {click.style(str(cmd), fg='cyan')}")
            click.echo()
            click.echo(click.style("Getting started:", fg="white", bold=True))
            click.echo()
            click.echo(f"  Type {click.style('/moderails', fg='yellow')} in your editor to activate the protocol.")
            click.echo("  The AI agent will guide you through the process.")
            click.echo()
            click.echo(click.style("Example commands:", fg="white", bold=True))
            click.echo()
            click.echo(f"  {click.style('moderails list', fg='green')} - See all tasks")
            click.echo()
            click.echo(click.style("💡 Tip:", fg="blue") + " Run 'moderails --help' for more")
            click.echo()
    except ValueError as e:
        click.echo(f"❌ Invalid base directory: {e}")
        return


# ============== START ==============

@cli.command()
@click.pass_context
def start(ctx):
    """Show protocol overview and current status with agent guidance."""
    # Print protocol overview with CLI commands
    click.echo(get_mode("start"))
    click.echo("\n---\n")
    
    try:
        services = get_services(ctx.obj.get("db_path"))
    except FileNotFoundError:
        click.echo("No moderails database found. Run `moderails init` first.")
        return
    
    # Show current status
    all_tasks = services["task"].list_all()
    epics = services["epic"].list_all()
    
    # Filter to only show todo and in-progress tasks
    tasks = [t for t in all_tasks if t.status in [TaskStatus.DRAFT, TaskStatus.IN_PROGRESS]]
    
    click.echo("## CURRENT STATUS\n")
    
    if not tasks and not epics:
        click.echo("No tasks in progress.")
        return
    
    if not tasks:
        click.echo("No active tasks (all tasks completed).")
        return
    
    # Sort tasks by created_at, newest at top (reverse=True)
    sorted_tasks = sorted(tasks, key=lambda x: x.created_at, reverse=True)
    
    # Display flat list with details
    for idx, t in enumerate(sorted_tasks, 1):
        click.echo(f"{idx}. Task ID: {t.id}  (use this ID for commands)")
        click.echo(f"   Name: {t.name}")
        click.echo(f"   Type: {t.type.value}")
        
        # Epic (if any)
        if t.epic:
            click.echo(f"   Epic: {t.epic.name}")
        
        # Status
        click.echo(f"   Status: {t.status.value}")
        
        # Timestamp
        if t.status == TaskStatus.COMPLETED and t.completed_at:
            timestamp = t.completed_at.strftime("%Y-%m-%d %H:%M")
            click.echo(f"   Completed: {timestamp}")
        else:
            timestamp = t.created_at.strftime("%Y-%m-%d %H:%M")
            click.echo(f"   Created: {timestamp}")
        
        click.echo()  # Empty line between tasks
    


# ============== TASK GROUP ==============

@cli.group()
@click.pass_context
def task(ctx):
    """Task management commands."""
    pass


@task.command("create")
@click.option("--name", "-n", required=True, help="Task name")
@click.option("--epic", "-e", help="Epic ID (6-character, optional)")
@click.option("--type", "-t", type=click.Choice(["feature", "fix", "refactor", "maintenance"]), default="feature", help="Task type (default: feature)")
@click.pass_context
def task_create(ctx, name: str, epic: Optional[str], type: str):
    """Create a new task."""
    services = get_services_or_exit(ctx)
    
    # Load mandatory context
    mandatory_context = services["context"].load_mandatory_context()
    if mandatory_context:
        click.echo(mandatory_context)
        click.echo("\n---\n")
    
    # Load epic context if exists
    epic_obj = None
    if epic:
        epic_obj = services["epic"].get(epic)
        if not epic_obj:
            click.echo(f"❌ Epic '{epic}' not found")
            return
        
        epic_summary = services["epic"].get_summary(epic_obj.name)
        if epic_summary:
            click.echo("## EPIC CONTEXT\n")
            click.echo(epic_summary)
            click.echo("\n---\n")
    
    try:
        task_type = TaskType(type)
        task = services["task"].create(name=name, epic_id=epic if epic else None, task_type=task_type)
        
        click.echo(f"✅ Task created: {task.id} - {click.style(task.name, fg='green', bold=True)}")
        click.echo(f"   Type: {task.type.value}")
        if epic_obj:
            click.echo(f"📁 Epic: {epic_obj.id} - {epic_obj.name}")
        click.echo(f"📄 File: {task.file_path}")
        click.echo(f"Status: {task.status.value}")
        
        click.echo("\n---\n")
        click.echo("## AGENT GUIDANCE\n")
        click.echo("User should type `#research` to begin working on this task.")
    except ValueError as e:
        click.echo(f"❌ Error: {e}")


@task.command("update")
@click.option("--task", "-t", "task_id", required=True, help="Task ID (6-character)")
@click.option("--status", "-s", type=click.Choice(["draft", "in-progress", "completed"]))
@click.option("--summary", help="Task summary")
@click.option("--git-hash", help="Git commit hash")
@click.pass_context
def task_update(ctx, task_id: str, status: Optional[str], summary: Optional[str], git_hash: Optional[str]):
    """Update task status, summary, or git hash."""
    services = get_services_or_exit(ctx)
    
    status_enum = TaskStatus(status) if status else None
    t = services["task"].update(task_id, status=status_enum, summary=summary, git_hash=git_hash)
    
    if not t:
        click.echo(f"❌ Task '{task_id}' not found")
        return
    
    click.echo(f"✅ Updated task: {t.id} - {t.name} [{t.status.value}]")
    
    if status == "completed":
        click.echo("\n💡 Now commit your changes with a descriptive message")


@task.command("delete")
@click.option("--task", "-t", "task_id", required=True, help="Task ID (6-character)")
@click.option("--confirm", is_flag=True, help="Confirm deletion")
@click.pass_context
def task_delete(ctx, task_id: str, confirm: bool):
    """Delete a task."""
    if not confirm:
        click.echo("Use --confirm to delete")
        return
    
    services = get_services_or_exit(ctx)
    if services["task"].delete(task_id):
        click.echo(f"✅ Deleted task: {task_id}")
    else:
        click.echo(f"❌ Task '{task_id}' not found")


@task.command("complete")
@click.option("--task", "-t", "task_id", required=True, help="Task ID (6-character)")
@click.option("--summary", "-s", help="Task summary")
@click.pass_context
def task_complete(ctx, task_id: str, summary: Optional[str]):
    """Mark task as completed and export to history.json."""
    services = get_services_or_exit(ctx)
    moderails_dir = get_moderails_dir(ctx.obj.get("db_path"))
    repo_dir = moderails_dir.parent
    
    try:
        # Update summary if provided
        if summary:
            services["task"].update(task_id, summary=summary)
        
        # Capture git hash from HEAD (assumes user already committed)
        git_hash = get_current_commit_hash(repo_dir)
        
        # Complete the task
        task = services["task"].complete(task_id, git_hash=git_hash)
        click.echo(f"✅ Task completed: {task.id} - {task.name}")
        
        if git_hash:
            click.echo(f"✅ Captured git hash: {git_hash[:7]}")
        
        # Export to history.json
        services["history"].export_task(task_id)
        click.echo("✅ Exported to history.json")
        
    except ValueError as e:
        click.echo(f"❌ {e}")


@task.command("load")
@click.option("--task", "-t", "task_id", required=True, help="Task ID (6-character)")
@click.pass_context
def task_load(ctx, task_id: str):
    """Load task details and epic context."""
    services = get_services_or_exit(ctx)
    moderails_dir = get_moderails_dir(ctx.obj.get("db_path"))
    
    # Load mandatory context
    mandatory_context = services["context"].load_mandatory_context()
    if mandatory_context:
        click.echo(mandatory_context)
        click.echo("\n---\n")
    
    # Get task
    task = services["task"].get(task_id)
    if not task:
        click.echo(f"❌ Task '{task_id}' not found")
        return
    
    # Display task details
    click.echo("## TASK DETAILS\n")
    click.echo(f"**ID**: {task.id}")
    click.echo(f"**Name**: {task.name}")
    click.echo(f"**Type**: {task.type.value}")
    click.echo(f"**Status**: {task.status.value}")
    if task.epic:
        click.echo(f"**Epic**: {task.epic.name} ({task.epic_id})")
    click.echo(f"**File**: .moderails/{task.file_name}")
    if task.summary:
        click.echo(f"**Summary**: {task.summary}")
    click.echo()
    
    # Load task file content
    task_file = moderails_dir / task.file_name
    if task_file.exists():
        click.echo("## TASK PLAN\n")
        click.echo(task_file.read_text())
        click.echo()
    
    # Load epic context if task belongs to an epic
    if task.epic:
        click.echo("## EPIC CONTEXT\n")
        epic_summary = services["epic"].get_summary(task.epic.name)
        if epic_summary:
            click.echo(epic_summary)
        else:
            click.echo("(no completed tasks in this epic yet)")


# ============== EPIC GROUP ==============

@cli.group()
@click.pass_context
def epic(ctx):
    """Epic management commands."""
    pass


@epic.command("create")
@click.option("--name", "-n", required=True, help="Epic name (can include spaces)")
@click.pass_context
def epic_create(ctx, name: str):
    """Create a new epic."""
    services = get_services_or_exit(ctx)
    
    try:
        e = services["epic"].create(name)
        click.echo(f"✅ Created epic: {e.id} - {e.name}")
    except Exception as ex:
        click.echo(f"❌ Error creating epic: {ex}")


@epic.command("update")
@click.option("--epic", "-e", "epic_id", required=True, help="Epic ID (6-character)")
@click.option("--name", "-n", required=True, help="New epic name")
@click.pass_context
def epic_update(ctx, epic_id: str, name: str):
    """Update epic name."""
    services = get_services_or_exit(ctx)
    
    epic_obj = services["epic"].get(epic_id)
    if not epic_obj:
        click.echo(f"❌ Epic '{epic_id}' not found")
        return
    
    try:
        epic_obj.name = name
        services["epic"].session.commit()
        click.echo(f"✅ Updated epic: {epic_obj.id} - {epic_obj.name}")
    except Exception as ex:
        services["epic"].session.rollback()
        click.echo(f"❌ Error updating epic: {ex}")


@epic.command("list")
@click.pass_context
def epic_list(ctx):
    """List all epics."""
    services = get_services_or_exit(ctx)
    
    epics = services["epic"].list_all()
    
    if not epics:
        click.echo("No epics found.")
        return
    
    for epic in epics:
        click.echo(f"{click.style(epic.id, fg='cyan')} - {click.style(epic.name, fg='blue', bold=True)}")


# ============== MODE ==============

@cli.command("mode")
@click.option("--name", "-n", required=True, help="Mode name")
@click.pass_context
def mode(ctx, name: str):
    """Get mode definition. Use when switching modes (e.g., //execute)."""
    valid_modes = ["research", "brainstorm", "plan", "execute", "complete", "abort"]
    if name not in valid_modes:
        click.echo(f"❌ Invalid mode. Valid modes: {', '.join(valid_modes)}")
        return
    
    click.echo(get_mode(name))


# ============== LIST ==============

@cli.command("list")
@click.option("--status", "-s", type=click.Choice(["draft", "in-progress", "completed"]), help="Filter by status")
@click.pass_context
def list_tasks(ctx, status: Optional[str]):
    """List all tasks in chronological order."""
    services = get_services_or_exit(ctx)
    
    # Get all tasks
    status_enum = TaskStatus(status) if status else None
    tasks = services["task"].list_all(status=status_enum)
    
    if not tasks:
        click.echo("No tasks found.")
        return
    
    # Sort all tasks by most recent timestamp (completed_at for completed, created_at for others)
    # Newest at top (reverse=True)
    sorted_tasks = sorted(
        tasks,
        key=lambda x: x.completed_at if (x.status == TaskStatus.COMPLETED and x.completed_at) else x.created_at,
        reverse=True
    )
    
    # Display: task_id [type] [status] [epic] [timestamp] - task name
    for task in sorted_tasks:
        click.echo(format_task_line(task))


# ============== CONTEXT GROUP ==============

@cli.group()
@click.pass_context
def context(ctx):
    """Context management commands."""
    pass




@context.command("search")
@click.option("--query", "-q", help="Search query for context files and task history")
@click.option("--file", "-f", help="File path to search tasks by file")
@click.pass_context
def context_search(ctx, query: Optional[str], file: Optional[str]):
    """Search context files and task history."""
    if not query and not file:
        click.echo("❌ Provide either --query or --file")
        return
    
    if query and file:
        click.echo("❌ Use either --query or --file, not both")
        return
    
    services = get_services_or_exit(ctx)
    moderails_dir = get_moderails_dir(ctx.obj.get("db_path"))
    
    click.echo("## CONTEXT SEARCH\n")
    
    # 1. Search context files (only if query provided, search in context/search/ directory)
    if query:
        search_dir = moderails_dir / "context" / "search"
        click.echo(f"### CONTEXT FILES (query: '{query}')\n")
        
        search_results = search_context_files(query, search_dir)
        if search_results:
            click.echo(search_results)
        else:
            click.echo("No matches in context files")
        
        click.echo("\n---\n")
    
    # 2. Search task history
    if file:
        click.echo(f"### TASK HISTORY (file: '{file}')\n")
        history_results = services["history"].search_by_file(file)
    else:
        click.echo(f"### TASK HISTORY (query: '{query}')\n")
        history_results = services["history"].search_by_query(query)
    
    if history_results:
        click.echo(f"Found {len(history_results)} related task(s):\n")
        for result in history_results:
            epic_str = f" [{result['epic']}]" if result.get('epic') else ""
            click.echo(click.style(f"{result['name']}{epic_str}", fg="green"))
            click.echo(f"  Status: {result['status']}")
            click.echo(f"  Summary: {result['summary']}")
            if result.get('files_changed'):
                click.echo(f"  Files: {', '.join(result['files_changed'][:5])}")
            if result.get('git_hash'):
                click.echo(f"  Git: {result['git_hash'][:7]}")
            click.echo()
    else:
        click.echo("No matching tasks in history")


# ============== SYNC ==============

@cli.command("sync")
@click.option("--force", is_flag=True, help="Force sync even if file hasn't changed")
@click.pass_context
def sync(ctx, force: bool):
    """Manually sync from history.json."""
    services = get_services_or_exit(ctx)
    
    if force:
        services["history"]._last_mtime = None
    
    imported = services["history"].sync_from_file()
    
    if imported > 0:
        click.echo(f"✅ Imported {imported} tasks from history.json")
    else:
        click.echo("✓ Already in sync")


if __name__ == "__main__":
    cli()
