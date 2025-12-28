"""Setup utilities for moderails initialization."""

from pathlib import Path
from typing import List


def get_template_path(name: str) -> Path:
    """Get path to a template file."""
    return Path(__file__).parent.parent / "templates" / name


def create_command_files() -> List[str]:
    """
    Create command files for Cursor and Claude Code.
    
    Returns:
        List of created file paths
    """
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

