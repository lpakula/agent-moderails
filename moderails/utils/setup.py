"""Setup utilities for moderails initialization."""

from pathlib import Path
from typing import List


def get_template_path(name: str) -> Path:
    """Get path to a template file."""
    return Path(__file__).parent.parent / "templates" / name


def create_command_files() -> List[str]:
    """
    Create command files for Cursor and Claude Code.
    
    Embeds the absolute project path so agents know where to run commands.
    
    Returns:
        List of created file paths
    """
    template_path = get_template_path("moderails.md")
    template_content = template_path.read_text()
    
    # Replace template variable with actual project path
    project_root = str(Path.cwd().resolve())
    content = template_content.replace("{{ project_root }}", project_root)
    
    command_dirs = [
        Path.cwd() / ".cursor" / "commands",
        Path.cwd() / ".claude" / "commands",
    ]
    
    created = []
    for cmd_dir in command_dirs:
        cmd_file = cmd_dir / "moderails.md"
        cmd_dir.mkdir(parents=True, exist_ok=True)
        
        # Check if content changed (or file is new)
        is_new = not cmd_file.exists()
        needs_update = is_new or cmd_file.read_text() != content
        
        if needs_update:
            cmd_file.write_text(content)
            created.append(str(cmd_file))
    
    return created

