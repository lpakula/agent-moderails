"""Tests for config module."""

import json
from pathlib import Path

from moderails.config import (
    find_config_path,
    load_config,
    save_config,
    get_db_path,
)


class TestFindConfigPath:
    """Tests for find_config_path function."""
    
    def test_find_config_in_subdirectory(self, temp_dir):
        """Test finding config.json in _moderails directory."""
        # Create config file
        config_dir = temp_dir / "_moderails"
        config_dir.mkdir(parents=True)
        config_file = config_dir / "config.json"
        config_file.write_text('{"version": "1.0"}')
        
        # Search from temp_dir
        found = find_config_path(temp_dir)
        assert found.resolve() == config_file.resolve()
    
    def test_no_config_found(self, temp_dir):
        """Test when no config.json exists."""
        found = find_config_path(temp_dir)
        assert found is None


class TestLoadConfig:
    """Tests for load_config function."""
    
    def test_load_existing_config(self, temp_dir):
        """Test loading an existing config file."""
        config_dir = temp_dir / "_moderails"
        config_dir.mkdir(parents=True)
        config_file = config_dir / "config.json"
        
        config_data = {"version": "1.0"}
        config_file.write_text(json.dumps(config_data))
        
        loaded = load_config(config_file)
        assert loaded == config_data
    
    def test_load_config_returns_defaults(self):
        """Test that load_config returns defaults when file not found."""
        loaded = load_config(Path("/nonexistent/config.json"))
        assert "version" in loaded


class TestSaveConfig:
    """Tests for save_config function."""
    
    def test_save_config_creates_directory(self, temp_dir, monkeypatch):
        """Test that save_config creates the _moderails directory."""
        monkeypatch.chdir(temp_dir)
        
        config = {"version": "1.0"}
        config_path = save_config(config)
        
        assert config_path.exists()
        assert config_path.parent.name == "_moderails"
    
    def test_save_config_writes_correct_content(self, temp_dir, monkeypatch):
        """Test that save_config writes the correct JSON content."""
        monkeypatch.chdir(temp_dir)
        
        config = {"version": "1.0"}
        config_path = save_config(config)
        
        saved_data = json.loads(config_path.read_text())
        assert saved_data == config


class TestGetDbPath:
    """Tests for get_db_path function."""
    
    def test_get_db_path(self, temp_dir):
        """Test getting database path."""
        config_dir = temp_dir / "_moderails"
        config_dir.mkdir(parents=True)
        config_file = config_dir / "config.json"
        config_file.write_text('{"version": "1.0"}')
        
        db_path = get_db_path(config_file)
        assert db_path == config_dir / "moderails.db"

