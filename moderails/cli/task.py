"""Task management CLI commands."""

import subprocess
import time
from typing import Optional

import click

from ..config import is_private_mode
from ..db.models import TaskStatus, TaskType
from ..utils.git import get_staged_files, is_git_repo
from .common import get_moderails_dir, get_services_or_exit


@click.group()
@click.pass_context
def task(ctx):
    """Task management commands."""
    pass


@task.command("create")
@click.option("--name", "-n", required=True, help="Task name")
@click.option("--description", "-d", help="Task description (context for draft tickets)")
@click.option("--epic", "-e", help="Epic ID (6-character, optional)")
@click.option("--type", "-t", type=click.Choice(["feature", "fix", "refactor", "chore"]), default="feature", help="Task type (default: feature)")
@click.option("--status", "-s", type=click.Choice(["draft", "in-progress"]), default="in-progress", help="Initial task status (default: in-progress)")
@click.pass_context
def task_create(ctx, name: str, description: Optional[str], epic: Optional[str], type: str, status: str):
    """Create a new task. Plan file is created when entering #plan mode."""
    services = get_services_or_exit(ctx)
    
    # Validate epic first if provided
    epic_obj = None
    if epic:
        epic_obj = services["epic"].get(epic)
        if not epic_obj:
            click.echo(f"❌ Epic '{epic}' not found")
            return
    
    try:
        task_type = TaskType(type)
        task_status = TaskStatus(status)
        task = services["task"].create(
            name=name,
            description=description or "",
            epic_id=epic if epic else None,
            task_type=task_type,
            status=task_status,
        )
        
        # Auto-create session if task starts as in-progress
        if task_status == TaskStatus.IN_PROGRESS:
            services["session"].ensure_active(task.id)
        
        click.echo(f"✅ Task created: {task.id} - {click.style(task.name, fg='green', bold=True)}")
        click.echo(f"   Type: {task.type.value}")
        if epic_obj:
            click.echo(f"   Epic: {epic_obj.id} - {epic_obj.name}")
        click.echo(f"   Status: {task.status.value}")
        
        return task
    except ValueError as e:
        click.echo(f"❌ Error: {e}")
        return None


@task.command("update")
@click.option("--id", "-i", "task_id", required=True, help="Task ID (6-character)")
@click.option("--name", help="New task name")
@click.option("--status", "-s", type=click.Choice(["draft", "in-progress", "completed"]))
@click.option("--type", type=click.Choice(["feature", "fix", "refactor", "chore"]), help="New task type")
@click.option("--summary", help="Task summary")
@click.option("--description", "-d", help="Task description (context for draft tickets)")
@click.option("--git-hash", help="Git commit hash")
@click.option("--file-name", help="Task file name (e.g., my-task.md)")
@click.pass_context
def task_update(ctx, task_id: str, name: Optional[str], status: Optional[str], type: Optional[str], summary: Optional[str], description: Optional[str], git_hash: Optional[str], file_name: Optional[str]):
    """Update task name, status, type, summary, description, git hash, or file name."""
    services = get_services_or_exit(ctx)
    
    status_enum = TaskStatus(status) if status else None
    type_enum = TaskType(type) if type else None
    t = services["task"].update(task_id, name=name, status=status_enum, task_type=type_enum, summary=summary, description=description, git_hash=git_hash, file_name=file_name)
    
    if not t:
        click.echo(f"❌ Task '{task_id}' not found")
        return
    
    # Auto-create session when task transitions to in-progress
    if status == "in-progress":
        services["session"].ensure_active(task_id)
    
    click.echo(f"✅ Updated task: {t.id} - {t.name} [{t.type.value}] [{t.status.value}]")
    
    if status == "completed":
        click.echo("\n💡 Now commit your changes with a descriptive message")


@task.command("delete")
@click.option("--id", "-i", "task_id", required=True, help="Task ID (6-character)")
@click.option("--confirm", is_flag=True, help="Confirm deletion")
@click.pass_context
def task_delete(ctx, task_id: str, confirm: bool):
    """Delete a task."""
    if not confirm:
        click.echo("Use --confirm to delete")
        return
    
    services = get_services_or_exit(ctx)
    if services["task"].delete(task_id):
        click.echo(f"✅ Deleted task: {task_id}")
    else:
        click.echo(f"❌ Task '{task_id}' not found")


@task.command("complete")
@click.option("--id", "-i", "task_id", required=True, help="Task ID (6-character)")
@click.option("--summary", "-s", help="Task summary")
@click.option("--commit-message", "-m", help="Git commit message")
@click.pass_context
def task_complete(ctx, task_id: str, summary: Optional[str], commit_message: Optional[str]):
    """Mark task as completed and optionally commit changes.
    
    In git repos: stages history.jsonl, commits with provided message, and updates task with git hash.
    In non-git projects: marks task complete and exports to history.
    """
    services = get_services_or_exit(ctx)
    moderails_dir = get_moderails_dir(ctx.obj.get("db_path"))
    history_path = moderails_dir / "history.jsonl"
    private_mode = is_private_mode()
    use_git = is_git_repo()
    
    if use_git:
        # Git workflow: require staged files and commit message
        staged_files = get_staged_files()
        if not staged_files:
            click.echo("❌ No staged files found.")
            click.echo("\n💡 Stage your changes first:")
            click.echo("   git add <file1> <file2> ...")
            click.echo("\nThen run this command again.")
            return
        
        if not commit_message:
            click.echo("❌ --commit-message is required.")
            return
    
    try:
        # Update summary if provided
        if summary:
            services["task"].update(task_id, summary=summary)
        
        # Complete the task
        task = services["task"].complete(task_id, git_hash=None)
        click.echo(f"✅ Task completed: {task.id} - {task.name}")
        
        # Delete the session (task is done, session no longer needed)
        services["session"].delete_for_task(task_id)
        
        # Export to history.jsonl
        services["history"].export_task(task_id)
        click.echo("✅ Exported to history.jsonl")
        
        # Git workflow: commit and update hash
        if use_git:
            # Step 1: Stage history.jsonl (skip in private mode - it's gitignored)
            if not private_mode:
                time.sleep(0.2)  # Let file watchers settle
                stage_result = subprocess.run(
                    ["git", "add", str(history_path)],
                    check=False,
                    capture_output=True,
                    text=True
                )
                if stage_result.returncode != 0:
                    click.echo("⚠️  Failed to stage history.jsonl")
                    click.echo("\n## FALLBACK: Complete git workflow manually")
                    click.echo("```bash")
                    click.echo(f"git add {history_path}")
                    click.echo(f"git commit -m \"{commit_message}\"")
                    click.echo(f"moderails task update --task {task_id} --git-hash $(git rev-parse HEAD)")
                    click.echo("```")
                    if stage_result.stderr:
                        click.echo(f"\nGit error: {stage_result.stderr.strip()}")
                    return
                
                click.echo("✅ Staged history.jsonl")
            
            # Step 2: Commit
            commit_result = subprocess.run(
                ["git", "commit", "-m", commit_message],
                check=False,
                capture_output=True,
                text=True
            )
            if commit_result.returncode != 0:
                click.echo("⚠️  Commit failed")
                click.echo("\n## FALLBACK: Complete git workflow manually")
                click.echo("```bash")
                click.echo(f"git commit -m \"{commit_message}\"")
                click.echo(f"moderails task update --task {task_id} --git-hash $(git rev-parse HEAD)")
                click.echo("```")
                if commit_result.stderr:
                    click.echo(f"\nGit error: {commit_result.stderr.strip()}")
                return
            
            click.echo(f"✅ Committed: {commit_message}")
            
            # Step 3: Get git hash and update task
            hash_result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                check=False,
                capture_output=True,
                text=True
            )
            if hash_result.returncode != 0:
                click.echo("⚠️  Could not get git hash")
                click.echo("\n## FALLBACK: Update task with git hash manually")
                click.echo("```bash")
                click.echo(f"moderails task update --task {task_id} --git-hash $(git rev-parse HEAD)")
                click.echo("```")
                return
            
            git_hash = hash_result.stdout.strip()
            services["task"].update(task_id, git_hash=git_hash)
            click.echo(f"✅ Updated task with git hash: {git_hash[:7]}")
            click.echo(f"\n🎉 Task {task_id} fully completed and committed!")
        
    except ValueError as e:
        click.echo(f"❌ {e}")


@task.command("list")
@click.option("--status", "-s", type=click.Choice(["draft", "in-progress", "completed"]), help="Filter by status")
@click.option("--epic-name", "-e", help="Filter by epic name")
@click.pass_context
def task_list(ctx, status: Optional[str], epic_name: Optional[str]):
    """List all tasks as a simple table (for agents)."""
    services = get_services_or_exit(ctx)
    
    # Get all tasks
    status_enum = TaskStatus(status) if status else None
    tasks = services["task"].list_all(epic_name=epic_name, status=status_enum)
    
    if not tasks:
        click.echo("No tasks found.")
        return
    
    # Sort: non-completed tasks first (newest at top), then completed tasks at bottom (newest at top)
    sorted_tasks = sorted(
        tasks,
        key=lambda x: (
            x.status == TaskStatus.COMPLETED,  # False (0) first, True (1) last
            -(x.completed_at if (x.status == TaskStatus.COMPLETED and x.completed_at) else x.created_at).timestamp()
        )
    )
    
    # Simple table format: id | name | status | epic_id
    click.echo("id     | name                                             | status      | epic_id")
    click.echo("-------|--------------------------------------------------|-------------|--------")
    for task in sorted_tasks:
        name_truncated = task.name[:48] + ".." if len(task.name) > 50 else task.name
        epic_id = task.epic_id if task.epic_id else ""
        click.echo(f"{task.id} | {name_truncated:<48} | {task.status.value:<11} | {epic_id}")


@task.command("load")
@click.option("--id", "-i", "task_id", required=True, help="Task ID (6-character)")
@click.pass_context
def task_load(ctx, task_id: str):
    """Load task details and plan file (task context only)."""
    services = get_services_or_exit(ctx)
    moderails_dir = get_moderails_dir(ctx.obj.get("db_path"))
    
    # Get task
    task = services["task"].get(task_id)
    if not task:
        click.echo(f"❌ Task '{task_id}' not found")
        return
    
    # Display task details
    click.echo("## TASK DETAILS\n")
    click.echo(f"**ID**: {task.id}")
    click.echo(f"**Name**: {task.name}")
    click.echo(f"**Type**: {task.type.value}")
    click.echo(f"**Status**: {task.status.value}")
    if task.epic:
        click.echo(f"**Epic**: {task.epic.name} ({task.epic_id})")
    if task.file_name:
        click.echo(f"**File**: _moderails/{task.file_name}")
    if task.summary:
        click.echo(f"**Summary**: {task.summary}")
    if task.description:
        click.echo(f"**Description**: {task.description}")
    click.echo()
    
    # Load task file content
    if task.file_name:
        task_file = moderails_dir / task.file_name
        if task_file.exists():
            click.echo("## TASK PLAN\n")
            click.echo(task_file.read_text())
