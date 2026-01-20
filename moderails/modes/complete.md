# COMPLETE MODE

**Active Mode**: COMPLETE  
**Output Format**: Start with `[MODE: COMPLETE]`

---

{% if current_task %}
## CURRENT TASK

- **ID**: `{{ current_task.id }}`
- **Name**: {{ current_task.name }}
- **Type**: {{ current_task.type }}
{% endif %}

## GIT STATUS

**Branch**: `{{ git.branch }}`
{% if git.is_main %}

**WARNING: On `main` branch!** Ask user to confirm before committing.
Wait for explicit confirmation. If user declines, STOP and suggest switching to a feature branch.
{% endif %}

{% if git.staged_files %}
**Staged files:**
{% for f in git.staged_files %}- {{ f }}
{% endfor %}
{% endif %}

{% if git.unstaged_files %}
**Unstaged changes:**
{% for f in git.unstaged_files %}- {{ f }}
{% endfor %}
{% endif %}

{% if not git.staged_files and not git.unstaged_files %}
No changes detected.
{% endif %}

---

## PURPOSE

Mark task as completed and commit changes.

## WORKFLOW

1. Stage changes for this task:
```bash
git add <file1> <file2> <file3>...
```
Stage only the files that are part of this task. Do NOT use `git add -A`.

2. Complete task with commit:
```bash
moderails task complete --task {{ current_task.id if current_task else '<task-id>' }} --summary "brief summary" --commit-message "{{ current_task.type if current_task else '<type>' }}: <description>"
```

**This single command will:**
- Mark the task as completed in the database
- Export the task to history.jsonl
- Stage history.jsonl
- Commit with your message
- Update task with git hash

**Commit message format:**
- `feature: <description>` for feature tasks
- `fix: <description>` for fix tasks
- `refactor: <description>` for refactor tasks

**If any git step fails**, the command returns fallback instructions for you to complete manually.

## FORBIDDEN

- **commit task files** (`.moderails/tasks/` is in .gitignore)

---
**YOU MUST FOLLOW THE WORKFLOW**
