# Moderails – COMPLETE MODE

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

2. Commit all changes:
```bash
git add -A
git commit -m "feat: <task-name> - <brief description>"
```

3. Update task with status, summary, and git hash in one command:
```bash
moderails task update --task <task> --status completed --summary "brief summary" --git-hash $(git rev-parse HEAD)
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
