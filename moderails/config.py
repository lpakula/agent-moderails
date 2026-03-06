"""Configuration management for moderails.

System-wide config lives in ~/.moderails/config.toml.
Per-project config is discovered via .moderails/ in each repo.
"""

import tomllib
from pathlib import Path
from typing import Any, Optional


SYSTEM_DIR = Path.home() / ".moderails"
SYSTEM_DB = SYSTEM_DIR / "moderails.db"
SYSTEM_CONFIG = SYSTEM_DIR / "config.toml"

PROJECT_DIR = ".moderails"


DEFAULT_CONFIG = {
    "daemon": {
        "poll_interval_seconds": 30,
        "run_timeout_minutes": 30,
    },
    "ui": {
        "port": 4200,
        "host": "localhost",
    },
}


def ensure_system_dir() -> Path:
    """Create ~/.moderails/ if it doesn't exist."""
    SYSTEM_DIR.mkdir(parents=True, exist_ok=True)
    return SYSTEM_DIR


def load_system_config() -> dict[str, Any]:
    """Load global config from ~/.moderails/config.toml, falling back to defaults."""
    if SYSTEM_CONFIG.exists():
        try:
            with open(SYSTEM_CONFIG, "rb") as f:
                user_config = tomllib.load(f)
            merged = DEFAULT_CONFIG.copy()
            for section, values in user_config.items():
                if section in merged and isinstance(merged[section], dict):
                    merged[section] = {**merged[section], **values}
                else:
                    merged[section] = values
            return merged
        except Exception:
            pass
    return DEFAULT_CONFIG.copy()


def save_system_config(config: dict[str, Any]) -> Path:
    """Save global config to ~/.moderails/config.toml."""
    ensure_system_dir()
    lines = []
    for section, values in config.items():
        if isinstance(values, dict):
            lines.append(f"[{section}]")
            for key, val in values.items():
                if isinstance(val, str):
                    lines.append(f'{key} = "{val}"')
                else:
                    lines.append(f"{key} = {val}")
            lines.append("")
    SYSTEM_CONFIG.write_text("\n".join(lines))
    return SYSTEM_CONFIG


def find_project_dir(start_path: Optional[Path] = None) -> Optional[Path]:
    """Find .moderails/ directory by walking up from start_path."""
    if start_path is None:
        start_path = Path.cwd()

    current = start_path.resolve()
    while current != current.parent:
        project_dir = current / PROJECT_DIR
        if project_dir.is_dir():
            return project_dir
        current = current.parent
    return None


def get_repo_root(start_path: Optional[Path] = None) -> Optional[Path]:
    """Get the git repo root for the given path."""
    import subprocess
    cwd = str(start_path or Path.cwd())
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            return Path(result.stdout.strip())
    except Exception:
        pass
    return None
