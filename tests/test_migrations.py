"""Tests for database migration utilities."""

import pytest
from pathlib import Path
from sqlalchemy import create_engine, text

from moderails.db.database import init_db
from moderails.db.migrations import (
    get_schema_version,
    set_schema_version,
    needs_migration,
    run_migration,
    run_migrations,
    auto_migrate,
    CURRENT_VERSION,
)


class TestMigrations:
    """Test migration utilities."""
    
    def test_get_schema_version_no_db(self, temp_dir):
        """Test getting version from non-existent database."""
        db_path = temp_dir / "nonexistent.db"
        version = get_schema_version(db_path)
        assert version == 0
    
    def test_set_and_get_schema_version(self, temp_dir):
        """Test setting and getting schema version."""
        db_path = temp_dir / "test.db"
        
        # Create empty database
        engine = create_engine(f"sqlite:///{db_path}")
        engine.dispose()
        
        # Set version
        set_schema_version(db_path, 5)
        
        # Get version
        version = get_schema_version(db_path)
        assert version == 5
    
    def test_needs_migration_fresh_db(self, temp_dir):
        """Test that non-existent database doesn't need migration."""
        db_path = temp_dir / "test.db"
        assert needs_migration(db_path) is False
    
    def test_needs_migration_old_version(self, temp_dir):
        """Test that old version needs migration."""
        db_path = temp_dir / "test.db"
        
        # Create database with old version
        engine = create_engine(f"sqlite:///{db_path}")
        engine.dispose()
        set_schema_version(db_path, CURRENT_VERSION - 1 if CURRENT_VERSION > 1 else 0)
        
        # Should need migration
        assert needs_migration(db_path) is True
    
    def test_run_migration(self, temp_dir):
        """Test running a specific migration with multiple SQL statements."""
        db_path = temp_dir / "test.db"
        
        # Create empty database
        engine = create_engine(f"sqlite:///{db_path}")
        engine.dispose()
        
        # Run first migration (contains multiple CREATE TABLE statements)
        run_migration(db_path, 1)
        
        # Verify both tables were created (tests multiple statements work)
        engine = create_engine(f"sqlite:///{db_path}")
        with engine.connect() as conn:
            # Check epics table
            result = conn.execute(text(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='epics'"
            ))
            assert result.fetchone() is not None
            
            # Check tasks table
            result = conn.execute(text(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='tasks'"
            ))
            assert result.fetchone() is not None
        engine.dispose()
    
    def test_run_migrations_sequential(self, temp_dir):
        """Test that migrations run sequentially."""
        db_path = temp_dir / "test.db"
        
        # Create empty database
        engine = create_engine(f"sqlite:///{db_path}")
        engine.dispose()
        
        # Set to version 0
        set_schema_version(db_path, 0)
        
        # Run all migrations
        run_migrations(db_path)
        
        # Verify current version
        version = get_schema_version(db_path)
        assert version == CURRENT_VERSION
    
    def test_auto_migrate(self, temp_dir):
        """Test automatic migration."""
        db_path = temp_dir / "test.db"
        
        # Create empty database with old version
        engine = create_engine(f"sqlite:///{db_path}")
        engine.dispose()
        set_schema_version(db_path, 0)
        
        # Auto-migrate
        migrated = auto_migrate(db_path)
        assert migrated is True
        
        # Verify version updated
        version = get_schema_version(db_path)
        assert version == CURRENT_VERSION
        
        # Running again should not migrate
        migrated = auto_migrate(db_path)
        assert migrated is False
    
    def test_init_db_sets_version(self, temp_dir):
        """Test that init_db sets correct schema version."""
        import os
        os.chdir(temp_dir)
        
        db_path = init_db()
        
        # Verify version was set
        version = get_schema_version(db_path)
        assert version == CURRENT_VERSION
    
    def test_migration_with_multiple_statements(self, temp_dir):
        """Test that migrations with multiple statements separated by semicolons work."""
        db_path = temp_dir / "test.db"
        
        # Create empty database
        engine = create_engine(f"sqlite:///{db_path}")
        engine.dispose()
        
        # Run first migration (has 2 CREATE TABLE statements)
        run_migration(db_path, 1)
        
        # Verify both tables exist and have correct structure
        engine = create_engine(f"sqlite:///{db_path}")
        with engine.connect() as conn:
            # Test epics table structure
            result = conn.execute(text("PRAGMA table_info(epics)"))
            columns = {row[1] for row in result.fetchall()}
            assert 'id' in columns
            assert 'name' in columns
            
            # Test tasks table structure
            result = conn.execute(text("PRAGMA table_info(tasks)"))
            columns = {row[1] for row in result.fetchall()}
            assert 'id' in columns
            assert 'name' in columns
            assert 'epic_id' in columns
            
            # Test foreign key relationship
            result = conn.execute(text("PRAGMA foreign_key_list(tasks)"))
            fk = result.fetchone()
            assert fk is not None
            assert fk[2] == 'epics'  # References epics table
        engine.dispose()
