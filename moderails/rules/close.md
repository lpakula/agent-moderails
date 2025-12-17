# Moderails – CLOSE MODE

**Active Mode**: CLOSE  
**Output Format**: Start with `[MODE: CLOSE]`

## PURPOSE
Abandon a task and reset all changes.

## WORKFLOW

1. Delete the task:
```bash
moderails task delete --task <task> --confirm
```

2. Reset git changes:
```bash
git reset --hard HEAD
```

---
**YOU MUST FOLLOW THE WORKFLOW**
