"""Admin CLI commands (init, migrate, start, mode, list, sync)."""

import json
from pathlib import Path
from typing import Optional

import click

from ..db.database import init_db
from ..db.models import TaskStatus
from ..modes import get_mode
from ..utils import create_command_files, format_task_line
from ..utils.context import build_mode_context, build_rerail_context, get_project_root
from .common import check_and_migrate, get_services, get_services_or_exit


def register_admin_commands(cli):
    """Register admin commands with the CLI group."""
    
    @cli.command()
    @click.option("--private", is_flag=True, help="Private mode: ignore all moderails files (don't commit to version control)")
    @click.pass_context
    def init(ctx, private: bool):
        """Initialize moderails in current directory."""
        try:
            db_path = init_db(private=private)
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
                if private:
                    click.echo(click.style("  🔒 Private mode: all _moderails files are gitignored", fg="yellow"))
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

    @cli.command()
    @click.pass_context
    def migrate(ctx):
        """Run database migrations to latest schema version."""
        from ..db.database import find_db_path
        from ..db.migrations import get_schema_version, CURRENT_VERSION
        
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

    @cli.command()
    @click.option("--rerail", is_flag=True, help="Instant resume: load session context without workflow prompts")
    @click.pass_context
    def start(ctx, rerail: bool):
        """Show protocol overview and current status with agent guidance."""
        # Auto-migrate database if needed (before showing status)
        if check_and_migrate():
            click.echo()  # Add blank line after migration message
        
        # Build context for start mode (includes current task and epics)
        try:
            services = get_services(ctx.obj.get("db_path"))
            mode_context = build_mode_context(services, "start")
        except FileNotFoundError:
            click.echo("No moderails database found. Run `moderails init` first.")
            return
        
        # Ensure session exists for in-progress task (edge case handling)
        if mode_context.get("current_task"):
            task_id = mode_context["current_task"]["id"]
            services["session"].ensure_active(task_id)
        
        # --rerail: instant resume with session context (no workflow prompts)
        if rerail:
            if mode_context.get("current_task"):
                task = services["task"].get(mode_context["current_task"]["id"])
                project_root = get_project_root()
                click.echo(build_rerail_context(services, task, project_root))
                return
            else:
                # No in-progress task, fall through to normal start
                click.echo("No in-progress task. Showing full start mode.\n")
        
        # Print protocol overview with dynamic context
        click.echo(get_mode("start", mode_context))

    @cli.command("mode", context_settings={"ignore_unknown_options": True, "allow_extra_args": True})
    @click.option("--name", "-n", required=True, help="Mode name")
    @click.pass_context
    def mode(ctx, name: str):
        """Get mode definition with dynamic context. Use when switching modes (e.g., #execute --no-confirmation)."""
        valid_modes = ["fast", "research", "brainstorm", "plan", "execute", "complete", "abort"]
        if name not in valid_modes:
            click.echo(f"❌ Invalid mode. Valid modes: {', '.join(valid_modes)}")
            return
        
        # Parse unknown options as flags (e.g., --no-confirmation → no-confirmation)
        flags = []
        for arg in ctx.args:
            if arg.startswith("--"):
                flags.append(arg[2:])  # Strip leading --
        
        # Build dynamic context for template rendering
        try:
            services = get_services(ctx.obj.get("db_path"))
            mode_context = build_mode_context(services, name, flags=flags)
            
            # Update session mode
            services["session"].set_mode(name)
        except FileNotFoundError:
            # No database - render without context (but still pass flags)
            mode_context = {"flags": flags}
        
        click.echo(get_mode(name, mode_context))

    @cli.command("list")
    @click.option("--status", "-s", type=click.Choice(["draft", "in-progress", "completed"]), help="Filter by status")
    @click.option("--epic-name", "-e", help="Filter by epic name")
    @click.pass_context
    def list_tasks(ctx, status: Optional[str], epic_name: Optional[str]):
        """List all tasks (active first, completed at bottom)."""
        services = get_services_or_exit(ctx)
        
        # Get all tasks
        status_enum = TaskStatus(status) if status else None
        tasks = services["task"].list_all(epic_name=epic_name, status=status_enum)
        
        if not tasks:
            click.echo("No tasks found.")
            return
        
        # Sort: completed first (top), then draft, then in-progress last (bottom, visible without scrolling)
        def _list_sort_key(x):
            ts = x.completed_at if (x.status == TaskStatus.COMPLETED and x.completed_at) else x.created_at
            rank = (0 if x.status == TaskStatus.COMPLETED else 1 if x.status == TaskStatus.DRAFT else 2)
            return (rank, -ts.timestamp())
        sorted_tasks = sorted(tasks, key=_list_sort_key)
        
        # Display: task_id [type] [status] [epic] [timestamp] - task name
        for task in sorted_tasks:
            click.echo(format_task_line(task))

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
