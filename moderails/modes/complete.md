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

3. Commit the code changes:
```bash
git add <file1> <file2> <file3>...
git commit -m "<type>: <task-name> - <brief description>"
```

**Commit message format:**
The commit message uses the task type directly:
- Tasks with type "feature" → `feature: <description>`
- Tasks with type "fix" → `fix: <description>`
- Tasks with type "refactor" → `refactor: <description>`

**Important:** 
- Only stage files that are part of this task. Do NOT use `git add -A`
- Do NOT include history.json yet (it will be committed by user later)

4. Mark task as completed with summary:
```bash
moderails task complete --task <task-id> --summary "brief summary of what was done"
```
**Task summary:** Write a brief summary that captures what was implemented, key changes made, and any notable decisions. 

## FORBIDDEN
- **commit task files** (`.moderails/tasks/` is in .gitignore)

---
**YOU MUST FOLLOW THE WORKFLOW**
