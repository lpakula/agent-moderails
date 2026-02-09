# PLAN MODE

**Active Mode**: PLAN  
**Output Format**: Start with `[MODE: PLAN]`

---

{% if current_task %}
## CURRENT TASK

- **ID**: `{{ current_task.id }}`
- **Name**: {{ current_task.name }}
- **File**: `{{ current_task.file_path }}`
{% if current_task.epic %}- **Epic**: {{ current_task.epic.name }} (`{{ current_task.epic.id }}`){% endif %}
{% else %}
## NO ACTIVE TASK

Start a task first with `moderails task create --name "Task name"` or switch to an existing task.
{% endif %}

---

## PURPOSE

Create executable TODO plan in the task file. **Default: one task.** Split only when the user explicitly asks.

## WORKFLOW

{% if current_task %}
1. Edit the task file: `{{ current_task.file_path }}`
{% else %}
1. No active task - start one first
{% endif %}

2. Create atomic TODO LIST items

3. **Evaluate complexity** (suggestion only): If the plan has many phases or TODO items (5+ phases or 20+ items), you may tell the user they *can* split later if they want:
   
   > "This task has many phases. If you ever want to split it into smaller tasks, say so or use `#plan --split`."

   Do **not** create new tasks or split unless the user explicitly asks (e.g. "split it" or uses `--split`).

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
- **No splitting the task or creating multiple tasks** unless the user explicitly requests it (e.g. "split this task" or `#plan --split`). Default is always one task.

## SPLIT MODE (only when user explicitly requests split)

**Only** if the user message contains `--split` or the user clearly asks to split the task (e.g. "split it", "break into smaller tasks"):

1. **Analyze the current task** and break it into logical phases (each becomes a separate task)

2. **Create tasks in order** under the same epic:
```bash
moderails task create --name "1-setup-database" --epic {{ current_task.epic.id if current_task and current_task.epic else '<epic-id>' }} --status draft
moderails task create --name "2-create-models" --epic {{ current_task.epic.id if current_task and current_task.epic else '<epic-id>' }} --status draft
moderails task create --name "3-add-api-endpoints" --epic {{ current_task.epic.id if current_task and current_task.epic else '<epic-id>' }} --status draft
```
   Use numbered prefixes (1-, 2-, 3-) to maintain order.
   Task files are stored in `_moderails/tasks/{epic-name}/{task-name}-{id}.plan.md`.

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
