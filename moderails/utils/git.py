"""Git utilities for generating LLM-optimized commit diffs."""

import subprocess
from pathlib import Path
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


def truncate_patch(patch: str, max_lines_per_file: int = 100) -> str:
    """
    Truncate per-file diffs to avoid context overload.
    
    Args:
        patch: Unified diff patch output
        max_lines_per_file: Maximum lines to show per file diff
    
    Returns:
        Truncated patch with markers for omitted content
    """
    if not patch:
        return ""
    
    lines = patch.splitlines()
    result = []
    current_file_start = None
    in_file = False
    
    for i, line in enumerate(lines):
        # Detect start of new file diff
        if line.startswith("diff --git "):
            # Process previous file if any
            if in_file and current_file_start is not None:
                file_content = lines[current_file_start:i]
                if len(file_content) > max_lines_per_file:
                    # Truncate and add marker
                    result.extend(file_content[:max_lines_per_file])
                    omitted = len(file_content) - max_lines_per_file
                    result.append(f"... [diff truncated: +{omitted} more lines omitted for context efficiency]")
                else:
                    result.extend(file_content)
            
            # Start new file
            current_file_start = i
            in_file = True
        
    # Process last file
    if in_file and current_file_start is not None:
        file_content = lines[current_file_start:]
        if len(file_content) > max_lines_per_file:
            result.extend(file_content[:max_lines_per_file])
            omitted = len(file_content) - max_lines_per_file
            result.append(f"... [diff truncated: +{omitted} more lines omitted for context efficiency]")
        else:
            result.extend(file_content)
    
    return "\n".join(result) if result else patch


def format_commit_diff(hash: str, cwd: str = ".") -> str:
    """
    Format a single commit in LLM-optimized structure.
    
    Format:
        @c <hash>
        @s <subject>
        @f
        <name-status lines>
        @p
        <patch>
        @end
    """
    commit_hash, subject = get_commit_meta(hash, cwd)
    name_status = get_name_status(hash, cwd)
    patch = get_patch_unified(hash, cwd)
    
    # Truncate large diffs to avoid context overload
    if patch:
        patch = truncate_patch(patch)
    
    parts = [f"@c {commit_hash}"]
    
    if subject:
        parts.append(f"@s {subject}")
    
    if name_status:
        parts.append("@f")
        parts.append(name_status)
    
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
    Generate simple list of files changed across commits.
    
    Args:
        git_hashes: List of commit hashes in chronological order
        cwd: Working directory for git commands
    
    Returns:
        Simple list of all files touched in the epic
    """
    if not git_hashes:
        return ""
    
    # Collect all unique files
    files = set()
    
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
            
            # Get all files regardless of operation type
            if status.startswith("R") and len(parts) > 2:
                # For renames, include the new filename
                files.add(parts[2])
            elif len(parts) > 1:
                files.add(parts[1])
    
    # Build simple list
    if not files:
        return ""
    
    output = []
    for f in sorted(files):
        output.append(f"- {f}")
    
    return "\n".join(output)

