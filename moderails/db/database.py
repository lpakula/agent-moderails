"""Database connection and auto-discovery."""

import os
from pathlib import Path
from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from .models import Base

# Module-level engine and session factory
_engine = None
_SessionLocal = None


def find_db_path(start_path: Optional[Path] = None) -> Optional[Path]:
    """
    Find moderails/moderails.db by walking up from start_path.
    
    Args:
        start_path: Starting directory (defaults to cwd)
        
    Returns:
        Path to moderails.db if found, None otherwise
    """
    if start_path is None:
        start_path = Path.cwd()
    
    current = start_path.resolve()
    
    # Walk up the directory tree
    while current != current.parent:
        db_path = current / "moderails" / "moderails.db"
        if db_path.exists():
            return db_path
        current = current.parent
    
    # Check root
    db_path = current / "moderails" / "moderails.db"
    if db_path.exists():
        return db_path
    
    return None


def init_db(db_path: Optional[Path] = None) -> Path:
    """
    Initialize a new database at the specified path.
    
    Args:
        db_path: Path to database file (defaults to moderails/moderails.db in cwd)
        
    Returns:
        Path to the created database
    """
    if db_path is None:
        db_path = Path.cwd() / "moderails" / "moderails.db"
    
    # Create directory if needed
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create engine and tables
    engine = create_engine(f"sqlite:///{db_path}", echo=False)
    Base.metadata.create_all(engine)
    
    # Create .gitignore in moderails directory
    gitignore_path = db_path.parent / ".gitignore"
    gitignore_content = """# moderails database
*.db
*.db-journal

# Task files (not committed)
tasks/
"""
    gitignore_path.write_text(gitignore_content)
    
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
