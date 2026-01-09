# CLI Commands

## Initialization

```bash
# Initialize in current directory (creates .moderails/)
moderails init
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
# List tasks
moderails list [--status <status>]
# List epics
moderails epic list
```

## Task Management

```bash
# Create task
moderails task create --name "Task Name" [--type feature|fix|refactor|chore] [--status draft|in-progress] [--epic <epic-id>] [--no-file] [--no-context]

# Update task
moderails task update --task <task-id> [--name <name>] [--status <status>] [--type <type>] [--summary <text>]

# Complete task
moderails task complete --task <task-id> [--summary <text>]
```


## Epic Management

```bash
# Create epic
moderails epic create --name "Epic Name"  
# Update epic
moderails epic update --epic <epic-id> --name "New Epic Name" 
```

## Context Management

```bash
# List available rules and files
moderails context list
# Load context (flags can be combined)
moderails context load --mandatory --memory auth --memory payments --file src/auth.ts
# Load task context
moderails task load --task <task-id>  
```

## History Sync

```bash
# Sync history from file
moderails sync
```
