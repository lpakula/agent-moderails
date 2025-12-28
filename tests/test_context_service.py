"""Tests for context service."""

from pathlib import Path

from moderails.services.context import ContextService


class TestContextService:
    """Tests for ContextService."""
    
    def test_load_mandatory_context_empty(self, temp_dir):
        """Test loading mandatory context when directory doesn't exist."""
        service = ContextService(temp_dir)
        
        result = service.load_mandatory_context()
        
        assert result is None
    
    def test_load_mandatory_context_no_files(self, temp_dir):
        """Test loading mandatory context when directory is empty."""
        service = ContextService(temp_dir)
        service.ensure_directories()
        
        result = service.load_mandatory_context()
        
        assert result is None
    
    def test_load_mandatory_context_single_file(self, temp_dir):
        """Test loading mandatory context with single file."""
        service = ContextService(temp_dir)
        service.ensure_directories()
        
        # Create a context file
        context_file = service.mandatory_dir / "conventions.md"
        context_file.write_text("# Conventions\n\nUse TypeScript for all code.")
        
        result = service.load_mandatory_context()
        
        assert result is not None
        assert "## MANDATORY CONTEXT" in result
        assert "### conventions.md" in result
        assert "Use TypeScript for all code" in result
    
    def test_load_mandatory_context_multiple_files(self, temp_dir):
        """Test loading mandatory context with multiple files."""
        service = ContextService(temp_dir)
        service.ensure_directories()
        
        # Create multiple context files
        (service.mandatory_dir / "architecture.md").write_text("# Architecture\n\nUse MVC pattern.")
        (service.mandatory_dir / "style.md").write_text("# Style Guide\n\nUse 2 spaces for indentation.")
        
        result = service.load_mandatory_context()
        
        assert result is not None
        assert "## MANDATORY CONTEXT" in result
        assert "### architecture.md" in result
        assert "### style.md" in result
        assert "Use MVC pattern" in result
        assert "Use 2 spaces" in result
    
    def test_load_mandatory_context_sorted(self, temp_dir):
        """Test that files are loaded in sorted order."""
        service = ContextService(temp_dir)
        service.ensure_directories()
        
        # Create files in non-alphabetical order
        (service.mandatory_dir / "z-last.md").write_text("Last")
        (service.mandatory_dir / "a-first.md").write_text("First")
        (service.mandatory_dir / "m-middle.md").write_text("Middle")
        
        result = service.load_mandatory_context()
        
        # Check order in result
        first_pos = result.index("### a-first.md")
        middle_pos = result.index("### m-middle.md")
        last_pos = result.index("### z-last.md")
        
        assert first_pos < middle_pos < last_pos
    
    def test_ensure_directories(self, temp_dir):
        """Test that ensure_directories creates necessary directories."""
        service = ContextService(temp_dir)
        
        assert not service.context_dir.exists()
        assert not service.mandatory_dir.exists()
        
        service.ensure_directories()
        
        assert service.context_dir.exists()
        assert service.mandatory_dir.exists()

