# CLI Commands

## Initialization

```bash
# Initialize in current directory (creates _moderails/)
moderails init

# Initialize in private mode (all _moderails files gitignored)
moderails init --private
```

## Session Management

```bash
# Start session
moderails start
# Get mode definition
moderails mode --name <mode>
# Run database migrations
moderails migrate
```

## Listing

```bash
# List tasks (human-friendly)
moderails list [--status draft|in-progress|completed] [--epic-name <name>]

# List tasks (agent-friendly table)
moderails task list [--status draft|in-progress|completed] [--epic-name <name>]

# List epics (agent-friendly table)
moderails epic list
```

## Task Management

```bash
# Create task (defaults to in-progress, plan file created when entering #plan mode)
moderails task create --name "Task Name" [--type feature|fix|refactor|chore] [--status draft|in-progress] [--epic <epic-id>]

# Update task
moderails task update --id <task-id> [--name <name>] [--status <status>] [--type <type>] [--summary <text>]

# Complete task (in git repos: stages history, commits, updates git hash)
moderails task complete --id <task-id> --commit-message "<type>: <description>" [--summary "<text>"]

# Complete task (non-git projects: marks complete and exports to history)
moderails task complete --id <task-id> [--summary "<text>"]

# Delete task
moderails task delete --id <task-id> --confirm
```


## Epic Management

```bash
# Create epic
moderails epic create --name "Epic Name"  
# Update epic
moderails epic update --id <epic-id> --name "New Epic Name" 
```

## Context Management

```bash
# List available skills, memories, and files tree
moderails context list
# Load specific memories (flags can be combined)
moderails context load --memory auth --memory payments
```

> **Note:** Mandatory context, skill names, list of available memories, and files tree are automatically injected when entering `#research` or `#fast` modes. Manual loading is only needed for additional memories.

## History Sync

```bash
# Sync history from file
moderails sync
```
