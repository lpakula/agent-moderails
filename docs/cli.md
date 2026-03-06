# CLI Reference

## Project

```bash
# Register the current git repo as a moderails project
moderails register
moderails register --name "My App"

# List all registered projects
moderails project list

# Rename a project
moderails project update --name "New Name"
moderails project update --id <project-id> --name "New Name"

# Unregister a project
moderails project delete
moderails project delete --id <project-id>
```

## Tasks

```bash
# List tasks for the current project
moderails task list

# List tasks across all projects
moderails task list --all

# Show task details and run history
moderails task show --id <task-id>

# Create a task (-d is required — becomes the prompt for the first run)
moderails task create -t "Fix login bug" -d "Safari shows blank page on submit"
moderails task create -t "Add pagination" -d "Add cursor-based pagination to the posts list" --type feature

# Start a run immediately after creating
moderails task create -t "My task" --start --flow default

# Update a task
moderails task update --id <task-id> --title "Better title"
moderails task update --id <task-id> --description "Updated description"

# Delete a task
moderails task delete --id <task-id>
moderails task delete --id <task-id> --yes
```

## Runs

```bash
# List runs for the current project
moderails run list

# List runs for a specific task
moderails run list --task <task-id>

# List runs across all projects
moderails run list --all

# Show run details
moderails run show <run-id>

# Print logs for a run
moderails run logs <run-id>
moderails run logs <run-id> --follow
moderails run logs <run-id> --raw

# Enqueue a new run for a task
moderails task start --id <task-id>
moderails task start --id <task-id> --flow ripper-5
moderails task start --id <task-id> --flow default --prompt "Focus on the mobile layout"

# Chain multiple flows (executed in order)
moderails task start --id <task-id> --flow ripper-5 --flow submit-pr
moderails task start --id <task-id> --flow default --flow submit-pr --prompt "Ship it"
```

## Flows

```bash
# List all flows
moderails flow list

# Show a flow and its steps
moderails flow show <name>

# Create a flow
moderails flow create <name>
moderails flow create <name> --description "What this flow does"
moderails flow create <name> --copy-from default

# Delete a flow
moderails flow delete <name>
moderails flow delete <name> --yes

# Export / import
moderails flow export --output flows.json
moderails flow import flows.json
```

### Steps

```bash
# List steps in a flow
moderails flow step list --flow <name>

# Add a step (from file)
moderails flow step add --flow <name> --name <step-name> --content step.md

# Add a step (from stdin)
cat step.md | moderails flow step add --flow <name> --name <step-name>

# Add a step at a specific position
moderails flow step add --flow <name> --name <step-name> --content step.md --position 2

# Edit a step's content
moderails flow step edit --flow <name> --name <step-name> --content step.md

# Remove a step
moderails flow step remove --flow <name> --name <step-name>
```

## Daemon

```bash
# Start the daemon (background)
moderails daemon start

# Start in foreground (logs to terminal + log file)
moderails daemon start --foreground

# Stop the daemon
moderails daemon stop

# Show daemon status
moderails daemon status
```

## Agent (internal)

These commands are called by the agent inside a worktree — not meant for manual use.

```bash
# Load the next step instructions
moderails mode next

# Re-read the current step (after crash or restart)
moderails mode current

# Save run summary (called by the complete step)
moderails run complete --summary "$(cat <<'EOF'
## What was done
...
EOF
)"
```

## UI

```bash
# Start the web UI
moderails ui

# Custom port
moderails ui --port 9000

# Auto-reload on code changes
moderails ui --reload
```

## Database

```bash
# Wipe and recreate the database
moderails db reset
moderails db reset --yes
```
