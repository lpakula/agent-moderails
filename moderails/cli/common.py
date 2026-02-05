"""Shared CLI utilities."""

from pathlib import Path
from typing import Optional

import click

from ..db.database import find_db_path, get_session
from ..services import ContextService, EpicService, SessionService, TaskService
from ..services.history import HistoryService


def get_moderails_dir(db_path: Optional[Path] = None) -> Path:
    """Get the moderails directory path."""
    if db_path:
        return db_path.parent
    found = find_db_path()
    return found.parent if found else Path.cwd() / "moderails"


def get_services(db_path: Optional[Path] = None) -> dict:
    """Get all services. Raises FileNotFoundError if database doesn't exist."""
    session = get_session(db_path)
    moderails_dir = get_moderails_dir(db_path)
    history_file = moderails_dir / "history.jsonl"
    return {
        "task": TaskService(session, moderails_dir),
        "epic": EpicService(session, moderails_dir),
        "history": HistoryService(session, history_file),
        "context": ContextService(moderails_dir),
        "session": SessionService(session, moderails_dir),
    }


def get_services_or_exit(ctx) -> dict:
    """Get services or exit with helpful message if database doesn't exist."""
    try:
        return get_services(ctx.obj.get("db_path"))
    except FileNotFoundError:
        click.echo("❌ No moderails database found. Run `moderails init` first.")
        ctx.exit(0)


def check_and_migrate() -> bool:
    """Check and run database migrations if needed.
    
    Returns:
        True if migrations were run, False otherwise
    """
    try:
        from ..db.database import find_db_path
        from ..db.migrations import auto_migrate
        
        db_path = find_db_path()
        if db_path:
            migrated = auto_migrate(db_path)
            if migrated:
                click.echo("✓ Database migrated to latest schema")
                return True
        return False
    except Exception:
        return False
