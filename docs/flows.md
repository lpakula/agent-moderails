# Flows

A flow is an ordered list of steps the agent works through, one at a time. Steps are markdown prompts. The agent calls `moderails mode next` to load each step, follows the instructions, then calls `moderails mode next` again to advance.

## How steps work

Each step is injected with a standard footer:

```
---
When you have completed this step, run `moderails mode next` to continue.
```

The agent never needs to know the full flow in advance — it receives one step at a time.

## Built-in flows

### default
Simple execution loop: **execute → test → commit**

Use this for most tasks where the scope is already clear.

### ripper-5
Full research-driven flow: **research → brainstorm → plan → execute → test → commit**

Use this for complex or exploratory tasks.

### submit-pr
Single step that either:
- Creates a PR (if none exists for the current branch)
- Comments on the existing PR with a summary of the latest run

Chain this after `default` or `ripper-5` to ship automatically.

## Flow chaining

When starting a run you can select multiple flows to execute in sequence. For example: `default` then `submit-pr`. The daemon advances through the chain automatically.

## Managing flows

```bash
# List all flows
moderails flow list

# Show a flow's steps
moderails flow show <name>

# Create a new flow
moderails flow create <name>

# Duplicate an existing flow
moderails flow create <name> --copy-from <source>

# Delete a flow
moderails flow delete <name>

# Export all flows to JSON
moderails flow export --output flows.json

# Import flows from JSON
moderails flow import flows.json
```

## Managing steps

```bash
# List steps in a flow
moderails flow step list --flow <name>

# Add a step (from file or stdin)
moderails flow step add --flow <name> --name <step-name> --content path/to/step.md

# Edit a step
moderails flow step edit --flow <name> --name <step-name> --content path/to/step.md

# Remove a step
moderails flow step remove --flow <name> --name <step-name>
```

You can also manage steps from the UI flow editor, including drag-and-drop reordering.

## The complete step

Every flow automatically appends a hidden `complete` step after the last user-defined step. This step instructs the agent to write a structured summary and call `moderails run complete --summary "..."`. The daemon marks the run as completed when this happens.
