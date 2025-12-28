"""Search utilities for context files."""

import subprocess
from pathlib import Path
from typing import List, Tuple, Optional


def search_context_files(query: str, search_dir: Path) -> Optional[str]:
    """
    Search markdown files in the search directory for the given query.
    
    Args:
        query: Search term
        search_dir: Directory to search in
    
    Returns:
        Formatted search results or None if no matches
    """
    if not search_dir.exists():
        return None
    
    try:
        # Try using grep for better performance
        result = subprocess.run(
            ["grep", "-r", "-i", "-n", "-C", "2", query, str(search_dir)],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            return result.stdout
        elif result.returncode == 1:
            return None  # No matches
        else:
            # Error occurred, fall through to Python search
            pass
    except FileNotFoundError:
        pass  # grep not available, use Python search
    
    # Fallback to Python search
    matches: List[Tuple[Path, int, str]] = []
    for md_file in search_dir.rglob("*.md"):
        try:
            content = md_file.read_text()
            lines = content.split('\n')
            for i, line in enumerate(lines, 1):
                if query.lower() in line.lower():
                    matches.append((md_file, i, line))
        except Exception:
            pass
    
    if matches:
        # Format matches similar to grep output
        result_lines = []
        for file_path, line_num, line in matches:
            result_lines.append(f"{file_path}:{line_num}: {line.strip()}")
        return "\n".join(result_lines)
    
    return None

