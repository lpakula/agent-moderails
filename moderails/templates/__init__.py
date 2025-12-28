"""Templates for moderails initialization."""

from pathlib import Path


def get_template_path(template_name: str) -> Path:
    """Get the path to a template file."""
    return Path(__file__).parent / template_name

