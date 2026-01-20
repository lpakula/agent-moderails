# EXECUTE MODE

**Active Mode**: EXECUTE  
**Output Format**: Start with `[MODE: EXECUTE]`
{% if "no-confirmation" in flags %}
**Flag**: `--no-confirmation` (batch mode)
{% endif %}

---

{% if current_task %}
## CURRENT TASK

- **ID**: `{{ current_task.id }}`
- **Name**: {{ current_task.name }}
- **Status**: {{ current_task.status }}
- **File**: `{{ current_task.file_path }}`
{% if current_task.epic %}
- **Epic**: {{ current_task.epic.name }}
{% endif %}
{% endif %}

---

## PURPOSE

Implement EXACTLY what's in the TODO list.

{% if "no-confirmation" in flags %}
## BATCH MODE

Work through ALL TODO items sequentially without stopping for confirmation.

## WORKFLOW

{% if current_task and current_task.status == "draft" %}
1. Update task to in-progress:
```bash
moderails task update --task {{ current_task.id }} --status in-progress
```

2. Read the task file: `{{ current_task.file_path }}`
{% else %}
1. Read the task file: `{{ current_task.file_path }}`
{% endif %}

2. **For EACH TODO item:**
   - Execute the TODO item
   - Mark complete in task file: change `[ ]` to `[x]`
   - Continue immediately to next item (no stopping)

3. When all TODOs are `[x]`:
   - Provide comprehensive summary of all changes
   - Suggest switching to `#complete` mode

{% else %}
## CRITICAL RULE

**ONE TODO ITEM PER RESPONSE.** After completing one item, STOP and wait for user confirmation before proceeding to the next.

## WORKFLOW

{% if current_task and current_task.status == "draft" %}
1. Update task to in-progress:
```bash
moderails task update --task {{ current_task.id }} --status in-progress
```

2. Read the task file: `{{ current_task.file_path }}`
{% else %}
1. Read the task file: `{{ current_task.file_path }}`
{% endif %}

2. **For EACH TODO item, follow this loop:**
   
   a) **Execute** one TODO item only
   
   b) **Mark complete** in task file: change `[ ]` to `[x]`
   
   c) **Explain** what you changed
   
   d) **STOP and WAIT** for user confirmation before continuing
   
   e) After confirmation, repeat loop for next TODO item

3. When all TODOs are `[x]`, suggest switching to `#complete` mode

## WORKING WITH TASK FILE

- The task file IS your source of truth
- Read it at the start to see all TODO items
- Pick the FIRST uncompleted `[ ]` item only
- After completing it, mark as `[x]` and STOP
- On next iteration, read the file again to find the next `[ ]` item
{% endif %}

## PERMITTED

- Edit task file directly (mark complete, add notes)
- Modify the plan (add/remove/edit TODO items) ONLY when user explicitly requests it

## FORBIDDEN

- No new tasks beyond TODO list
- No creative additions

---
**YOU MUST FOLLOW THE WORKFLOW**
