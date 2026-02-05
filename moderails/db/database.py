"""Database connection and auto-discovery."""

from pathlib import Path
from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from ..config import find_config_path, get_db_path as config_get_db_path, get_default_config, save_config
from ..templates import get_template_path

# Module-level engine and session factory
_engine = None
_SessionLocal = None


def find_db_path(start_path: Optional[Path] = None) -> Optional[Path]:
    """
    Find moderails.db by using config.json to determine the path.
    
    Args:
        start_path: Starting directory (defaults to cwd)
        
    Returns:
        Path to moderails.db if found, None otherwise
    """
    config_path = find_config_path(start_path)
    if config_path:
        db_path = config_get_db_path(config_path)
        if db_path.exists():
            return db_path
    
    return None


def init_db(private: bool = False) -> Path:
    """
    Initialize a new database and configuration in _moderails directory.
    
    Args:
        private: If True, all moderails files are gitignored and not committed.
    
    Returns:
        Path to the created database
    """
    # Create config with private setting
    config = get_default_config(private=private)
    config_path = save_config(config)
    
    # Get db path from config
    db_path = config_get_db_path(config_path)
    
    # Create directory if needed
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Initialize database schema with migrations
    from .migrations import init_schema
    init_schema(db_path)
    
    # Create .gitignore in moderails directory (always use standard template)
    gitignore_path = db_path.parent / ".gitignore"
    gitignore_template = get_template_path("gitignore.txt")
    gitignore_content = gitignore_template.read_text()
    gitignore_path.write_text(gitignore_content)
    
    # In private mode, add pattern to project's root .gitignore
    if private:
        project_root = Path.cwd()
        root_gitignore = project_root / ".gitignore"
        
        private_pattern = "*moderails*"
        
        # Read existing content or start fresh
        existing_content = ""
        if root_gitignore.exists():
            existing_content = root_gitignore.read_text()
        
        # Add pattern if it doesn't already exist
        if private_pattern not in existing_content:
            new_content = existing_content.rstrip()
            if new_content and not new_content.endswith("\n"):
                new_content += "\n"
            if new_content:
                new_content += "\n"
            new_content += "# moderails (private mode)\n"
            new_content += f"{private_pattern}\n"
            root_gitignore.write_text(new_content)
    
    # Create context directories
    context_dir = db_path.parent / "context"
    context_dir.mkdir(exist_ok=True)
    
    mandatory_dir = context_dir / "mandatory"
    mandatory_dir.mkdir(exist_ok=True)
    
    memories_dir = context_dir / "memories"
    memories_dir.mkdir(exist_ok=True)
    
    # Create README in context directory
    context_readme = context_dir / "README.md"
    if not context_readme.exists():
        readme_template = get_template_path("context-readme.md")
        context_readme_content = readme_template.read_text()
        context_readme.write_text(context_readme_content)
    
    # Create empty history.jsonl file
    history_file = db_path.parent / "history.jsonl"
    if not history_file.exists():
        history_file.touch()
    
    return db_path


def get_engine(db_path: Optional[Path] = None):
    """
    Get or create database engine.
    
    Args:
        db_path: Explicit path to database (auto-discovers if None)
        
    Returns:
        SQLAlchemy engine
        
    Raises:
        FileNotFoundError: If no database found and db_path not specified
    """
    global _engine
    
    if _engine is not None:
        return _engine
    
    if db_path is None:
        db_path = find_db_path()
        if db_path is None:
            raise FileNotFoundError(
                "No moderails database found. Run 'moderails init' to create one."
            )
    
    _engine = create_engine(f"sqlite:///{db_path}", echo=False)
    return _engine


def get_session(db_path: Optional[Path] = None) -> Session:
    """
    Get a new database session.
    
    Args:
        db_path: Explicit path to database (auto-discovers if None)
        
    Returns:
        SQLAlchemy session
    """
    global _SessionLocal
    
    engine = get_engine(db_path)
    
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=engine)
    
    return _SessionLocal()


def get_db(db_path: Optional[Path] = None):
    """
    Context manager for database sessions.
    
    Usage:
        with get_db() as db:
            db.query(Epic).all()
    """
    session = get_session(db_path)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def reset_engine():
    """Reset the global engine (for testing)."""
    global _engine, _SessionLocal
    _engine = None
    _SessionLocal = None
