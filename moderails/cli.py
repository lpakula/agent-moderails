"""CLI for moderails - structured agent workflow with persistent memory."""

import json
import subprocess
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
)
from .utils.git import get_staged_files


def get_moderails_dir(db_path: Optional[Path] = None) -> Path:
    if db_path:
        return db_path.parent
    found = find_db_path()
    return found.parent if found else Path.cwd() / "moderails"


def get_services(db_path: Optional[Path] = None):
    """Get services. Raises FileNotFoundError if database doesn't exist."""
    session = get_session(db_path)
    moderails_dir = get_moderails_dir(db_path)
    history_file = moderails_dir / "history.jsonl"
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


def check_and_migrate():
    """Check and run database migrations if needed.
    
    Returns:
        True if migrations were run, False otherwise
    """
    try:
        from moderails.db.database import find_db_path
        from moderails.db.migrations import auto_migrate
        
        db_path = find_db_path()
        if db_path:
            migrated = auto_migrate(db_path)
            if migrated:
                click.echo("✓ Database migrated to latest schema")
                return True
        return False
    except Exception:
        return False


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
            click.echo(f"✓ Synced {imported} tasks from history.jsonl", err=True)
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
            click.echo(f"  {click.style('moderails epic list', fg='green')} - See all epics")
            click.echo()
            click.echo(click.style("💡 Tip:", fg="blue") + " Run 'moderails --help' for more")
            click.echo()
    except ValueError as e:
        click.echo(f"❌ Invalid base directory: {e}")
        return


# ============== MIGRATE ==============

@cli.command()
@click.pass_context
def migrate(ctx):
    """Run database migrations to latest schema version."""
    from moderails.db.database import find_db_path
    from moderails.db.migrations import get_schema_version, CURRENT_VERSION
    
    db_path = find_db_path()
    if not db_path:
        click.echo(click.style("✗ No database found. Run: moderails init", fg="red"))
        ctx.exit(1)
    
    current = get_schema_version(db_path)
    click.echo(f"Current schema version: {current}")
    click.echo(f"Latest schema version: {CURRENT_VERSION}")
    
    if current < CURRENT_VERSION:
        click.echo("\nApplying migrations...")
        migrated = check_and_migrate()
        if migrated:
            click.echo(click.style("✓ Database migrated successfully", fg="green"))
        else:
            click.echo(click.style("✗ Migration failed", fg="red"))
            ctx.exit(1)
    else:
        click.echo(click.style("✓ Database is up to date", fg="green"))


# ============== START ==============

@cli.command()
@click.pass_context
def start(ctx):
    """Show protocol overview and current status with agent guidance."""
    # Auto-migrate database if needed (before showing status)
    if check_and_migrate():
        click.echo()  # Add blank line after migration message
    
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
@click.option("--type", "-t", type=click.Choice(["feature", "fix", "refactor", "chore"]), default="feature", help="Task type (default: feature)")
@click.option("--status", "-s", type=click.Choice(["draft", "in-progress"]), default="draft", help="Initial task status (default: draft)")
@click.option("--no-file", is_flag=True, help="Skip task file creation")
@click.option("--no-context", is_flag=True, help="Suppress context output")
@click.pass_context
def task_create(ctx, name: str, epic: Optional[str], type: str, status: str, no_file: bool, no_context: bool):
    """Create a new task."""
    services = get_services_or_exit(ctx)
    
    # Validate epic first if provided
    epic_obj = None
    if epic:
        epic_obj = services["epic"].get(epic)
        if not epic_obj:
            click.echo(f"❌ Epic '{epic}' not found")
            return
    
    # Load and display context unless suppressed
    if not no_context:
        # Load mandatory context
        mandatory_context = services["context"].load_mandatory_context()
        if mandatory_context:
            click.echo(mandatory_context)
            click.echo("\n---\n")
        
        # Load epic context if exists
        if epic_obj:
            epic_summary = services["epic"].get_summary(epic_obj.name)
            if epic_summary:
                click.echo("## EPIC CONTEXT\n")
                click.echo(epic_summary)
                click.echo("\n---\n")
    
    try:
        task_type = TaskType(type)
        task_status = TaskStatus(status)
        task = services["task"].create(
            name=name, 
            epic_id=epic if epic else None, 
            task_type=task_type, 
            status=task_status,
            create_file=not no_file
        )
        
        # Always show task creation result
        click.echo(f"✅ Task created: {task.id} - {click.style(task.name, fg='green', bold=True)}")
        click.echo(f"   Type: {task.type.value}")
        if epic_obj:
            click.echo(f"   Epic: {epic_obj.id} - {epic_obj.name}")
        click.echo(f"   Status: {task.status.value}")
        
        if not no_context:
            if not no_file:
                click.echo(f"   File: {task.file_path}")
            click.echo("\n---\n")
            click.echo("## AGENT GUIDANCE\n")
            click.echo("User should type `#research` to begin working on this task.")
        
        # Return task for programmatic use (e.g., in snapshot workflow)
        return task
    except ValueError as e:
        click.echo(f"❌ Error: {e}")
        return None


@task.command("update")
@click.option("--task", "-t", "task_id", required=True, help="Task ID (6-character)")
@click.option("--name", help="New task name")
@click.option("--status", "-s", type=click.Choice(["draft", "in-progress", "completed"]))
@click.option("--type", type=click.Choice(["feature", "fix", "refactor", "chore"]), help="New task type")
@click.option("--summary", help="Task summary")
@click.option("--git-hash", help="Git commit hash")
@click.option("--file-name", help="Task file name (e.g., my-task.md)")
@click.pass_context
def task_update(ctx, task_id: str, name: Optional[str], status: Optional[str], type: Optional[str], summary: Optional[str], git_hash: Optional[str], file_name: Optional[str]):
    """Update task name, status, type, summary, git hash, or file name."""
    services = get_services_or_exit(ctx)
    
    status_enum = TaskStatus(status) if status else None
    type_enum = TaskType(type) if type else None
    t = services["task"].update(task_id, name=name, status=status_enum, task_type=type_enum, summary=summary, git_hash=git_hash, file_name=file_name)
    
    if not t:
        click.echo(f"❌ Task '{task_id}' not found")
        return
    
    click.echo(f"✅ Updated task: {t.id} - {t.name} [{t.type.value}] [{t.status.value}]")
    
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
    """Mark task as completed"""
    services = get_services_or_exit(ctx)
    
    # Check for staged files (required for files_changed in history)
    staged_files = get_staged_files()
    if not staged_files:
        click.echo("❌ No staged files found.")
        click.echo("\n💡 Stage your changes first:")
        click.echo("   git add <file1> <file2> ...")
        click.echo("\nThen run this command again.")
        return
    
    try:
        # Update summary if provided
        if summary:
            services["task"].update(task_id, summary=summary)
        
        # Complete the task (without git hash - that comes later via task update)
        task = services["task"].complete(task_id, git_hash=None)
        click.echo(f"✅ Task completed: {task.id} - {task.name}")
        
        # Export to history.jsonl and stage it
        services["history"].export_task(task_id)
        
        # Auto-stage history.jsonl for the commit
        moderails_dir = get_moderails_dir(ctx.obj.get("db_path"))
        history_path = moderails_dir / "history.jsonl"
        subprocess.run(["git", "add", str(history_path)], check=False)
        
        click.echo("✅ Exported and staged history.jsonl")
        
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
    valid_modes = ["fast", "research", "brainstorm", "plan", "execute", "complete", "abort"]
    if name not in valid_modes:
        click.echo(f"❌ Invalid mode. Valid modes: {', '.join(valid_modes)}")
        return
    
    click.echo(get_mode(name))


# ============== LIST ==============

@cli.command("list")
@click.option("--status", "-s", type=click.Choice(["draft", "in-progress", "completed"]), help="Filter by status")
@click.pass_context
def list_tasks(ctx, status: Optional[str]):
    """List all tasks (active first, completed at bottom)."""
    services = get_services_or_exit(ctx)
    
    # Get all tasks
    status_enum = TaskStatus(status) if status else None
    tasks = services["task"].list_all(status=status_enum)
    
    if not tasks:
        click.echo("No tasks found.")
        return
    
    # Sort: non-completed tasks first (newest at top), then completed tasks at bottom (newest at top)
    sorted_tasks = sorted(
        tasks,
        key=lambda x: (
            x.status == TaskStatus.COMPLETED,  # False (0) first, True (1) last
            -(x.completed_at if (x.status == TaskStatus.COMPLETED and x.completed_at) else x.created_at).timestamp()
        )
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




@context.command("list")
@click.pass_context
def context_list(ctx):
    """List available memories and files from history."""
    services = get_services_or_exit(ctx)
    
    click.echo("## AVAILABLE CONTEXT\n")
    
    # 1. List available memories
    memories = services["context"].list_memories()
    click.echo("### MEMORIES\n")
    if memories:
        for memory in memories:
            click.echo(f"- {memory}")
    else:
        click.echo("No memories")
    
    click.echo()
    
    # 2. Show files from history
    click.echo("### FILES\n")
    files_tree = services["context"].get_files_tree()
    if files_tree:
        click.echo(files_tree)
    else:
        click.echo("No files")
    
    # 3. Usage instructions
    click.echo("\n---\n")
    click.echo("### USAGE\n")
    click.echo("```sh")
    click.echo("# Load all context types (flags can be combined)")
    click.echo("moderails context load --memory auth --memory payments --file src/auth.ts")
    click.echo("```")


@context.command("load")
@click.option("--mandatory", "-m", is_flag=True, help="Load mandatory context")
@click.option("--memory", "-M", multiple=True, help="Memory name to load (can specify multiple)")
@click.option("--file", "-f", multiple=True, help="File path to search tasks (can specify multiple)")
@click.pass_context
def context_load(ctx, mandatory: bool, memory: tuple, file: tuple):
    """Load context: mandatory, memories, and/or files. Flags can be combined."""
    if not mandatory and not memory and not file:
        click.echo("❌ Provide --mandatory, --memory, or --file")
        click.echo("\n💡 Run `moderails context list` to see available options")
        return
    
    services = get_services_or_exit(ctx)
    moderails_dir = get_moderails_dir(ctx.obj.get("db_path"))
    
    output_parts = []
    
    # 1. Load mandatory context
    if mandatory:
        mandatory_context = services["context"].load_mandatory_context()
        if mandatory_context:
            output_parts.append(mandatory_context)
        else:
            output_parts.append("No mandatory context files found.")
            output_parts.append(f"Add markdown files to: {moderails_dir / 'context' / 'mandatory'}/")
    
    # 2. Load memories by name
    if memory:
        memory_content = services["context"].load_memories(list(memory))
        
        if memory_content:
            output_parts.append(memory_content)
        else:
            available = services["context"].list_memories()
            msg = f"❌ No memories found for: {', '.join(memory)}"
            if available:
                msg += f"\nAvailable: {', '.join(available)}"
            output_parts.append(msg)
    
    # 3. Search task history by file(s)
    if file:
        for file_path in file:
            history_results = services["history"].search_by_file(file_path)
            
            if history_results:
                file_parts = [f"## FILE HISTORY: {file_path}\n"]
                file_parts.append(f"Found {len(history_results)} related task(s):\n")
                for result in history_results:
                    epic_str = f" [{result['epic']}]" if result.get('epic') else ""
                    file_parts.append(f"**{result['name']}{epic_str}**")
                    file_parts.append(f"  Status: {result['status']}")
                    file_parts.append(f"  Summary: {result['summary']}")
                    if result.get('files_changed'):
                        file_parts.append(f"  Files: {', '.join(result['files_changed'][:5])}")
                    if result.get('git_hash'):
                        file_parts.append(f"  Git: {result['git_hash'][:7]}")
                    file_parts.append("")
                output_parts.append("\n".join(file_parts))
            else:
                output_parts.append(f"No tasks found for file: {file_path}")
    
    # Output all parts with separators
    click.echo("\n---\n".join(output_parts))


# ============== SYNC ==============

@cli.command("sync")
@click.option("--force", is_flag=True, help="Force sync even if file hasn't changed")
@click.pass_context
def sync(ctx, force: bool):
    """Manually sync from history.jsonl."""
    services = get_services_or_exit(ctx)
    
    if force:
        services["history"]._last_mtime = None
    
    imported = services["history"].sync_from_file()
    
    if imported > 0:
        click.echo(f"✅ Imported {imported} tasks from history.jsonl")
    else:
        click.echo("✓ Already in sync")


if __name__ == "__main__":
    cli()
