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
moderails task create --name "Task Name" [--type feature|fix|refactor|chore] [--epic <epic-id>]
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
# Load task context
moderails task load --task <task-id>  
# Search context
moderails context search --query <topic> | --file <path>  
```

## History Sync

```bash
# Sync history from file
moderails sync
```
