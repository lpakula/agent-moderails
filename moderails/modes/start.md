# Moderails Protocol

Modal control system for AI agents.

## AVAILABLE CLI COMMANDS

```
# Task Management
moderails list [--status <draft|in-progress|completed>]
moderails task create --name "Task Name" [--epic <epic-id>] [--type feature|fix|refactor|chore]
moderails task load --task <task-id>
moderails task complete --task <task-id> [--summary <text>]
moderails task update --task <task-id> [--name <name>] [--status <status>] [--type <type>] [--summary <text>]

# Epic Management
moderails epic list
moderails epic create --name "epic-name"
moderails epic update --epic <epic-id> --name "new-epic-name"

# Context Management
moderails context search --query <topic> | --file <path>

Examples:
  moderails context search --query "auth"           # Search by keyword
  moderails context search --query "auth|user"      # OR search (matches "auth" OR "user")
  moderails context search --file "models/user.py"  # Search by file

# Session
moderails start
moderails mode --name <mode>
moderails sync
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

## CRITICAL RULES

- **MUST** start every response with `[MODE: NAME]`
- **MUST** Use task files in `.moderails/tasks`
- **FORBIDDEN**: Switching modes without explicit user command (e.g., `#execute`)
- **FORBIDDEN**: `todo_write` or any other internal TODO tools


## WORKFLOW

### When no task exists:
1. Ask user in natural language: "What would you like to build?"
2. Wait for user's description
3. Based on the description, propose:
   - A task name
   - Task type (feature/fix/refactor/chore)
4. Check existing epics with `moderails epic list` and suggest one if related, or suggest creating a new epic if appropriate
5. Create task: `moderails task create --name "Task name" [--type feature|fix|refactor|chore] [--epic <epic-id>]`
   - If creating new epic: first run `moderails epic create --name "epic-name"` to get epic ID
   - Type defaults to "feature" if not specified
6. Advise user to type `#research` to begin initial analysis

### When task exists:
1. Ask user to confirm which task to work on
2. Load the task context: `moderails task load --task <task-id>`
3. Advise user to type `#research` if task file is empty (template)
4. Advise user to type `#execute` if task file is not empty 

---
**YOU MUST FOLLOW THE WORKFLOW**