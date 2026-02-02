"""Git utilities for generating LLM-optimized commit diffs."""

import subprocess
from typing import Optional


def _run_git(args: list[str], cwd: str = ".") -> Optional[str]:
    """Run git command and return output, or None on error."""
    try:
        result = subprocess.run(
            ["git", "-C", cwd] + args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            return None
        return result.stdout
    except Exception:
        return None


def is_git_repo(cwd: str = ".") -> bool:
    """Check if current directory is inside a git repository."""
    return _run_git(["rev-parse", "--is-inside-work-tree"], cwd) is not None


# Patterns to exclude from files_changed in history
EXCLUDED_PATTERNS = [
    "_moderails/",
    "poetry.lock",
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "Gemfile.lock",
    "Cargo.lock",
    "composer.lock",
    "go.sum",
]


def get_staged_files(cwd: str = ".") -> list[str]:
    """
    Get list of staged files, excluding irrelevant patterns.
    
    Returns:
        List of file paths that are staged for commit
    """
    output = _run_git(["diff", "--cached", "--name-only"], cwd)
    if not output:
        return []
    
    files = []
    for line in output.splitlines():
        line = line.strip()
        if not line:
            continue
        
        # Check if file matches any excluded pattern
        excluded = False
        for pattern in EXCLUDED_PATTERNS:
            if pattern in line:
                excluded = True
                break
        
        if not excluded:
            files.append(line)
    
    return files


def get_current_branch(cwd: str = ".") -> str | None:
    """
    Get the current git branch name.
    
    Returns:
        Branch name or None if not in a git repo or detached HEAD
    """
    output = _run_git(["branch", "--show-current"], cwd)
    if not output:
        return None
    return output.strip() or None


def get_unstaged_files(cwd: str = ".") -> list[str]:
    """
    Get list of unstaged modified files (tracked files with changes not staged).
    
    Returns:
        List of file paths with unstaged changes
    """
    output = _run_git(["diff", "--name-only"], cwd)
    if not output:
        return []
    
    files = []
    for line in output.splitlines():
        line = line.strip()
        if not line:
            continue
        
        # Check if file matches any excluded pattern
        excluded = False
        for pattern in EXCLUDED_PATTERNS:
            if pattern in line:
                excluded = True
                break
        
        if not excluded:
            files.append(line)
    
    return files


def get_commit_meta(hash: str, cwd: str = ".") -> tuple[str, str]:
    """
    Get commit hash and subject line.
    
    Returns:
        (full_hash, subject) or (hash, "") on error
    """
    output = _run_git(["show", "-s", "--format=%H%n%s", hash], cwd)
    if not output:
        return (hash, "")
    
    lines = output.splitlines()
    full_hash = lines[0] if lines else hash
    subject = lines[1] if len(lines) > 1 else ""
    return (full_hash, subject)


def get_name_status(hash: str, cwd: str = ".") -> str:
    """
    Get file change summary (Added/Modified/Deleted/Renamed).
    
    Returns:
        Lines like "A    file.py" or "R100    old.py    new.py"
    """
    output = _run_git(
        ["show", "--pretty=format:", "--name-status", "-M", "-C", hash],
        cwd
    )
    return output.rstrip() if output else ""


def get_patch_unified(hash: str, cwd: str = ".") -> str:
    """
    Get unified diff patch with minimal context for token efficiency.
    
    Uses --unified=0 for most compact representation.
    """
    output = _run_git(
        ["show", "--pretty=format:", "--patch", "--unified=0", "-M", "-C", hash],
        cwd
    )
    return output.rstrip() if output else ""


def truncate_patch(patch: str, max_lines_per_file: int = 50) -> str:
    """
    Truncate per-file diffs to avoid context overload.
    
    - Deleted files: show "[file deleted]" instead of full content
    - Renamed files with no changes: show "[renamed from X]"
    - Large diffs: show "[diff skipped: N lines]"
    
    Args:
        patch: Unified diff patch output
        max_lines_per_file: Maximum lines to show per file diff (default 50)
    
    Returns:
        Truncated patch - noise reduced for agent consumption
    """
    if not patch:
        return ""
    
    lines = patch.splitlines()
    result = []
    current_file_start = None
    current_filename = None
    in_file = False
    
    def extract_filename(diff_line: str) -> str:
        """Extract filename from 'diff --git a/file b/file' line."""
        parts = diff_line.split(" b/")
        return parts[-1] if len(parts) > 1 else diff_line
    
    def is_deleted_file(file_content: list[str]) -> bool:
        """Check if this is a deleted file diff."""
        # Skip first line (always "diff --git...")
        for line in file_content[1:]:
            if line.startswith("deleted file mode"):
                return True
            if line.startswith("@@"):
                break
        return False
    
    def is_new_file(file_content: list[str]) -> bool:
        """Check if this is a new file diff."""
        # Skip first line (always "diff --git...")
        for line in file_content[1:]:
            if line.startswith("new file mode"):
                return True
            if line.startswith("@@"):
                break
        return False
    
    def is_rename_only(file_content: list[str]) -> tuple[bool, str | None]:
        """Check if this is a rename with no content changes. Returns (is_rename_only, old_name)."""
        old_name = None
        has_rename = False
        has_hunks = False
        
        # Skip first line (always "diff --git...")
        for line in file_content[1:]:
            if line.startswith("rename from "):
                old_name = line.replace("rename from ", "").strip()
                has_rename = True
            if line.startswith("@@"):
                has_hunks = True
                break
        
        return (has_rename and not has_hunks, old_name)
    
    def process_file(file_content: list[str], filename: str):
        """Process a single file's diff content."""
        # Check for deleted file
        if is_deleted_file(file_content):
            result.append(f"D  {filename}")
            return
        
        # Check for rename-only
        rename_only, old_name = is_rename_only(file_content)
        if rename_only and old_name:
            result.append(f"R  {old_name} -> {filename}")
            return
        
        # Check for new file that's too large
        if is_new_file(file_content) and len(file_content) > max_lines_per_file:
            result.append(f"A  [{len(file_content)} lines] {filename}")
            return
        
        # Check for modified file that's too large
        if len(file_content) > max_lines_per_file:
            result.append(f"M  [{len(file_content)} lines] {filename}")
            return
        
        # Include full diff
        result.extend(file_content)
    
    for i, line in enumerate(lines):
        # Detect start of new file diff
        if line.startswith("diff --git "):
            # Process previous file if any
            if in_file and current_file_start is not None:
                file_content = lines[current_file_start:i]
                process_file(file_content, current_filename or "unknown")
            
            # Start new file
            current_file_start = i
            current_filename = extract_filename(line)
            in_file = True
        
    # Process last file
    if in_file and current_file_start is not None:
        file_content = lines[current_file_start:]
        process_file(file_content, current_filename or "unknown")
    
    return "\n".join(result) if result else patch


def format_commit_diff(hash: str, cwd: str = ".") -> str:
    """
    Format a single commit in LLM-optimized structure.
    
    Format:
        @c <hash>
        @s <subject>
        @p
        <patch>
        @end
    
    Note: File list (@f) is omitted as it's redundant with the patch.
    """
    commit_hash, subject = get_commit_meta(hash, cwd)
    patch = get_patch_unified(hash, cwd)
    
    # Truncate large diffs to avoid context overload
    if patch:
        patch = truncate_patch(patch)
    
    parts = [f"@c {commit_hash}"]
    
    if subject:
        parts.append(f"@s {subject}")
    
    if patch:
        parts.append("@p")
        parts.append(patch)
    
    parts.append("@end")
    
    return "\n".join(parts)


def generate_epic_diff(git_hashes: list[str], cwd: str = ".") -> str:
    """
    Generate LLM-optimized diff for multiple commits in chronological order.
    
    Args:
        git_hashes: List of commit hashes in chronological order
        cwd: Working directory for git commands
    
    Returns:
        Formatted diff string with all commits, or empty string if no valid commits
    """
    if not git_hashes:
        return ""
    
    # Filter out empty hashes and format each commit
    commit_diffs = []
    for hash in git_hashes:
        if hash and hash.strip():
            diff = format_commit_diff(hash.strip(), cwd)
            if diff:
                commit_diffs.append(diff)
    
    if not commit_diffs:
        return ""
    
    return "\n\n".join(commit_diffs)


def generate_epic_files_changed(git_hashes: list[str], cwd: str = ".") -> str:
    """
    Generate list of files changed across commits with status indicators.
    
    Args:
        git_hashes: List of commit hashes in chronological order
        cwd: Working directory for git commands
    
    Returns:
        List of files with status (A=added, M=modified, D=deleted, R=renamed)
    """
    if not git_hashes:
        return ""
    
    # Collect files with their status (file -> status)
    # Later status overwrites earlier (e.g., A then M -> M)
    files: dict[str, str] = {}
    
    for hash in git_hashes:
        if not hash or not hash.strip():
            continue
        
        name_status = get_name_status(hash.strip(), cwd)
        if not name_status:
            continue
        
        for line in name_status.splitlines():
            parts = line.split("\t")
            if not parts:
                continue
            
            status = parts[0].strip()
            
            # Normalize status to single letter
            if status.startswith("R"):
                status_char = "R"
            elif status.startswith("C"):
                status_char = "C"
            else:
                status_char = status[0] if status else "M"
            
            # Get filename based on operation type
            if status.startswith("R") and len(parts) > 2:
                # For renames, include the new filename
                files[parts[2]] = status_char
            elif len(parts) > 1:
                files[parts[1]] = status_char
    
    # Build list with status
    if not files:
        return ""
    
    output = []
    for f in sorted(files.keys()):
        output.append(f"{files[f]}  {f}")
    
    return "\n".join(output)

