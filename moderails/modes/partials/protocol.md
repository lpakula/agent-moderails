## AVAILABLE CLI COMMANDS

```
# Task Management
moderails task list [--status <draft|in-progress|completed>]
moderails task create --name "Task Name" [--epic <epic-id>] [--type feature|fix|refactor|chore]
moderails task complete --id <task-id> --commit-message "..."
moderails task update --id <task-id> [--name <name>] [--status <status>] [--type <type>] [--summary <text>]

# Epic Management
moderails epic list
moderails epic create --name "epic-name" [--skills <skill1> --skills <skill2>]
moderails epic update --id <epic-id> [--name "new-name"] [--add-skill <skill>] [--remove-skill <skill>]

# Context Management
moderails context list                                # List available memories and files
moderails context load --memory <name>                # Load specific memory

# Session
moderails start [--rerail]                         # --rerail for instant resume
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
