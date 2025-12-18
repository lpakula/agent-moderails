"""Configuration management for moderails."""

import json
from pathlib import Path
from typing import Optional


DEFAULT_BASE_DIR = "agent"
CONFIG_FILENAME = "config.json"
MODERAILS_SUBDIR = "moderails"


def validate_base_dir(base_dir: str) -> None:
    """
    Validate base directory name.
    
    Args:
        base_dir: Base directory name to validate
        
    Raises:
        ValueError: If base_dir is invalid
    """
    if not base_dir:
        raise ValueError("Base directory cannot be empty")
    
    if base_dir.startswith("."):
        raise ValueError(
            "Base directory cannot start with a dot (.) - "
            "dot-prefixed directories are protected by editors/agents"
        )
    
    if "/" in base_dir or "\\" in base_dir:
        raise ValueError("Base directory cannot contain path separators")


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
        # Check for config in base_dir/moderails/config.json
        for subdir in current.iterdir():
            if subdir.is_dir():
                config_path = subdir / MODERAILS_SUBDIR / CONFIG_FILENAME
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
                config = json.load(f)
                # Ensure base_dir is set
                if "base_dir" not in config:
                    config["base_dir"] = DEFAULT_BASE_DIR
                return config
        except (json.JSONDecodeError, IOError):
            pass
    
    # Return defaults
    return {
        "base_dir": DEFAULT_BASE_DIR,
        "version": "1.0"
    }


def save_config(config: dict, base_dir: str) -> Path:
    """
    Save configuration to config.json.
    
    Args:
        config: Configuration dictionary
        base_dir: Base directory name (e.g., "agent", "tools")
        
    Returns:
        Path to the saved config file
        
    Raises:
        ValueError: If base_dir is invalid
    """
    validate_base_dir(base_dir)
    
    moderails_dir = Path.cwd() / base_dir / MODERAILS_SUBDIR
    moderails_dir.mkdir(parents=True, exist_ok=True)
    
    config_path = moderails_dir / CONFIG_FILENAME
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)
    
    return config_path


def get_moderails_dir(config_path: Optional[Path] = None) -> Path:
    """
    Get the moderails directory path based on configuration.
    
    Args:
        config_path: Explicit path to config.json (auto-discovers if None)
        
    Returns:
        Path to moderails directory
    """
    config = load_config(config_path)
    base_dir = config.get("base_dir", DEFAULT_BASE_DIR)
    
    # If config exists, use its parent directory
    if config_path is None:
        config_path = find_config_path()
    
    if config_path and config_path.exists():
        return config_path.parent
    
    # Otherwise, construct from current directory and config
    return Path.cwd() / base_dir / MODERAILS_SUBDIR


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

