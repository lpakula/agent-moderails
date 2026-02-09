"""CLI for moderails - structured agent workflow with persistent memory."""

import click

from .. import __version__
from ..utils import create_command_files
from .admin import register_admin_commands
from .common import check_and_migrate, get_services
from .context import context
from .epic import epic
from .task import task


@click.group()
@click.version_option(version=__version__, prog_name="moderails", message="%(prog)s version %(version)s")
@click.pass_context
def cli(ctx):
    """moderails - structured agent workflow with persistent memory."""
    ctx.ensure_object(dict)
    ctx.obj["db_path"] = None
    
    # Run migrations first (before any ORM access), then sync history and command files
    try:
        check_and_migrate()
        services = get_services(ctx.obj.get("db_path"))
        
        # Sync history
        imported = services["history"].sync_from_file()
        if imported > 0:
            click.echo(f"✓ Synced {imported} tasks from history.jsonl", err=True)
        
        # Update command files if content changed (e.g., after version upgrade)
        updated = create_command_files()
        if updated:
            click.echo(f"✓ Updated command files", err=True)
    except FileNotFoundError:
        pass  # DB doesn't exist yet, skip


# Register command groups
cli.add_command(task)
cli.add_command(epic)
cli.add_command(context)

# Register admin commands (init, migrate, start, mode, list, sync)
register_admin_commands(cli)
