# Moderails Protocol

Modal control system for AI agents.

## MODES

| Mode | Command | Purpose |
|------|---------|---------|
| START | `moderails start` | Initial mode, show status |
| RESEARCH | `#research` | Gather information, explore scope |
| BRAINSTORM | `#brainstorm` | (Optional) Explore alternatives |
| PLAN | `#plan` | Create TODO list in task file |
| EXECUTE | `#execute` | Implement TODO items one by one |
| COMPLETE | `#complete` | Mark task done, commit |
| CLOSE | `#close` | Abandon task, reset git |

## CRITICAL RULES

- **MUST** start every response with `[MODE: NAME]`
- **MUST** Use task files in `moderails/tasks/`
- **FORBIDDEN**: Switching modes without explicit user command (e.g., `#execute`)
- **FORBIDDEN**: `todo_write` or any other internal TODO tools

## MODE SWITCHING

When user types `#execute`, run:
```sh
moderails mode --name execute
```

## CLI COMMANDS

| Command | Purpose |
|---------|---------|
| `moderails start` | Show status and protocol |
| `moderails start --new --task "task" --epic "epic"` | Create new task |
| `moderails start --task "task"` | Continue existing task |
| `moderails mode --name <mode>` | Get mode rules |
