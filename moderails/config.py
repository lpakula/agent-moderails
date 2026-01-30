"""Configuration management for moderails."""

import json
from pathlib import Path
from typing import Optional

from . import __version__


MODERAILS_DIR = ".moderails"
CONFIG_FILENAME = "config.json"


def get_default_config(private: bool = False) -> dict:
    """Return default config with current version."""
    return {"version": __version__, "private": private}


def find_config_path(start_path: Optional[Path] = None) -> Optional[Path]:
    """
    Find config.json by walking up from start_path.
    
    Args:
        start_path: Starting directory (defaults to cwd)
        
    Returns:
        Path to config.json if found, None otherwise
    """
    if start_path is None:
        start_path = Path.cwd()
    
    current = start_path.resolve()
    
    # Walk up the directory tree
    while current != current.parent:
        # Check for config in .moderails/config.json
        config_path = current / MODERAILS_DIR / CONFIG_FILENAME
        if config_path.exists():
            return config_path
        current = current.parent
    
    return None


def load_config(config_path: Optional[Path] = None) -> dict:
    """
    Load configuration from config.json.
    
    Args:
        config_path: Explicit path to config.json (auto-discovers if None)
        
    Returns:
        Configuration dictionary with defaults if not found
    """
    if config_path is None:
        config_path = find_config_path()
    
    if config_path and config_path.exists():
        try:
            with open(config_path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    
    # Return defaults
    return get_default_config()


def save_config(config: dict) -> Path:
    """
    Save configuration to config.json in .moderails directory.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Path to the saved config file
    """
    moderails_dir = Path.cwd() / MODERAILS_DIR
    moderails_dir.mkdir(parents=True, exist_ok=True)
    
    config_path = moderails_dir / CONFIG_FILENAME
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)
    
    return config_path


def get_moderails_dir(config_path: Optional[Path] = None) -> Path:
    """
    Get the .moderails directory path.
    
    Args:
        config_path: Explicit path to config.json (auto-discovers if None)
        
    Returns:
        Path to .moderails directory
    """
    # If config exists, use its parent directory
    if config_path is None:
        config_path = find_config_path()
    
    if config_path and config_path.exists():
        return config_path.parent
    
    # Otherwise, use current directory
    return Path.cwd() / MODERAILS_DIR


def get_db_path(config_path: Optional[Path] = None) -> Path:
    """
    Get the database path based on configuration.
    
    Args:
        config_path: Explicit path to config.json (auto-discovers if None)
        
    Returns:
        Path to moderails.db
    """
    moderails_dir = get_moderails_dir(config_path)
    return moderails_dir / "moderails.db"


def is_private_mode(config_path: Optional[Path] = None) -> bool:
    """
    Check if moderails is running in private mode.
    
    In private mode, all .moderails files are gitignored and
    history.jsonl is not committed.
    
    Args:
        config_path: Explicit path to config.json (auto-discovers if None)
        
    Returns:
        True if private mode is enabled
    """
    config = load_config(config_path)
    return config.get("private", False)

