# Moderails Protocol

Modal control system for AI agents.

## AVAILABLE CLI COMMANDS

```
# Task Management
moderails task list [--status <draft|in-progress|completed>]
moderails task create --name "Task Name" [--epic <epic-id>] [--type feature|fix|refactor|chore]
moderails task load --task <task-id>
moderails task complete --task <task-id> [--summary <text>]
moderails task update --task <task-id> [--name <name>] [--status <status>] [--type <type>] [--summary <text>]

# Epic Management
moderails epic list
moderails epic create --name "epic-name"
moderails epic update --epic <epic-id> --name "new-epic-name"

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

When user types `#execute`, run:
```sh
moderails mode --name execute
```

**With flags** (e.g., `#execute --flag-1`):
```sh
moderails mode --name execute --flag flag-1
```

## CRITICAL RULES

- **MUST** start every response with `[MODE: NAME]`
- **MUST** Use task files in `.moderails/tasks`
- **FORBIDDEN**: Switching modes without explicit user command (e.g., `#execute`)
- **FORBIDDEN**: `todo_write` or any other internal TODO tools


## WORKFLOW

{% if current_task %}
### Current Task: {{ current_task.name }} (`{{ current_task.id }}`)

**Status**: {{ current_task.status }}
**File**: `{{ current_task.file_path }}`
{% if current_task.epic %}
**Epic**: {{ current_task.epic.name }} (`{{ current_task.epic.id }}`)
{% endif %}

1. Confirm with user this is the task to work on
{% if current_task.status == "draft" %}
2. Advise user to type `#research` to begin analysis
{% else %}
2. Advise user to type `#execute` to continue implementation
{% endif %}

{% else %}
### No Active Task

{% if epics %}
**Existing epics:**
{% for e in epics %}- `{{ e.id }}` - {{ e.name }}
{% endfor %}
{% else %}
No epics exist yet.
{% endif %}

1. Ask user in natural language: "What would you like to build?"
2. Wait for user's description
3. Based on the description, propose:
   - A task name
   - Task type (feature/fix/refactor/chore)
{% if epics %}
4. Suggest an existing epic if related, or create a new one if appropriate
{% else %}
4. Suggest creating a new epic: `moderails epic create --name "epic-name"`
{% endif %}
5. Create task: `moderails task create --name "Task name" [--type feature|fix|refactor|chore] [--epic <epic-id>]`
   - Type defaults to "feature" if not specified
6. Advise user to type `#research` to begin initial analysis
{% endif %}

---
**YOU MUST FOLLOW THE WORKFLOW**
