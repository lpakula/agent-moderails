# Moderails – EXECUTE MODE

**Active Mode**: EXECUTE  
**Output Format**: Start with `[MODE: EXECUTE]`

## PURPOSE
Implement EXACTLY what's in the TODO list. One item at a time.

## WORKFLOW

1. Update task status to in-progress:
```bash
moderails task update --task <task> --status in-progress
```

2. Read the task file to fetch fresh content

3. For each TODO item:
   - Execute the item
   - Mark complete in task file: `[x]`
   - Explain changes made
   - Wait for user confirmation

4. When all TODOs complete, suggest `#complete`

## WORKING WITH TASK FILE
- The task file IS your source of truth
- Read it before each TODO item
- Update `[ ]` to `[x]` as you complete items

## PERMITTED
- Execute one TODO item at a time
- Make minimal changes per plan
- Edit task file directly (mark complete, add notes)

## FORBIDDEN
- No new tasks beyond TODO list
- No refactors or optimizations
- No creative additions

---
**YOU MUST FOLLOW THE WORKFLOW**
