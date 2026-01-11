# PLAN MODE

**Active Mode**: PLAN  
**Output Format**: Start with `[MODE: PLAN]`

## PURPOSE
Create executable TODO plan in the task file.

## WORKFLOW

1. Update each section in the task file

2. Create atomic TODO LIST items

3. **Evaluate complexity**: If the plan has many phases or TODO items (5+ phases or 20+ items), suggest splitting:
   
   > "This task has many phases. Consider splitting into smaller tasks with `--split` for better tracking."

4. Get user approval

5. When approved, suggest `#execute`

## PLANNING RULES
- Edit the task file directly
- Keep TODO list minimal but complete
- Each item must be atomic and specific

## PERMITTED
- Design detailed implementation plan
- Edit task file directly
- Create atomic TODO items

## FORBIDDEN
- No implementation or code writing
- No code samples in task files
- No task status update 
- No `todo_write` or internal TODO lists

## SPLIT MODE

If user message contains `--split` flag:

1. **Analyze the current task** and break it into logical phases (each becomes a separate task)

2. **Create tasks in order** under the same epic:
```bash
moderails task create --name "1-setup-database" --epic <epic-id> --status draft
moderails task create --name "2-create-models" --epic <epic-id> --status draft
moderails task create --name "3-add-api-endpoints" --epic <epic-id> --status draft
```
   Use numbered prefixes (1-, 2-, 3-) to maintain order.
   Task files are named `<epic-name>--<task-name>-<id>.plan.md` for easy grouping.

3. **Update each task file** with its specific plan:
   - Each task should have 3-7 TODO items max
   - Keep tasks atomic and focused
   - Reference dependencies between tasks if needed

4. **Update original task** to reference the split:
   - Mark it as split or delete it
   - Point to the new task sequence

5. **Summary**: List all created tasks with their IDs

**Goal**: Each split task should be completable in one focused session.

---
**YOU MUST FOLLOW THE WORKFLOW**
