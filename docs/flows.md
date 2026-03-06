# Flows

A flow is an ordered list of steps the agent works through, one at a time. Steps are markdown prompts. The agent calls `moderails mode next` to load each step, follows the instructions, then calls `moderails mode next` again to advance.

## How steps work

Each step is injected with a standard footer:

```
---
When you have completed this step, run `moderails mode next` to continue.
```

The agent never needs to know the full flow in advance — it receives one step at a time.

## Default flows

These are seeded into the database on `moderails register` / `moderails db reset`:

### default
Simple execution loop: **execute → test → commit**

Use this for most tasks where the scope is already clear.

### submit-pr
Single step that either:
- Creates a PR (if none exists for the current branch)
- Comments on the existing PR with a summary of the latest run

Chain this after any flow to ship automatically.

## Flow library

Additional flows ship in `moderails/flows/` but are **not** seeded automatically. Import them through the UI — import always overrides an existing flow with the same name.

### ripper-5
Full research-driven flow: **init → research → brainstorm → plan → execute → test → commit**

Use this for complex or exploratory tasks.

### react-js
React/JS flow: **execute → test (Playwright screenshots) → commit (PR-ready summary)**

Use this for frontend tasks where visual verification matters.

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
```

Flow import is available through the UI only.

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

## Gates

Gates are optional shell commands attached to a step. When defined, `moderails mode next` **refuses to advance** until every gate command exits 0. The agent sees the failure output and must fix the issue before it can proceed.

### Defining gates

Add a `gates` array to any step in the flow JSON:

```json
{
  "name": "test",
  "position": 1,
  "content": "# TEST\n\n...",
  "gates": [
    {"command": "test -f .moderails/screenshots/homepage.png", "label": "Homepage screenshot exists"},
    {"command": "npm test -- --watchAll=false", "label": "Test suite passes"}
  ]
}
```

Each gate has:
- `command` — a shell command (runs in the worktree root, must exit 0 to pass)
- `label` — human-readable description shown on failure

### How enforcement works

When the agent calls `moderails mode next`:

1. If the current step has gates, each gate command runs
2. If any gate fails, the agent gets an error with the failed labels and stderr
3. The agent must fix the issues and call `moderails mode next` again
4. Only when all gates pass does the flow advance

### Common gate patterns

```bash
# File existence
test -f .moderails/screenshots/homepage.png

# Glob match (at least one file)
ls *.png 2>/dev/null | grep -q .

# Test suite
npm test -- --watchAll=false
pytest -x

# Build succeeds
npm run build
make build

# Git state
git diff --cached --quiet   # nothing unstaged

# Process check
lsof -ti :3000              # dev server is running
```

### Template variables

Gate commands, labels, and step content support `{{variable}}` interpolation. Available variables:

| Variable | Value |
|----------|-------|
| `{{run.id}}` | Current run ID |
| `{{task.id}}` | Current task ID |
| `{{flow.name}}` | Current flow name |

Example — screenshots scoped to the run:

```json
{
  "command": "ls .moderails/screenshots/{{run.id}}/*.png 2>/dev/null | grep -q .",
  "label": "Screenshots exist in {{run.id}}/"
}
```

Variables are resolved at runtime when the agent calls `moderails mode next` or `moderails mode current`.

### Tips

- Gates are optional — steps without gates advance unconditionally (same as before)
- Gate commands have a 60-second timeout
- The agent sees the gate requirements in the step content, so it knows what to do
- Keep gate commands fast and idempotent

## The complete step

Every flow automatically appends a hidden `complete` step after the last user-defined step. This step instructs the agent to write a structured summary and call `moderails run complete --summary "..."`. The daemon marks the run as completed when this happens.
