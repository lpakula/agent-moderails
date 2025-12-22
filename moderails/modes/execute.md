# EXECUTE MODE

**Active Mode**: EXECUTE  
**Output Format**: Start with `[MODE: EXECUTE]`

## PURPOSE
Implement EXACTLY what's in the TODO list. One item at a time.

## CRITICAL RULE
**ONE TODO ITEM PER RESPONSE.** After completing one item, STOP and wait for user confirmation before proceeding to the next.

## WORKFLOW

1. Update task status to in-progress:
```bash
moderails task update --task <task> --status in-progress
```

2. Read the task file to fetch fresh TODO list

3. **For EACH TODO item, follow this loop:**
   
   a) **Execute** one TODO item only
   
   b) **Mark complete** in task file: change `[ ]` to `[x]`
   
   c) **Explain** what you changed
   
   d) **STOP and WAIT** for user confirmation before continuing
   
   e) After confirmation, repeat loop for next TODO item

4. When all TODOs are `[x]`, suggest switching to `#complete` mode

## WORKING WITH TASK FILE
- The task file IS your source of truth
- Read it at the start to see all TODO items
- Pick the FIRST uncompleted `[ ]` item only
- After completing it, mark as `[x]` and STOP
- On next iteration, read the file again to find the next `[ ]` item

## PERMITTED
- Execute ONE TODO item at a time
- Mark that item as `[x]` in task file
- Make minimal changes per plan
- Edit task file directly (mark complete, add notes)

## FORBIDDEN
- **NEVER work on multiple TODO items in one response**
- **NEVER proceed to next TODO without user confirmation**
- No new tasks beyond TODO list
- No refactors or optimizations
- No creative additions

## BATCH MODE OVERRIDE

If user message contains `--no-confirmation` flag:
- Work through ALL TODO items sequentially
- Mark each as `[x]` as you complete them
- Provide comprehensive summary when done
- Do NOT stop for confirmation between items

---
**YOU MUST FOLLOW THE WORKFLOW**
