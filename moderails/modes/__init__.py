"""Mode definitions loader."""

from pathlib import Path

MODES_DIR = Path(__file__).parent

MODE_ORDER = ["start", "research", "brainstorm", "plan", "execute", "complete", "close"]


def get_mode(mode_name: str) -> str:
    """Load mode definition from markdown file."""
    mode_file = MODES_DIR / f"{mode_name}.md"
    if not mode_file.exists():
        return f"Mode file not found: {mode_name}.md"
    return mode_file.read_text()


def get_full_protocol() -> str:
    """Load all mode definitions concatenated."""
    parts = []
    for mode in MODE_ORDER:
        mode_file = MODES_DIR / f"{mode}.md"
        if mode_file.exists():
            parts.append(mode_file.read_text())
    return "\n\n---\n\n".join(parts)


def get_task_template() -> str:
    """Load task template."""
    template_file = MODES_DIR.parent / "templates" / "task-template.md"
    return template_file.read_text()
