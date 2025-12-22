"""Tests for config module."""

import json
import pytest
from pathlib import Path

from moderails.config import (
    validate_base_dir,
    find_config_path,
    load_config,
    save_config,
    get_moderails_dir,
    get_db_path,
    DEFAULT_BASE_DIR,
)


class TestValidateBaseDir:
    """Tests for validate_base_dir function."""
    
    def test_valid_base_dir(self):
        """Test that valid base directory names pass validation."""
        validate_base_dir("agent")
        validate_base_dir("ai")
        validate_base_dir("tools")
        validate_base_dir("dev")
        # Should not raise
    
    def test_empty_base_dir(self):
        """Test that empty base directory raises ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_base_dir("")
    
    def test_dot_prefix_base_dir(self):
        """Test that dot-prefixed base directory raises ValueError."""
        with pytest.raises(ValueError, match="protected by editors/agents"):
            validate_base_dir(".ai")
        
        with pytest.raises(ValueError, match="protected by editors/agents"):
            validate_base_dir(".tools")
    
    def test_path_separator_in_base_dir(self):
        """Test that path separators in base directory raise ValueError."""
        with pytest.raises(ValueError, match="path separators"):
            validate_base_dir("agent/sub")
        
        with pytest.raises(ValueError, match="path separators"):
            validate_base_dir("agent\\sub")


class TestFindConfigPath:
    """Tests for find_config_path function."""
    
    def test_find_config_in_subdirectory(self, temp_dir):
        """Test finding config.json in subdirectory."""
        # Create config file
        config_dir = temp_dir / "agent" / "moderails"
        config_dir.mkdir(parents=True)
        config_file = config_dir / "config.json"
        config_file.write_text('{"base_dir": "agent"}')
        
        # Search from temp_dir
        found = find_config_path(temp_dir)
        assert found == config_file
    
    def test_no_config_found(self, temp_dir):
        """Test when no config.json exists."""
        found = find_config_path(temp_dir)
        assert found is None


class TestLoadConfig:
    """Tests for load_config function."""
    
    def test_load_existing_config(self, temp_dir):
        """Test loading an existing config file."""
        config_dir = temp_dir / "agent" / "moderails"
        config_dir.mkdir(parents=True)
        config_file = config_dir / "config.json"
        
        config_data = {"base_dir": "custom", "version": "1.0"}
        config_file.write_text(json.dumps(config_data))
        
        loaded = load_config(config_file)
        assert loaded == config_data
    
    def test_load_config_with_missing_base_dir(self, temp_dir):
        """Test loading config that's missing base_dir key."""
        config_dir = temp_dir / "agent" / "moderails"
        config_dir.mkdir(parents=True)
        config_file = config_dir / "config.json"
        
        config_file.write_text('{"version": "1.0"}')
        
        loaded = load_config(config_file)
        assert loaded["base_dir"] == DEFAULT_BASE_DIR
    
    def test_load_config_returns_defaults(self):
        """Test that load_config returns defaults when file not found."""
        loaded = load_config(Path("/nonexistent/config.json"))
        assert loaded["base_dir"] == DEFAULT_BASE_DIR
        assert "version" in loaded


class TestSaveConfig:
    """Tests for save_config function."""
    
    def test_save_config_creates_directory(self, temp_dir, monkeypatch):
        """Test that save_config creates the directory structure."""
        monkeypatch.chdir(temp_dir)
        
        config = {"base_dir": "agent", "version": "1.0"}
        config_path = save_config(config, "agent")
        
        assert config_path.exists()
        assert config_path.parent.name == "moderails"
        assert config_path.parent.parent.name == "agent"
    
    def test_save_config_writes_correct_content(self, temp_dir, monkeypatch):
        """Test that save_config writes the correct JSON content."""
        monkeypatch.chdir(temp_dir)
        
        config = {"base_dir": "tools", "version": "1.0"}
        config_path = save_config(config, "tools")
        
        saved_data = json.loads(config_path.read_text())
        assert saved_data == config
    
    def test_save_config_validates_base_dir(self, temp_dir, monkeypatch):
        """Test that save_config validates base directory."""
        monkeypatch.chdir(temp_dir)
        
        config = {"base_dir": ".ai"}
        with pytest.raises(ValueError):
            save_config(config, ".ai")


class TestGetModerailsDir:
    """Tests for get_moderails_dir function."""
    
    def test_get_moderails_dir_with_existing_config(self, temp_dir):
        """Test getting moderails directory when config exists."""
        config_dir = temp_dir / "custom" / "moderails"
        config_dir.mkdir(parents=True)
        config_file = config_dir / "config.json"
        config_file.write_text('{"base_dir": "custom"}')
        
        result = get_moderails_dir(config_file)
        assert result == config_dir
    
    def test_get_moderails_dir_default(self, temp_dir, monkeypatch):
        """Test getting default moderails directory."""
        monkeypatch.chdir(temp_dir)
        
        result = get_moderails_dir()
        assert result == temp_dir / DEFAULT_BASE_DIR / "moderails"


class TestGetDbPath:
    """Tests for get_db_path function."""
    
    def test_get_db_path(self, temp_dir):
        """Test getting database path."""
        config_dir = temp_dir / "agent" / "moderails"
        config_dir.mkdir(parents=True)
        config_file = config_dir / "config.json"
        config_file.write_text('{"base_dir": "agent"}')
        
        db_path = get_db_path(config_file)
        assert db_path == config_dir / "moderails.db"

