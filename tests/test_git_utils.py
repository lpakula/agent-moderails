"""Tests for git utilities."""

import subprocess
import pytest
from pathlib import Path

from moderails.utils.git import (
    get_commit_meta,
    get_name_status,
    get_patch_unified,
    format_commit_diff,
    generate_epic_diff,
    generate_epic_files_changed,
)


@pytest.fixture
def git_repo_with_commits(mock_git_repo):
    """Create a git repo with multiple commits."""
    repo_dir = mock_git_repo
    
    # Create second commit - add file
    new_file = repo_dir / "added.py"
    new_file.write_text("def hello(): pass")
    subprocess.run(["git", "add", "added.py"], cwd=repo_dir, capture_output=True)
    subprocess.run(["git", "commit", "-m", "feat: add hello function"], cwd=repo_dir, capture_output=True)
    
    # Get commit hash
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_dir,
        capture_output=True,
        text=True
    )
    commit_hash = result.stdout.strip()
    
    return repo_dir, commit_hash


class TestGetCommitMeta:
    """Tests for get_commit_meta function."""
    
    def test_get_commit_meta_success(self, git_repo_with_commits):
        """Test successfully getting commit metadata."""
        repo_dir, commit_hash = git_repo_with_commits
        
        full_hash, subject = get_commit_meta(commit_hash, str(repo_dir))
        
        assert full_hash == commit_hash
        assert subject == "feat: add hello function"
    
    def test_get_commit_meta_invalid_hash(self, mock_git_repo):
        """Test with invalid commit hash."""
        full_hash, subject = get_commit_meta("invalid_hash", str(mock_git_repo))
        
        assert full_hash == "invalid_hash"
        assert subject == ""


class TestGetNameStatus:
    """Tests for get_name_status function."""
    
    def test_get_name_status(self, git_repo_with_commits):
        """Test getting file change status."""
        repo_dir, commit_hash = git_repo_with_commits
        
        status = get_name_status(commit_hash, str(repo_dir))
        
        assert "added.py" in status
        assert status.startswith("A")  # Added file
    
    def test_get_name_status_with_modification(self, mock_git_repo):
        """Test getting status for modified file."""
        repo_dir = mock_git_repo
        
        # Modify existing file
        test_file = repo_dir / "test.txt"
        test_file.write_text("modified content")
        subprocess.run(["git", "add", "test.txt"], cwd=repo_dir, capture_output=True)
        subprocess.run(["git", "commit", "-m", "modify file"], cwd=repo_dir, capture_output=True)
        
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_dir,
            capture_output=True,
            text=True
        )
        commit_hash = result.stdout.strip()
        
        status = get_name_status(commit_hash, str(repo_dir))
        
        assert "test.txt" in status
        assert status.startswith("M")  # Modified file


class TestGetPatchUnified:
    """Tests for get_patch_unified function."""
    
    def test_get_patch_unified(self, git_repo_with_commits):
        """Test getting unified diff patch."""
        repo_dir, commit_hash = git_repo_with_commits
        
        patch = get_patch_unified(commit_hash, str(repo_dir))
        
        assert "added.py" in patch
        assert "def hello(): pass" in patch
        assert "diff --git" in patch


class TestFormatCommitDiff:
    """Tests for format_commit_diff function."""
    
    def test_format_commit_diff(self, git_repo_with_commits):
        """Test formatting commit diff in LLM-optimized format."""
        repo_dir, commit_hash = git_repo_with_commits
        
        formatted = format_commit_diff(commit_hash, str(repo_dir))
        
        assert f"@c {commit_hash}" in formatted
        assert "@s feat: add hello function" in formatted
        assert "@f" in formatted
        assert "@p" in formatted
        assert "@end" in formatted
        assert "added.py" in formatted


class TestGenerateEpicDiff:
    """Tests for generate_epic_diff function."""
    
    def test_generate_epic_diff_multiple_commits(self, mock_git_repo):
        """Test generating diff for multiple commits."""
        repo_dir = mock_git_repo
        hashes = []
        
        # Create multiple commits
        for i in range(2):
            file_path = repo_dir / f"file{i}.txt"
            file_path.write_text(f"content {i}")
            subprocess.run(["git", "add", f"file{i}.txt"], cwd=repo_dir, capture_output=True)
            subprocess.run(["git", "commit", "-m", f"commit {i}"], cwd=repo_dir, capture_output=True)
            
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=repo_dir,
                capture_output=True,
                text=True
            )
            hashes.append(result.stdout.strip())
        
        diff = generate_epic_diff(hashes, str(repo_dir))
        
        assert "@c" in diff
        assert "commit 0" in diff
        assert "commit 1" in diff
        assert "@end" in diff
    
    def test_generate_epic_diff_empty_list(self):
        """Test with empty hash list."""
        diff = generate_epic_diff([])
        assert diff == ""
    
    def test_generate_epic_diff_filters_empty_hashes(self, mock_git_repo):
        """Test that empty hashes are filtered out."""
        diff = generate_epic_diff(["", "  ", None], str(mock_git_repo))
        assert diff == ""


class TestGenerateEpicFilesChanged:
    """Tests for generate_epic_files_changed function."""
    
    def test_generate_epic_files_changed(self, mock_git_repo):
        """Test generating list of changed files."""
        repo_dir = mock_git_repo
        hashes = []
        
        # Create commits with different files
        for i in range(3):
            file_path = repo_dir / f"module{i}.py"
            file_path.write_text(f"# Module {i}")
            subprocess.run(["git", "add", f"module{i}.py"], cwd=repo_dir, capture_output=True)
            subprocess.run(["git", "commit", "-m", f"add module {i}"], cwd=repo_dir, capture_output=True)
            
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=repo_dir,
                capture_output=True,
                text=True
            )
            hashes.append(result.stdout.strip())
        
        files = generate_epic_files_changed(hashes, str(repo_dir))
        
        assert "module0.py" in files
        assert "module1.py" in files
        assert "module2.py" in files
        assert files.count("-") == 3  # Three bullet points
    
    def test_generate_epic_files_changed_empty_list(self):
        """Test with empty hash list."""
        files = generate_epic_files_changed([])
        assert files == ""
    
    def test_generate_epic_files_changed_deduplicates(self, mock_git_repo):
        """Test that duplicate files are deduplicated."""
        repo_dir = mock_git_repo
        hashes = []
        
        # Modify same file multiple times
        for i in range(2):
            test_file = repo_dir / "test.txt"
            test_file.write_text(f"content {i}")
            subprocess.run(["git", "add", "test.txt"], cwd=repo_dir, capture_output=True)
            subprocess.run(["git", "commit", "-m", f"modify {i}"], cwd=repo_dir, capture_output=True)
            
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=repo_dir,
                capture_output=True,
                text=True
            )
            hashes.append(result.stdout.strip())
        
        files = generate_epic_files_changed(hashes, str(repo_dir))
        
        # Should only appear once
        assert files.count("test.txt") == 1

