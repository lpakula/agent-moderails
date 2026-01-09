"""Context service - manages context loading and discovery."""

import json
from pathlib import Path
from typing import Optional


class ContextService:
    def __init__(self, moderails_dir: Path):
        self.moderails_dir = moderails_dir
        self.context_dir = moderails_dir / "context"
        self.mandatory_dir = self.context_dir / "mandatory"
        self.memories_dir = self.context_dir / "memories"
        self.history_file = moderails_dir / "history.jsonl"
    
    def load_mandatory_context(self) -> Optional[str]:
        """Load all files from mandatory context directory.
        
        Returns:
            Concatenated content of all mandatory context files, or None if directory doesn't exist
        """
        if not self.mandatory_dir.exists():
            return None
        
        # Get all markdown files in mandatory directory
        context_files = sorted(self.mandatory_dir.glob("*.md"))
        
        if not context_files:
            return None
        
        # Build context output
        context_parts = ["## MANDATORY CONTEXT\n"]
        
        for i, file_path in enumerate(context_files):
            try:
                content = file_path.read_text()
                context_parts.append(f"### {file_path.name}\n")
                context_parts.append(content)
                
                # Add separator between files (but not after the last one)
                if i < len(context_files) - 1:
                    context_parts.append("\n---\n")
                else:
                    context_parts.append("\n")
            except Exception:
                # Skip files that can't be read
                continue
        
        return "\n".join(context_parts) if len(context_parts) > 1 else None
    
    def list_memories(self) -> list[str]:
        """List available memory names (without .md extension).
        
        Returns:
            List of memory names that can be loaded
        """
        if not self.memories_dir.exists():
            return []
        
        return sorted([
            f.stem for f in self.memories_dir.glob("*.md")
        ])
    
    def load_memories(self, names: list[str]) -> Optional[str]:
        """Load specific memory files by name.
        
        Args:
            names: List of memory names (without .md extension)
        
        Returns:
            Concatenated content of requested memory files, or None if none found
        """
        if not self.memories_dir.exists():
            return None
        
        loaded_parts = []
        not_found = []
        
        for name in names:
            file_path = self.memories_dir / f"{name}.md"
            if file_path.exists():
                try:
                    content = file_path.read_text()
                    loaded_parts.append(f"### MEMORY: {name}\n")
                    loaded_parts.append(content)
                    loaded_parts.append("\n")
                except Exception:
                    not_found.append(name)
            else:
                not_found.append(name)
        
        if not loaded_parts:
            return None
        
        result = "## LOADED MEMORIES\n\n" + "\n---\n".join(
            [part for part in "".join(loaded_parts).split("\n---\n") if part.strip()]
        )
        
        if not_found:
            result += f"\n\n⚠️ Not found: {', '.join(not_found)}"
        
        return result
    
    def get_files_tree(self) -> Optional[str]:
        """Build a file tree from history.jsonl files_changed field.
        
        Returns:
            Formatted file tree showing all files touched by completed tasks
        """
        if not self.history_file.exists():
            return None
        
        # Collect all unique files from history
        files_set: set[str] = set()
        
        with open(self.history_file, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    task_data = json.loads(line)
                    for file_path in task_data.get('files_changed', []):
                        files_set.add(file_path)
                except json.JSONDecodeError:
                    continue
        
        if not files_set:
            return None
        
        # Sort and format as tree
        sorted_files = sorted(files_set)
        
        # Group by directory for nicer output
        tree_lines = []
        current_dir = ""
        for file_path in sorted_files:
            parts = file_path.rsplit("/", 1)
            if len(parts) == 2:
                dir_path, filename = parts
                if dir_path != current_dir:
                    current_dir = dir_path
                    tree_lines.append(f"{dir_path}/")
                tree_lines.append(f"  {filename}")
            else:
                if current_dir != "":
                    current_dir = ""
                    tree_lines.append("./")
                tree_lines.append(f"  {file_path}")
        
        return "\n".join(tree_lines)
    
    def ensure_directories(self) -> None:
        """Ensure context directories exist."""
        self.context_dir.mkdir(exist_ok=True)
        self.mandatory_dir.mkdir(exist_ok=True)
        self.memories_dir.mkdir(exist_ok=True)

