# COMPLETE MODE

**Active Mode**: COMPLETE  
**Output Format**: Start with `[MODE: COMPLETE]`

## PURPOSE
Mark task as completed and commit changes.

## WORKFLOW

1. Check current branch:
```bash
git branch --show-current
```
**If on `main` branch: ASK USER TO CONFIRM before proceeding with commit.**  
Wait for explicit confirmation. If user declines, STOP and suggest switching to a feature branch.

2. Review changes for this task:
```bash
git status
```
Identify which files were changed as part of this task.

3. Mark task as completed with summary:
```bash
moderails task complete --task <task-id> --summary "brief summary of what was done"
```
**Task summary:** Write a brief summary that captures what was implemented, key changes made, and any notable decisions.

**This will:**
- Mark the task as completed in the database
- Export the task to history.jsonl 

4. Commit the code changes AND history.jsonl:
```bash
git add <file1> <file2> <file3>... history.jsonl
git commit -m "<type>: <task-name> - <brief description>"
```

**Commit message format:**
The commit message uses the task type directly:
- Tasks with type "feature" → `feature: <description>`
- Tasks with type "fix" → `fix: <description>`
- Tasks with type "refactor" → `refactor: <description>`

**Important:** 
- Only stage files that are part of this task
- MUST include history.jsonl in the commit
- Do NOT use `git add -A`

5. Update task with git hash:
```bash
moderails task update --task <task-id> --git-hash $(git rev-parse HEAD)
```
This captures the commit hash for the completed work. 

## FORBIDDEN
- **commit task files** (`.moderails/tasks/` is in .gitignore)

---
**YOU MUST FOLLOW THE WORKFLOW**
