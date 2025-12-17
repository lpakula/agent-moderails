"""Mode rules loader."""

from pathlib import Path

RULES_DIR = Path(__file__).parent

MODE_ORDER = ["start", "research", "brainstorm", "plan", "execute", "complete", "close"]


def get_rule(mode_name: str) -> str:
    """Load rule content from markdown file."""
    rule_file = RULES_DIR / f"{mode_name}.md"
    if not rule_file.exists():
        return f"Rule file not found: {mode_name}.md"
    return rule_file.read_text()


def get_full_protocol() -> str:
    """Load all mode rules concatenated."""
    parts = []
    for mode in MODE_ORDER:
        rule_file = RULES_DIR / f"{mode}.md"
        if rule_file.exists():
            parts.append(rule_file.read_text())
    return "\n\n---\n\n".join(parts)


def get_task_template() -> str:
    """Load task template."""
    template_file = RULES_DIR.parent / "templates" / "task-template.md"
    return template_file.read_text()
