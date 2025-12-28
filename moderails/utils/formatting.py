"""Formatting utilities for CLI output."""

from typing import Tuple
import click
from ..db.models import Task, TaskStatus


def get_task_colors(status: TaskStatus) -> Tuple[str, str, str, str, str, str]:
    """
    Get colors for task display based on status.
    
    Returns:
        (status_color, task_id_color, type_color, epic_color, timestamp_color, name_color)
    """
    if status == TaskStatus.COMPLETED:
        return ("green", "bright_black", "bright_black", "cyan", "white", "bright_black")
    elif status == TaskStatus.IN_PROGRESS:
        return ("bright_yellow", "white", "green", "cyan", "white", "white")
    else:  # DRAFT
        return ("blue", "white", "green", "cyan", "white", "white")


def format_task_line(task: Task) -> str:
    """
    Format a task as a colored single-line string for display.
    
    Format: task_id [type] [status] [epic] [timestamp] - task name (git_hash)
    """
    status_color, task_id_color, type_color, epic_color, timestamp_color, name_color = get_task_colors(task.status)
    
    line_parts = []
    
    # Task ID
    line_parts.append(click.style(task.id, fg=task_id_color))
    
    # Type in brackets
    line_parts.append(click.style(f"[{task.type.value}]", fg=type_color))
    
    # Status in brackets
    line_parts.append(click.style(f"[{task.status.value}]", fg=status_color))
    
    # Epic (if any) in brackets
    if task.epic:
        line_parts.append(click.style(f"[{task.epic.name}]", fg=epic_color))
    
    # Timestamp
    if task.status == TaskStatus.COMPLETED and task.completed_at:
        timestamp = task.completed_at.strftime("[%Y-%m-%d %H:%M]")
    else:
        timestamp = task.created_at.strftime("[%Y-%m-%d %H:%M]")
    line_parts.append(click.style(timestamp, fg=timestamp_color))
    
    # Dash separator
    line_parts.append("-")
    
    # Task name
    line_parts.append(click.style(task.name, fg=name_color))
    
    # Git hash (if exists)
    if task.git_hash:
        git_hash_short = task.git_hash[:7]
        line_parts.append(click.style(f"({git_hash_short})", fg="yellow"))
    
    return " ".join(line_parts)

