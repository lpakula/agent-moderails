"""CLI for moderails - structured agent workflow with persistent memory."""

import json
from pathlib import Path
from typing import Optional

import click

from .db.database import find_db_path, get_session, init_db
from .db.models import TaskStatus
from .modes import get_mode
from .services import ContextService, EpicService, TaskService


def get_moderails_dir(db_path: Optional[Path] = None) -> Path:
    if db_path:
        return db_path.parent
    found = find_db_path()
    return found.parent if found else Path.cwd() / "moderails"


def get_services(db_path: Optional[Path] = None):
    session = get_session(db_path)
    moderails_dir = get_moderails_dir(db_path)
    return {
        "task": TaskService(session, moderails_dir),
        "epic": EpicService(session),
        "context": ContextService(moderails_dir),
    }


@click.group()
@click.pass_context
def cli(ctx):
    """moderails - structured agent workflow with persistent memory."""
    ctx.ensure_object(dict)
    ctx.obj["db_path"] = None


# ============== INIT ==============

def get_template_path(name: str) -> Path:
    """Get path to a template file."""
    return Path(__file__).parent / "templates" / name


def create_command_files():
    """Create command files for Cursor and Claude Code."""
    template_path = get_template_path("moderails.md")
    template_content = template_path.read_text()
    
    command_dirs = [
        Path.cwd() / ".cursor" / "commands",
        Path.cwd() / ".claude" / "commands",
    ]
    
    created = []
    for cmd_dir in command_dirs:
        cmd_file = cmd_dir / "moderails.md"
        if not cmd_file.exists():
            cmd_dir.mkdir(parents=True, exist_ok=True)
            cmd_file.write_text(template_content)
            created.append(str(cmd_file))
    
    return created


@cli.command()
@click.option("--base-dir", "-b", default="agent", help="Base directory name (default: agent)")
@click.pass_context
def init(ctx, base_dir: str):
    """Initialize moderails in current directory."""
    try:
        db_path = init_db(base_dir=base_dir)
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
            click.echo("  → Initialize the protocol in your editor:")
            click.echo(f"      {click.style('/moderails', fg='yellow')}")
            click.echo("  → Build your project context (one-time setup):")
            click.echo(f"      {click.style('#onboard', fg='yellow')}")
            click.echo()
            click.echo("  → Check status anytime:")
            click.echo(f"      {click.style('moderails', fg='green')} status")
            click.echo()
            click.echo(click.style("💡 Tip:", fg="blue") + " Run 'moderails --help' to see all commands")
            click.echo()
    except ValueError as e:
        click.echo(f"❌ Invalid base directory: {e}")
        return


# ============== START ==============

@cli.command()
@click.option("--new", "is_new", is_flag=True, help="Create new task")
@click.option("--task", "-t", "task_name", help="Task name")
@click.option("--epic", "-e", help="Epic name (required with --new)")
@click.option("--tags", help="Tags (with --new)")
@click.pass_context
def start(ctx, is_new: bool, task_name: Optional[str], epic: Optional[str], tags: Optional[str]):
    """Start moderails session or create new task.
    
    New task:     moderails start --new --task "task" --epic "epic" --tags "auth,api"
    Existing:     moderails start --task "task"
    Session:      moderails start
    """
    # Print protocol overview
    click.echo(get_mode("start"))
    click.echo("\n---\n")
    
    try:
        services = get_services(ctx.obj.get("db_path"))
    except FileNotFoundError:
        click.echo("No moderails database found. Run `moderails init` first.")
        return
    
    if is_new:
        if not task_name or not epic:
            click.echo("❌ --task and --epic required with --new")
            return
        
        # Load epic context if exists
        epic_obj = services["epic"].get_by_name(epic)
        if epic_obj:
            epic_summary = services["epic"].get_summary(epic)
            if epic_summary:
                click.echo("## EPIC CONTEXT\n")
                click.echo(epic_summary)
                click.echo("\n---\n")
        
        # Load context (mandatory + tag-based)
        tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []
        context_content = services["context"].load_for_tags(tag_list)
        if context_content:
            click.echo("## PROJECT CONTEXT\n")
            click.echo(context_content)
            click.echo("\n---\n")
        
        task = services["task"].create(name=task_name, epic_name=epic, tags=tags)
        click.echo(f"✅ Created task: {task.name}")
        click.echo(f"📁 File: {task.file_path}")
        
        click.echo("\n💡 Suggested: Go into RESEARCH mode to explore the task scope.")
        
    elif task_name:
        task = services["task"].get_by_name(task_name)
        if not task:
            click.echo(f"❌ Task '{task_name}' not found")
            return
        
        # Load epic context
        epic_summary = services["epic"].get_summary(task.epic.name)
        if epic_summary:
            click.echo("## EPIC CONTEXT\n")
            click.echo(epic_summary)
            click.echo("\n---\n")
        
        # Load context (mandatory + epic tag-based)
        tag_list = [t.strip() for t in task.epic.tag.split(",") if t.strip()] if task.epic.tag else []
        context_content = services["context"].load_for_tags(tag_list)
        if context_content:
            click.echo("## PROJECT CONTEXT\n")
            click.echo(context_content)
            click.echo("\n---\n")
        
        # Load task content
        content = services["task"].get_task_content(task_name)
        click.echo(f"## TASK: {task.name} [{task.status.value}]\n")
        click.echo(f"Epic: {task.epic.name}")
        click.echo(f"File: {task.file_path}\n")
        
        if content:
            click.echo("---\n")
            click.echo(content)
        
        click.echo("\n---\n")
        
        if task.status == TaskStatus.TODO:
            click.echo("💡 Suggested: Go into RESEARCH mode")
        else:
            click.echo("💡 Suggested: Go into EXECUTE mode to continue work")
    
    else:
        # Session overview
        tasks = services["task"].list_all()
        epics = services["epic"].list_all()
        
        click.echo("## CURRENT STATUS\n")
        
        if not epics:
            click.echo("No epics yet. Create a task with: moderails start --new --task 'task' --epic 'epic'")
            return
        
        click.echo("Epics and Tasks:")
        for e in epics:
            tag_str = f" (tags: {e.tag})" if e.tag else " (no tags)"
            click.echo(f"  Epic: {e.name}{tag_str}")
            epic_tasks = [t for t in tasks if t.epic_id == e.id]
            if epic_tasks:
                for t in epic_tasks:
                    click.echo(f"    - Task: {t.name} ({t.status.value})")
            else:
                click.echo("    (no tasks)")
        
        in_progress = [t for t in tasks if t.status == TaskStatus.IN_PROGRESS]
        todo = [t for t in tasks if t.status == TaskStatus.TODO]
        
        click.echo("\n---")
        if in_progress:
            click.echo(f"💡 Continue task: moderails start --task \"{in_progress[0].name}\"")
        elif todo:
            click.echo(f"💡 Start task: moderails start --task \"{todo[0].name}\"")
        else:
            click.echo("💡 Create new task: moderails start --new --task \"task\" --epic \"epic\"")


# ============== TASK GROUP ==============

@cli.group()
@click.pass_context
def task(ctx):
    """Task management commands."""
    pass


@task.command("update")
@click.option("--task", "-t", "task_name", required=True, help="Task name")
@click.option("--status", "-s", type=click.Choice(["todo", "in-progress", "completed"]))
@click.option("--summary", help="Task summary")
@click.option("--git-hash", help="Git commit hash")
@click.pass_context
def task_update(ctx, task_name: str, status: Optional[str], summary: Optional[str], git_hash: Optional[str]):
    """Update task status, summary, or git hash."""
    services = get_services(ctx.obj.get("db_path"))
    
    status_enum = TaskStatus(status) if status else None
    t = services["task"].update(task_name, status=status_enum, summary=summary, git_hash=git_hash)
    
    if not t:
        click.echo(f"❌ Task '{task_name}' not found")
        return
    
    click.echo(f"✅ Updated task: {t.name} [{t.status.value}]")
    
    if status == "completed":
        click.echo("\n💡 Now commit your changes with a descriptive message")


@task.command("delete")
@click.option("--task", "-t", "task_name", required=True, help="Task name")
@click.option("--confirm", is_flag=True, help="Confirm deletion")
@click.pass_context
def task_delete(ctx, task_name: str, confirm: bool):
    """Delete a task."""
    if not confirm:
        click.echo("Use --confirm to delete")
        return
    
    services = get_services(ctx.obj.get("db_path"))
    if services["task"].delete(task_name):
        click.echo(f"✅ Deleted task: {task_name}")
    else:
        click.echo(f"❌ Task '{task_name}' not found")


# ============== EPIC GROUP ==============

@cli.group()
@click.pass_context
def epic(ctx):
    """Epic management commands."""
    pass


@epic.command("update")
@click.option("--name", "-n", required=True, help="Epic name")
@click.option("--tags", "-t", required=True, help="New tags for the epic")
@click.pass_context
def epic_update(ctx, name: str, tags: str):
    """Update epic tags."""
    services = get_services(ctx.obj.get("db_path"))
    
    e = services["epic"].update(name, tag=tags)
    if not e:
        click.echo(f"❌ Epic '{name}' not found")
        return
    
    click.echo(f"✅ Updated epic: {e.name} [{e.tag}]")


@epic.command("delete")
@click.option("--name", "-n", required=True, help="Epic name")
@click.option("--confirm", is_flag=True, help="Confirm deletion")
@click.pass_context
def epic_delete(ctx, name: str, confirm: bool):
    """Delete an epic and all its tasks."""
    if not confirm:
        click.echo("Use --confirm to delete (this will delete all tasks under the epic)")
        return
    
    services = get_services(ctx.obj.get("db_path"))
    
    # Delete all tasks under the epic first
    task_list = services["task"].list_all(epic_name=name)
    for t in task_list:
        services["task"].delete(t.name)
    
    if services["epic"].delete(name):
        click.echo(f"✅ Deleted epic: {name} ({len(task_list)} tasks)")
    else:
        click.echo(f"❌ Epic '{name}' not found")


@epic.command("summary")
@click.option("--name", "-n", required=True, help="Epic name")
@click.option("--short", is_flag=True, help="Show only filenames (no diffs)")
@click.pass_context
def epic_summary(ctx, name: str, short: bool):
    """Get epic summary with completed task summaries and git diff."""
    services = get_services(ctx.obj.get("db_path"))
    
    summary = services["epic"].get_summary(name, short=short)
    if not summary:
        click.echo(f"❌ Epic '{name}' not found")
        return
    
    click.echo(summary)


# ============== MODE ==============

@cli.command("mode")
@click.option("--name", "-n", required=True, help="Mode name")
@click.pass_context
def mode(ctx, name: str):
    """Get mode definition. Use when switching modes (e.g., //execute)."""
    valid_modes = ["onboard", "research", "brainstorm", "plan", "execute", "complete", "abort", "archive"]
    if name not in valid_modes:
        click.echo(f"❌ Invalid mode. Valid modes: {', '.join(valid_modes)}")
        return
    
    click.echo(get_mode(name))


# ============== STATUS ==============

@cli.command("status")
@click.option("--full", is_flag=True, help="Show full summaries without truncation")
@click.pass_context
def status(ctx, full: bool):
    """Show all epics and tasks with status."""
    services = get_services(ctx.obj.get("db_path"))
    
    epics = services["epic"].list_all()
    tasks = services["task"].list_all()
    
    if not epics:
        click.echo("No epics found.")
        return
    
    for epic in epics:
        tag_str = f" [{epic.tag}]" if epic.tag else " [no tags]"
        click.echo(click.style(f"{epic.name}{tag_str}", fg="blue", bold=True))
        
        epic_tasks = [t for t in tasks if t.epic_id == epic.id]
        for task in epic_tasks:
            if task.status.value == "completed":
                if full:
                    summary_preview = task.summary
                else:
                    summary_preview = task.summary[:60] + "..." if len(task.summary) > 60 else task.summary
                hash_str = f" [{task.git_hash[:7]}]" if task.git_hash else ""
                task_line = f"  - {task.name}{hash_str} (completed): {summary_preview}"
                click.echo(click.style(task_line, fg="green"))
            elif task.status.value == "in-progress":
                task_line = f"  - {task.name} (in-progress)"
                click.echo(click.style(task_line, fg="yellow"))
            else:
                task_line = f"  - {task.name} (todo)"
                click.echo(click.style(task_line, fg="white"))


if __name__ == "__main__":
    cli()
