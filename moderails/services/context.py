"""Context service - manages mandatory context loading."""

from pathlib import Path
from typing import Optional


class ContextService:
    def __init__(self, moderails_dir: Path):
        self.moderails_dir = moderails_dir
        self.context_dir = moderails_dir / "context"
        self.mandatory_dir = self.context_dir / "mandatory"
    
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
    
    def ensure_directories(self) -> None:
        """Ensure context directories exist."""
        self.context_dir.mkdir(exist_ok=True)
        self.mandatory_dir.mkdir(exist_ok=True)

