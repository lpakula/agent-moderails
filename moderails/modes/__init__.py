"""Mode definitions loader."""

from pathlib import Path
from typing import Any, Optional

from jinja2 import Environment, FileSystemLoader, TemplateError

MODES_DIR = Path(__file__).parent

MODE_ORDER = ["start", "research", "brainstorm", "plan", "execute", "complete", "close"]


def get_mode(mode_name: str, context: Optional[dict[str, Any]] = None) -> str:
    """Load and render mode definition from markdown file.
    
    Supports Jinja2 templating for dynamic content injection.
    Templates without Jinja syntax are returned as-is (backward compatible).
    Supports {% include 'partials/filename.md' %} for shared content.
    
    Args:
        mode_name: Name of the mode (e.g., 'execute', 'research')
        context: Optional dict of context variables for template rendering
        
    Returns:
        Rendered mode content
    """
    mode_file = MODES_DIR / f"{mode_name}.md"
    if not mode_file.exists():
        return f"Mode file not found: {mode_name}.md"
    
    template_content = mode_file.read_text()
    
    # Skip templating if no Jinja syntax (backward compatible)
    if "{{" not in template_content and "{%" not in template_content:
        return template_content
    
    # Render with Jinja2 using FileSystemLoader for includes
    try:
        env = Environment(loader=FileSystemLoader(str(MODES_DIR)), autoescape=False)
        template = env.from_string(template_content)
        return template.render(context or {})
    except TemplateError as e:
        # Return original content with error note if template fails
        return f"<!-- Template error: {e} -->\n{template_content}"


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
