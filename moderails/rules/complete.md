# Moderails – COMPLETE MODE

**Active Mode**: COMPLETE  
**Output Format**: Start with `[MODE: COMPLETE]`

## PURPOSE
Mark task as completed and commit changes.

## WORKFLOW

1. Verify branch matches epic name:
```bash
git branch --show-current
```
**If branch name does not match epic name, STOP and ask user to resolve it.**

2. Update task status:
```bash
moderails task update --task <task> --status completed --summary "brief summary"
```

3. Commit all changes:
```bash
git add -A
git commit -m "feat: <task-name> - <brief description>"
```

4. Update task with git hash:
```bash
moderails task update --task <task> --git-hash $(git rev-parse HEAD)
```

## SUMMARY GUIDELINES
Write a brief summary that captures:
- What was implemented
- Key changes made
- Any notable decisions

This summary becomes part of the epic context for future tasks.

## GIT COMMIT MESSAGE
Use conventional commits format:
- `feat: <description>` for new features
- `fix: <description>` for bug fixes
- `refactor: <description>` for refactoring

## FORBIDDEN
- **NEVER commit task files** (`moderails/tasks/` is in .gitignore)


---
**YOU MUST FOLLOW THE WORKFLOW**
