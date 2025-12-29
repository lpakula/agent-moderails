"""Simple SQL-based database migrations."""

from pathlib import Path
from sqlalchemy import create_engine, text

# Migration scripts - each key is a version number
MIGRATIONS = {
    1: """
        -- Create epics table
        CREATE TABLE IF NOT EXISTS epics (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL UNIQUE
        );
        
        -- Create tasks table
        CREATE TABLE IF NOT EXISTS tasks (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            file_name TEXT NOT NULL,
            summary TEXT,
            type TEXT,
            status TEXT,
            git_hash TEXT,
            completed_at DATETIME,
            epic_id TEXT,
            created_at DATETIME,
            FOREIGN KEY (epic_id) REFERENCES epics(id)
        );
    """,
    # Future migrations go here:
    # 2: "ALTER TABLE tasks ADD COLUMN priority TEXT;",
    # 3: "ALTER TABLE tasks ADD COLUMN deadline DATETIME;",
}

CURRENT_VERSION = max(MIGRATIONS.keys())


def get_schema_version(db_path: Path) -> int:
    """Get current schema version from database.
    
    Returns:
        Schema version number, or 0 if not set
    """
    engine = create_engine(f"sqlite:///{db_path}")
    
    try:
        with engine.connect() as conn:
            # Check if schema_version table exists
            result = conn.execute(text(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_version'"
            ))
            
            if not result.fetchone():
                return 0
            
            # Get version
            result = conn.execute(text("SELECT version FROM schema_version LIMIT 1"))
            row = result.fetchone()
            return row[0] if row else 0
    except Exception:
        return 0
    finally:
        engine.dispose()


def set_schema_version(db_path: Path, version: int) -> None:
    """Set schema version in database."""
    engine = create_engine(f"sqlite:///{db_path}")
    
    try:
        with engine.connect() as conn:
            # Create table if needed
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS schema_version (
                    version INTEGER PRIMARY KEY
                )
            """))
            
            # Update or insert version
            conn.execute(text("DELETE FROM schema_version"))
            conn.execute(text(f"INSERT INTO schema_version (version) VALUES ({version})"))
            conn.commit()
    finally:
        engine.dispose()


def needs_migration(db_path: Path) -> bool:
    """Check if database needs migration."""
    if not db_path.exists():
        return False
    
    current = get_schema_version(db_path)
    return current < CURRENT_VERSION


def run_migration(db_path: Path, version: int) -> None:
    """Run a specific migration."""
    if version not in MIGRATIONS:
        raise ValueError(f"Migration version {version} not found")
    
    engine = create_engine(f"sqlite:///{db_path}")
    
    try:
        with engine.connect() as conn:
            # Split migration into separate statements (SQLite limitation)
            migration_sql = MIGRATIONS[version]
            statements = [s.strip() for s in migration_sql.split(';') if s.strip()]
            
            # Execute each statement separately
            for statement in statements:
                conn.execute(text(statement))
            
            conn.commit()
    finally:
        engine.dispose()


def run_migrations(db_path: Path) -> None:
    """Run all pending migrations sequentially."""
    current_version = get_schema_version(db_path)
    
    # Run migrations from current+1 to latest
    for version in range(current_version + 1, CURRENT_VERSION + 1):
        run_migration(db_path, version)
        set_schema_version(db_path, version)


def auto_migrate(db_path: Path) -> bool:
    """Automatically migrate database if needed.
    
    Returns:
        True if migration was performed
    """
    if not needs_migration(db_path):
        return False
    
    run_migrations(db_path)
    return True


def init_schema(db_path: Path) -> None:
    """Initialize a fresh database with current schema."""
    # Run all migrations sequentially
    for version in range(1, CURRENT_VERSION + 1):
        run_migration(db_path, version)
    
    # Set to current version
    set_schema_version(db_path, CURRENT_VERSION)
