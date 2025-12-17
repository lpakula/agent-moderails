"""Context service - file-based context management."""

from pathlib import Path


class ContextService:
    """Load context from moderails/context/ files.
    
    - Root .md files are mandatory (always loaded)
    - Subfolder .md files are loaded by tag name
    """
    
    def __init__(self, moderails_dir: Path):
        self.context_dir = moderails_dir / "context"
    
    def load_for_tags(self, tags: list[str]) -> str:
        """Load combined context content.
        
        1. Always loads .md files from root (mandatory)
        2. Loads .md files from tag subfolders
        """
        if not self.context_dir.exists():
            return ""
        
        parts = []
        
        # Load mandatory context (root .md files)
        for md_file in sorted(self.context_dir.glob("*.md")):
            if md_file.is_file():
                content = md_file.read_text()
                if content.strip():
                    parts.append(f"<!-- Context: {md_file.name} (mandatory) -->\n{content}")
        
        # Load tag-specific context
        if tags:
            for tag in tags:
                tag_dir = self.context_dir / tag
                if tag_dir.is_dir():
                    for md_file in sorted(tag_dir.glob("*.md")):
                        content = md_file.read_text()
                        if content.strip():
                            parts.append(f"<!-- Context: {tag}/{md_file.name} -->\n{content}")
        
        return "\n\n---\n\n".join(parts)
