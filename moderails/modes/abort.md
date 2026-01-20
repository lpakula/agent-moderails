# ABORT MODE

**Active Mode**: ABORT  
**Output Format**: Start with `[MODE: ABORT]`

---

{% if current_task %}
## CURRENT TASK

- **ID**: `{{ current_task.id }}`
- **Name**: {{ current_task.name }}
- **File**: `{{ current_task.file_path }}`
{% endif %}

---

## PURPOSE

Abandon a task and reset all changes.

## WORKFLOW

1. Delete the task:
```bash
moderails task delete --task {{ current_task.id if current_task else '<task-id>' }} --confirm
```

2. Reset git changes:
```bash
git reset --hard HEAD
```

---
**YOU MUST FOLLOW THE WORKFLOW**
