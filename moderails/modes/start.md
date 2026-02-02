# Moderails Protocol

Modal control system for AI agents.

## AVAILABLE CLI COMMANDS

```
# Task Management
moderails task list [--status <draft|in-progress|completed>]
moderails task create --name "Task Name" [--epic <epic-id>] [--type feature|fix|refactor|chore]
moderails task complete --id <task-id> --commit-message "..."
moderails task update --id <task-id> [--name <name>] [--status <status>] [--type <type>] [--summary <text>]

# Epic Management
moderails epic list
moderails epic create --name "epic-name"
moderails epic update --id <epic-id> --name "new-epic-name"

# Context Management
moderails context list                                # List available memories and files
moderails context load --memory <name>                # Load specific memory

# Session
moderails start
moderails mode --name <mode>
```

## MODES

| Mode | Command | Purpose |
|------|---------|---------|
| START | `moderails start` | Initial mode, show status |
| RESEARCH | `#research` | Gather information, explore scope |
| BRAINSTORM | `#brainstorm` | (Optional) Explore alternatives |
| PLAN | `#plan` | Create TODO list in task file |
| EXECUTE | `#execute` | Implement TODO items one by one |
| COMPLETE | `#complete` | Mark task done, commit |
| FAST | `#fast` | (Optional) Quick iterations without protocol |
| ABORT | `#abort` | Abandon task, reset git |

## MODE SWITCHING

When user types `#<mode> [--flags]`, run:
```sh
moderails mode --name <mode> [--flags]
```

Example: `#execute --no-confirmation` → `moderails mode --name execute --no-confirmation`

## CRITICAL RULES

- **MUST** start every response with `[MODE: NAME]`
- **MUST** Use task files in `_moderails/tasks`
- **FORBIDDEN**: Switching modes without explicit user command (e.g., `#execute`)
- **FORBIDDEN**: `todo_write` or any other internal TODO tools


## WORKFLOW

{% if current_task %}
### Current Task: {{ current_task.name }} (`{{ current_task.id }}`)

- **Status**: in-progress
- **Type**: {{ current_task.type }}
{% if current_task.has_plan_file %}- **Plan**: `{{ current_task.file_path }}`{% endif %}
{% if current_task.epic %}- **Epic**: {{ current_task.epic.name }} (`{{ current_task.epic.id }}`){% endif %}

1. Confirm with user this is the task to work on
{% if current_task.has_plan_file -%}
2. Advise user to type `#execute` to continue implementation
{% else -%}
2. Advise user to type `#research` to begin analysis
{%- endif %}

{% elif draft_tasks %}
### No Active Task

**Draft tasks available:**
{% for t in draft_tasks %}- `{{ t.id }}` - {{ t.name }}{% if t.epic %} ({{ t.epic.name }}){% endif %}
{% endfor %}
1. Ask user which draft to start, or create a new task
2. To start a draft: `moderails task update --id <id> --status in-progress`
3. Advise user to type `#research` to begin analysis

{% else %}
### No Tasks
{% if epics %}
**Existing epics:**
{% for e in epics %}- `{{ e.id }}` - {{ e.name }}
{% endfor %}
{% endif %}
1. Ask user in natural language: "What would you like to build?"
2. Wait for user's description
3. Based on the description, propose:
   - A task name
   - Task type (feature/fix/refactor/chore)
{% if epics -%}
4. Suggest an existing epic if related, or create a new one
{% else -%}
4. Create a new epic: `moderails epic create --name "epic-name"`
{% endif -%}
5. Create task: `moderails task create --name "Task name" [--type feature|fix|refactor|chore] [--epic <epic-id>]`
6. Advise user to type `#research` to begin analysis
{%- endif %}

---
**YOU MUST FOLLOW THE WORKFLOW**
